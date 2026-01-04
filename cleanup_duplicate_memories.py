#!/usr/bin/env python3
"""
Clean up duplicate memories from the database.

This script finds and removes duplicate or very similar memories,
keeping only the most recent or most important version.
"""

import asyncio
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.models.database import MemoryModel, UserModel
from app.utils.embeddings import get_embedding_generator
import numpy as np
from collections import defaultdict
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Database connection
POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_companion")
engine = create_async_engine(POSTGRES_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def cosine_similarity(a, b):
    """Calculate cosine similarity between two vectors."""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


async def cleanup_duplicates(user_external_id: str, similarity_threshold: float = 0.95, dry_run: bool = True):
    """
    Find and remove duplicate memories for a user.
    
    Args:
        user_external_id: External user ID
        similarity_threshold: Similarity threshold for duplicates (0.95 = 95% similar)
        dry_run: If True, only show what would be deleted without actually deleting
    """
    async with AsyncSessionLocal() as session:
        # Get user
        result = await session.execute(
            select(UserModel).where(UserModel.external_user_id == user_external_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"❌ User '{user_external_id}' not found")
            return
        
        print(f"🔍 Analyzing memories for user: {user_external_id}")
        print(f"   Similarity threshold: {similarity_threshold} ({int(similarity_threshold * 100)}%)")
        print(f"   Mode: {'DRY RUN (no changes)' if dry_run else 'LIVE (will delete)'}")
        print()
        
        # Get all memories for user
        result = await session.execute(
            select(MemoryModel)
            .where(MemoryModel.conversation_id.in_(
                select(MemoryModel.conversation_id).where(
                    MemoryModel.conversation_id.in_(
                        select(UserModel.id).where(UserModel.id == user.id)
                    )
                )
            ))
            .order_by(MemoryModel.created_at.desc())
        )
        memories = result.scalars().all()
        
        if not memories:
            print("ℹ️  No memories found")
            return
        
        print(f"📊 Total memories: {len(memories)}")
        print()
        
        # Group by content (exact duplicates)
        content_groups = defaultdict(list)
        for memory in memories:
            content_groups[memory.content.strip().lower()].append(memory)
        
        # Find exact duplicates
        exact_duplicates = []
        for content, group in content_groups.items():
            if len(group) > 1:
                # Keep the most recent one, mark others for deletion
                group.sort(key=lambda m: m.created_at, reverse=True)
                exact_duplicates.extend(group[1:])  # Skip first (most recent)
        
        if exact_duplicates:
            print(f"🔴 Found {len(exact_duplicates)} EXACT duplicates:")
            for memory in exact_duplicates[:10]:  # Show first 10
                print(f"   • \"{memory.content[:60]}...\" (created {memory.created_at})")
            if len(exact_duplicates) > 10:
                print(f"   ... and {len(exact_duplicates) - 10} more")
            print()
        
        # Find semantic duplicates (very similar but not exact)
        embedding_gen = get_embedding_generator()
        
        # Get embeddings for all unique contents
        unique_memories = []
        seen_contents = set()
        for memory in memories:
            if memory.content.strip().lower() not in seen_contents:
                unique_memories.append(memory)
                seen_contents.add(memory.content.strip().lower())
        
        print(f"🔍 Checking {len(unique_memories)} unique memories for semantic duplicates...")
        
        semantic_duplicates = []
        checked = set()
        
        for i, memory1 in enumerate(unique_memories):
            if memory1.id in [m.id for m in exact_duplicates]:
                continue  # Skip if already marked as exact duplicate
            
            for memory2 in unique_memories[i+1:]:
                if memory2.id in [m.id for m in exact_duplicates]:
                    continue
                
                pair_key = tuple(sorted([memory1.id, memory2.id]))
                if pair_key in checked:
                    continue
                checked.add(pair_key)
                
                # Calculate similarity
                if memory1.embedding and memory2.embedding:
                    emb1 = np.array(memory1.embedding)
                    emb2 = np.array(memory2.embedding)
                    similarity = cosine_similarity(emb1, emb2)
                    
                    if similarity >= similarity_threshold:
                        # Keep the one with higher importance, or more recent if same
                        if memory1.importance > memory2.importance:
                            duplicate = memory2
                        elif memory2.importance > memory1.importance:
                            duplicate = memory1
                        elif memory1.created_at > memory2.created_at:
                            duplicate = memory2
                        else:
                            duplicate = memory1
                        
                        if duplicate not in semantic_duplicates:
                            semantic_duplicates.append(duplicate)
                            print(f"   • Similar ({similarity:.2%}): \"{memory1.content[:40]}\" ≈ \"{memory2.content[:40]}\"")
        
        print()
        if semantic_duplicates:
            print(f"🟡 Found {len(semantic_duplicates)} SEMANTIC duplicates (very similar)")
        else:
            print(f"✅ No semantic duplicates found")
        print()
        
        # Summary
        total_to_delete = len(exact_duplicates) + len(semantic_duplicates)
        
        print("=" * 70)
        print(f"📊 SUMMARY:")
        print(f"   Total memories: {len(memories)}")
        print(f"   Exact duplicates: {len(exact_duplicates)}")
        print(f"   Semantic duplicates: {len(semantic_duplicates)}")
        print(f"   Total to remove: {total_to_delete}")
        print(f"   After cleanup: {len(memories) - total_to_delete}")
        print("=" * 70)
        print()
        
        if total_to_delete == 0:
            print("✨ No duplicates to remove! Your memories are clean.")
            return
        
        # Delete if not dry run
        if not dry_run:
            print("🗑️  Deleting duplicates...")
            
            ids_to_delete = [m.id for m in exact_duplicates + semantic_duplicates]
            
            await session.execute(
                delete(MemoryModel).where(MemoryModel.id.in_(ids_to_delete))
            )
            await session.commit()
            
            print(f"✅ Deleted {total_to_delete} duplicate memories")
        else:
            print("ℹ️  DRY RUN: No changes made.")
            print("   To actually delete duplicates, run:")
            print(f"   python cleanup_duplicate_memories.py --execute")


async def main():
    import sys
    
    # Check if --execute flag is provided
    dry_run = "--execute" not in sys.argv
    
    # Default user (change this or pass as argument)
    user_id = "myuser123"
    
    if len(sys.argv) > 1 and not sys.argv[1].startswith("--"):
        user_id = sys.argv[1]
    
    await cleanup_duplicates(user_id, similarity_threshold=0.95, dry_run=dry_run)


if __name__ == "__main__":
    asyncio.run(main())







