#!/usr/bin/env python3
"""
Run scraper + RAG rebuild. Use from PythonAnywhere cron or manually.
From backend dir: python scripts/run_scrape.py  or  python -m scripts.run_scrape
"""
import asyncio
import os
import sys
from pathlib import Path

# Ensure backend root is on path and cwd (for .env loading)
backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))
os.chdir(backend_root)

from app.db.session import AsyncSessionLocal
from app.services.rag import RAGService
from app.services.scraper import run_full_scrape
from app.tasks.scheduler import expire_old_discounts


async def main():
    async with AsyncSessionLocal() as session:
        inserted = await run_full_scrape(session)
        expired = await expire_old_discounts(session)
        try:
            await RAGService().rebuild_index(session)
        except Exception as e:
            print(f"RAG rebuild skipped: {e}")
        print(f"Scrape done: inserted {inserted}, expired {expired}")


if __name__ == "__main__":
    asyncio.run(main())
