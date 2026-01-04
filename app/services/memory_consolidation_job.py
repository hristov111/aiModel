"""Periodic memory consolidation job (dedup / cleanup).

This job is designed to run inside the API process (dev/small deployments) or be
reused by a dedicated worker/cron in production.

Strategy (safe defaults):
- Exact duplicates: mark older duplicates inactive and point `superseded_by` to the kept record.
- Semantic near-duplicates: for each memory, find highly similar memories in the same user + type and inactivate the duplicates.

We avoid destructive deletes by default; we only mark rows inactive.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, desc, and_, func
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.database import UserModel, MemoryModel

logger = logging.getLogger(__name__)


def _normalize_content(content: str) -> str:
    return " ".join((content or "").strip().lower().split())


def _pick_keeper(a: MemoryModel, b: MemoryModel) -> Tuple[MemoryModel, MemoryModel]:
    """Return (keeper, duplicate). Prefer higher importance, then newer."""
    if (a.importance or 0) > (b.importance or 0):
        return a, b
    if (b.importance or 0) > (a.importance or 0):
        return b, a
    # tie-breaker: keep newest
    if (a.created_at or datetime.min) >= (b.created_at or datetime.min):
        return a, b
    return b, a


async def _mark_superseded(db: AsyncSession, duplicate: MemoryModel, keeper: MemoryModel) -> None:
    duplicate.is_active = False
    duplicate.superseded_by = keeper.id
    duplicate.updated_at = datetime.utcnow()
    db.add(duplicate)


async def _consolidate_user_exact_duplicates(
    db: AsyncSession,
    user_db_id: UUID,
    max_memories: int,
) -> int:
    """Mark exact duplicates inactive. Returns number of inactivated rows."""
    stmt = (
        select(MemoryModel)
        .where(
            and_(
                MemoryModel.user_id == user_db_id,
                MemoryModel.is_active == True,
            )
        )
        .order_by(desc(MemoryModel.created_at))
        .limit(max_memories)
    )
    result = await db.execute(stmt)
    memories = list(result.scalars())

    kept_by_key: Dict[str, MemoryModel] = {}
    inactivated = 0

    for mem in memories:
        key = _normalize_content(mem.content)
        if not key:
            continue
        keeper = kept_by_key.get(key)
        if keeper is None:
            kept_by_key[key] = mem
            continue

        # We already kept a more recent item due to sort order; keep it as canonical.
        await _mark_superseded(db, duplicate=mem, keeper=keeper)
        inactivated += 1

    return inactivated


async def _consolidate_user_semantic_duplicates(
    db: AsyncSession,
    user_db_id: UUID,
    max_memories: int,
    similarity_threshold: float,
) -> int:
    """Mark semantic near-duplicates inactive. Returns number of inactivated rows."""
    # Work on a bounded set for safety
    base_stmt = (
        select(MemoryModel)
        .where(
            and_(
                MemoryModel.user_id == user_db_id,
                MemoryModel.is_active == True,
                MemoryModel.embedding.is_not(None),
            )
        )
        .order_by(desc(MemoryModel.importance), desc(MemoryModel.created_at))
        .limit(max_memories)
    )
    result = await db.execute(base_stmt)
    base_memories = list(result.scalars())

    inactivated = 0
    seen_inactive_ids = set()

    for mem in base_memories:
        if not mem.is_active or mem.id in seen_inactive_ids or mem.embedding is None:
            continue

        # Find the most similar memory of the same type for this user (excluding self).
        # Similarity = 1 - cosine_distance
        sim_expr = (1 - MemoryModel.embedding.cosine_distance(mem.embedding))
        stmt = (
            select(MemoryModel, sim_expr.label("similarity"))
            .where(
                and_(
                    MemoryModel.user_id == user_db_id,
                    MemoryModel.is_active == True,
                    MemoryModel.id != mem.id,
                    MemoryModel.embedding.is_not(None),
                    MemoryModel.memory_type == mem.memory_type,
                    sim_expr >= similarity_threshold,
                )
            )
            .order_by(sim_expr.desc())
            .limit(3)
        )
        rows = (await db.execute(stmt)).all()
        if not rows:
            continue

        for other, similarity in rows:
            if not other.is_active or other.id in seen_inactive_ids:
                continue
            keeper, duplicate = _pick_keeper(mem, other)
            if duplicate.id == keeper.id:
                continue
            await _mark_superseded(db, duplicate=duplicate, keeper=keeper)
            seen_inactive_ids.add(duplicate.id)
            inactivated += 1

    return inactivated


async def run_memory_consolidation_once() -> Dict[str, int]:
    """Run one consolidation pass across users with safety limits."""
    import os

    # Allow explicit override for this job (useful for running from host machine)
    postgres_url = os.getenv("MEMORY_CONSOLIDATION_POSTGRES_URL") or os.getenv("POSTGRES_URL") or settings.postgres_url

    # If running on host machine, map docker hostname/port to local exposed port.
    if not os.path.exists("/.dockerenv"):
        postgres_url = postgres_url.replace("@postgres:5432/", "@localhost:5433/")

        # If this repo's dev docker-compose is present, prefer the dev DB defaults.
        # This avoids accidental use of a production-like .env when running locally.
        dev_compose_path = os.path.join(os.path.dirname(__file__), "..", "..", "docker-compose.dev.yml")
        if os.path.exists(os.path.abspath(dev_compose_path)):
            dev_default = "postgresql+asyncpg://postgres:postgres@localhost:5433/ai_companion_dev"
            if "ai_companion_dev" not in postgres_url or "localhost:5433" not in postgres_url:
                postgres_url = dev_default

    engine = create_async_engine(postgres_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    stats = {"users_processed": 0, "exact_inactivated": 0, "semantic_inactivated": 0}

    async with async_session() as db:
        # Pick a bounded set of users to avoid long pauses.
        user_stmt = (
            select(UserModel)
            .order_by(desc(UserModel.last_active), desc(UserModel.created_at))
            .limit(settings.memory_consolidation_job_max_users_per_run)
        )
        users = list((await db.execute(user_stmt)).scalars())

        for user in users:
            try:
                exact = await _consolidate_user_exact_duplicates(
                    db=db,
                    user_db_id=user.id,
                    max_memories=settings.memory_consolidation_job_max_memories_per_user,
                )
                semantic = await _consolidate_user_semantic_duplicates(
                    db=db,
                    user_db_id=user.id,
                    max_memories=min(200, settings.memory_consolidation_job_max_memories_per_user),
                    similarity_threshold=settings.memory_consolidation_job_semantic_threshold,
                )
                if exact or semantic:
                    await db.commit()
                stats["users_processed"] += 1
                stats["exact_inactivated"] += exact
                stats["semantic_inactivated"] += semantic
            except Exception as e:
                await db.rollback()
                logger.warning(f"Consolidation failed for user {user.external_user_id}: {e}")

    await engine.dispose()
    return stats


async def memory_consolidation_loop(stop_event: asyncio.Event) -> None:
    """Run consolidation periodically until stop_event is set."""
    interval = max(1, int(settings.memory_consolidation_job_interval_minutes)) * 60
    logger.info(
        "Memory consolidation job enabled: interval=%ss, max_users=%s, max_memories_per_user=%s, semantic_threshold=%.2f",
        interval,
        settings.memory_consolidation_job_max_users_per_run,
        settings.memory_consolidation_job_max_memories_per_user,
        settings.memory_consolidation_job_semantic_threshold,
    )

    # small startup delay so the service can come up cleanly
    await asyncio.sleep(5)

    while not stop_event.is_set():
        try:
            stats = await run_memory_consolidation_once()
            logger.info(
                "Memory consolidation run complete: users=%s exact_inactivated=%s semantic_inactivated=%s",
                stats["users_processed"],
                stats["exact_inactivated"],
                stats["semantic_inactivated"],
            )
        except Exception as e:
            logger.error(f"Memory consolidation run failed: {e}", exc_info=True)

        try:
            await asyncio.wait_for(stop_event.wait(), timeout=interval)
        except asyncio.TimeoutError:
            # expected - loop again
            continue


