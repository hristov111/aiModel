#!/usr/bin/env python3
"""Run one memory consolidation pass (dedup / cleanup).

Usage:
  python run_memory_consolidation.py

This runs a single pass using the same logic as the periodic job and prints a
small summary.
"""

import asyncio

from app.services.memory_consolidation_job import run_memory_consolidation_once


async def main() -> None:
    stats = await run_memory_consolidation_once()
    print("Memory consolidation complete:")
    print(f"  users_processed: {stats['users_processed']}")
    print(f"  exact_inactivated: {stats['exact_inactivated']}")
    print(f"  semantic_inactivated: {stats['semantic_inactivated']}")


if __name__ == "__main__":
    asyncio.run(main())


