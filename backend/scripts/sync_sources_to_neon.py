#!/usr/bin/env python3
"""
Copy scrape sources from local DB to Neon, or seed all SOURCES into Neon.

Mode 1 - From local (banks that had deals):
  Finds which banks had deals in local Postgres, looks up their full config from SOURCES,
  and writes to Neon's scrape_sources + banks tables.

Mode 2 - Seed all (when local has no data):
  Writes all SOURCES from scraper.py to Neon's scrape_sources.

Prerequisites:
  - TARGET_DATABASE_URL = Neon
  - For mode 1: SOURCE_DATABASE_URL = local postgres, Docker running

Usage:
  cd backend

  # From local (banks with deals)
  $env:SOURCE_DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/pakbank"
  $env:TARGET_DATABASE_URL="postgresql+asyncpg://neondb_owner:...@ep-xxx.neon.tech/neondb?sslmode=require"
  python scripts/sync_sources_to_neon.py

  # Seed all SOURCES (no local needed)
  python scripts/sync_sources_to_neon.py --seed-all
"""
import asyncio
import os
import sys
from pathlib import Path

backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))
os.chdir(backend_root)


def _fix_url(u: str) -> str:
    if not u:
        return u
    if u.startswith("postgres://"):
        u = "postgresql+asyncpg://" + u[11:]
    elif u.startswith("postgresql://") and "+asyncpg" not in u:
        u = "postgresql+asyncpg://" + u[13:]
    return u.replace("sslmode=require", "ssl=require")


async def main():
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker

    from app.db.models import Base
    from app.services.scraper import SOURCES

    seed_all = "--seed-all" in sys.argv
    source_url = _fix_url(os.environ.get("SOURCE_DATABASE_URL", ""))
    target_url = _fix_url(os.environ.get("TARGET_DATABASE_URL", os.environ.get("DATABASE_URL", "")))

    if not target_url or "neon" not in target_url.lower():
        print("TARGET_DATABASE_URL or DATABASE_URL must point to Neon (Render's DATABASE_URL)")
        sys.exit(1)

    if seed_all:
        source_url = None
    elif not source_url or ("localhost" not in source_url and "127.0.0.1" not in source_url):
        print("SOURCE_DATABASE_URL must point to local postgres, or use --seed-all")
        sys.exit(1)

    sources_by_name = {s.name: s for s in SOURCES}

    tgt_engine = create_async_engine(target_url, echo=False)
    async with tgt_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    if source_url:
        src_engine = create_async_engine(source_url, echo=False)
        async with src_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    TgtSession = sessionmaker(bind=tgt_engine, class_=AsyncSession, expire_on_commit=False)

    if seed_all:
        banks_to_sync = [(s.name, s.website) for s in SOURCES]
        print(f"Seed all: {len(banks_to_sync)} sources from SOURCES")
    else:
        SrcSession = sessionmaker(bind=src_engine, class_=AsyncSession, expire_on_commit=False)
        async with SrcSession() as src:
            r = await src.execute(
                text(
                    "SELECT DISTINCT b.name, b.website FROM banks b "
                    "JOIN cards c ON c.bank_id = b.id "
                    "JOIN discounts d ON d.card_id = c.id"
                )
            )
            banks_to_sync = r.fetchall()
        print(f"Local: {len(banks_to_sync)} banks have deals")

    async with TgtSession() as tgt:
        synced = 0
        skipped = 0
        for bank_name, website in banks_to_sync:
            source = sources_by_name.get(bank_name)
            if not source:
                print(f"  Skip {bank_name}: not in SOURCES")
                skipped += 1
                continue

            # Ensure Bank exists in target
            check = await tgt.execute(
                text("SELECT id FROM banks WHERE name = :n"), {"n": bank_name}
            )
            if not check.fetchone():
                await tgt.execute(
                    text("INSERT INTO banks (name, website) VALUES (:n, :w)"),
                    {"n": bank_name, "w": website or source.website},
                )
                await tgt.flush()

            # Upsert scrape_sources
            await tgt.execute(
                text(
                    """
                    INSERT INTO scrape_sources (bank_name, website, base_url, peekaboo_base, is_active)
                    VALUES (:bn, :w, :bu, :pb, true)
                    ON CONFLICT (bank_name) DO UPDATE SET
                        website = EXCLUDED.website,
                        base_url = EXCLUDED.base_url,
                        peekaboo_base = EXCLUDED.peekaboo_base,
                        is_active = true
                    """
                ),
                {
                    "bn": source.name,
                    "w": source.website,
                    "bu": source.base_url,
                    "pb": source.peekaboo_base,
                },
            )
            print(f"  Synced: {source.name} ({source.base_url})")
            synced += 1

        await tgt.commit()
        print(f"\nDone: {synced} sources saved to Neon, {skipped} skipped")

    if source_url:
        await src_engine.dispose()
    await tgt_engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
