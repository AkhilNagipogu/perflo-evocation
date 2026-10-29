"""
Database seed script — initializes administrator account, default root domains, and pricing plans.
Run with: python scripts/seed_data.py
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys

# Ensure backend app is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.core.init_db import init_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seed")


async def main() -> None:
    await init_db()


if __name__ == "__main__":
    asyncio.run(main())
