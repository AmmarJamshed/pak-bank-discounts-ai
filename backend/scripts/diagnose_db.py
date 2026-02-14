#!/usr/bin/env python3
"""
Diagnose deal counts in local vs Neon databases.
Run with SOURCE_DATABASE_URL (local) and/or TARGET_DATABASE_URL (Neon).

Examples:
  # Count in local Postgres (Docker must be running)
  $env:SOURCE_DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/pakbank"
  python scripts/diagnose_db.py

  # Count in Neon (production)
  $env:TARGET_DATABASE_URL="postgresql+asyncpg://neondb_owner:...@ep-xxx.neon.tech/neondb?sslmode=require"
  python scripts/diagnose_db.py --target

  # Compare both
  $env:SOURCE_DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/pakbank"
  $env:TARGET_DATABASE_URL="postgresql+asyncpg://neondb_owner:...@ep-xxx.neon.tech/neondb?sslmode=require"
  python scripts/diagnose_db.py
"""
import asyncio
import os
import sys
from pathlib import Path

backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))
os.chdir(backend_root)

# Patch config before importing app modules
_source = os.environ.get("SOURCE_DATABASE_URL", "").strip()
_target = os.environ.get("TARGET_DATABASE_URL", os.environ.get("DATABASE_URL", "")).strip()

# Apply asyncpg fix to URLs
def _fix_url(u: str) -> str:
    if not u:
        return u
    if u.startswith("postgres://"):
        u = "postgresql+asyncpg://" + u[11:]
    elif u.startswith("postgresql://") and "+asyncpg" not in u:
        u = "postgresql+asyncpg://" + u[13:]
    return u.replace("sslmode=require", "ssl=require")


async def count_in_db(url: str, label: str) -> dict:
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker

    url = _fix_url(url)
    engine = create_async_engine(url, echo=False)
    async_session = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    counts = {}
    async with async_session() as session:
        for table in ["banks", "cards", "merchants", "discounts"]:
            r = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
            counts[table] = r.scalar() or 0
    await engine.dispose()
    return counts


async def main():
    only_target = "--target" in sys.argv
    if only_target:
        if not _target:
            print("TARGET_DATABASE_URL or DATABASE_URL required for --target")
            sys.exit(1)
        counts = await count_in_db(_target, "Target (Neon)")
        print("=== Target (Neon / Production) ===")
        for t, c in counts.items():
            print(f"  {t}: {c}")
        print(f"\n  Total deals: {counts.get('discounts', 0)}")
        return

    if _source and _target:
        print("=== Source (Local Postgres) ===\n")
        src = await count_in_db(_source, "Source")
        for t, c in src.items():
            print(f"  {t}: {c}")
        print(f"\n  Total deals: {src.get('discounts', 0)}\n")

        print("=== Target (Neon / Production) ===\n")
        tgt = await count_in_db(_target, "Target")
        for t, c in tgt.items():
            print(f"  {t}: {c}")
        print(f"\n  Total deals: {tgt.get('discounts', 0)}\n")

        diff = src.get("discounts", 0) - tgt.get("discounts", 0)
        print(f"=== Summary ===")
        print(f"  Deals in local: {src.get('discounts', 0)}")
        print(f"  Deals in Neon:  {tgt.get('discounts', 0)}")
        print(f"  Missing in Neon: {diff}")
    elif _source:
        counts = await count_in_db(_source, "Source")
        print("=== Source (Local Postgres) ===")
        for t, c in counts.items():
            print(f"  {t}: {c}")
        print(f"\n  Total deals: {counts.get('discounts', 0)}")
    elif _target:
        counts = await count_in_db(_target, "Target")
        print("=== Target (Neon) ===")
        for t, c in counts.items():
            print(f"  {t}: {c}")
        print(f"\n  Total deals: {counts.get('discounts', 0)}")
    else:
        print("Set SOURCE_DATABASE_URL (local) and/or TARGET_DATABASE_URL (Neon)")
        print("\nLocal: postgresql+asyncpg://postgres:postgres@localhost:5432/pakbank")
        print("Neon:  from Render Dashboard -> pak-bank-backend -> Environment -> DATABASE_URL")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
