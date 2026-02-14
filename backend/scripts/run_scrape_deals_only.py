#!/usr/bin/env python3
"""
Run scraper only (no RAG). Use when running locally to populate Neon.
Avoids sentence_transformers/numpy deps. RAG rebuild can run on backend.
From backend dir: python scripts/run_scrape_deals_only.py
"""
import asyncio
import sys
from pathlib import Path

backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))
sys.path.insert(0, str(backend_root))

import os

os.chdir(backend_root)

from datetime import date

from sqlalchemy import delete

from app.db.init_db import init_db
from app.db.models import Discount
from app.db.session import AsyncSessionLocal
from app.services.scraper import run_full_scrape


async def expire_old(session):
    stmt = delete(Discount).where(
        Discount.valid_to.is_not(None), Discount.valid_to < date.today()
    )
    r = await session.execute(stmt)
    await session.commit()
    return r.rowcount or 0


async def main():
    await init_db()
    async with AsyncSessionLocal() as session:
        inserted = await run_full_scrape(session)
        expired = await expire_old(session)
        print(f"Scrape done: inserted {inserted}, expired {expired}")


if __name__ == "__main__":
    asyncio.run(main())
