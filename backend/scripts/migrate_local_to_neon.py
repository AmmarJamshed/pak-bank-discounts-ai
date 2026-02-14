#!/usr/bin/env python3
"""
Migrate deals from local Postgres (Docker) to Neon (production).

Prerequisites:
  1. Docker running with postgres (docker compose up -d postgres)
  2. SOURCE_DATABASE_URL = local postgres (localhost:5432)
  3. TARGET_DATABASE_URL = Neon URL (same as Render's DATABASE_URL)

Usage:
  cd backend
  $env:SOURCE_DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/pakbank"
  $env:TARGET_DATABASE_URL="postgresql+asyncpg://neondb_owner:...@ep-xxx.neon.tech/neondb?sslmode=require"
  python scripts/migrate_local_to_neon.py
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


async def migrate():
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker

    source_url = _fix_url(os.environ.get("SOURCE_DATABASE_URL", ""))
    target_url = _fix_url(os.environ.get("TARGET_DATABASE_URL", os.environ.get("DATABASE_URL", "")))

    if not source_url or "localhost" not in source_url and "127.0.0.1" not in source_url:
        print("SOURCE_DATABASE_URL must point to local postgres (localhost:5432)")
        sys.exit(1)
    if not target_url or "neon" not in target_url.lower():
        print("TARGET_DATABASE_URL must point to Neon (Render's DATABASE_URL)")
        sys.exit(1)

    src_engine = create_async_engine(source_url, echo=False)
    tgt_engine = create_async_engine(target_url, echo=False)
    SrcSession = sessionmaker(bind=src_engine, class_=AsyncSession, expire_on_commit=False)
    TgtSession = sessionmaker(bind=tgt_engine, class_=AsyncSession, expire_on_commit=False)

    async with SrcSession() as src, TgtSession() as tgt:
        # 1. Banks: name -> target id
        r = await src.execute(text("SELECT id, name, website FROM banks"))
        banks = r.fetchall()
        bank_map = {}  # old_id -> new_id
        for old_id, name, website in banks:
            existing = await tgt.execute(
                text("SELECT id FROM banks WHERE name = :n"), {"n": name}
            )
            row = existing.fetchone()
            if row:
                bank_map[old_id] = row[0]
            else:
                ins = await tgt.execute(
                    text("INSERT INTO banks (name, website) VALUES (:n, :w) RETURNING id"),
                    {"n": name, "w": website or ""},
                )
                bank_map[old_id] = ins.scalar()
        await tgt.commit()
        print(f"Banks: {len(bank_map)} synced")

        # 2. Cards: (bank_id, name, type, tier) -> target id
        r = await src.execute(
            text("SELECT id, bank_id, name, type, tier FROM cards")
        )
        cards = r.fetchall()
        card_map = {}  # old_id -> new_id
        for old_id, bank_id, name, card_type, tier in cards:
            new_bank_id = bank_map.get(bank_id)
            if not new_bank_id:
                continue
            existing = await tgt.execute(
                text("SELECT id FROM cards WHERE bank_id = :bid AND name = :n"),
                {"bid": new_bank_id, "n": name},
            )
            row = existing.fetchone()
            if row:
                card_map[old_id] = row[0]
            else:
                ins = await tgt.execute(
                    text(
                        "INSERT INTO cards (bank_id, name, type, tier) "
                        "VALUES (:bid, :n, :t, :tier) RETURNING id"
                    ),
                    {"bid": new_bank_id, "n": name, "t": card_type or "Card", "tier": tier or "Basic"},
                )
                card_map[old_id] = ins.scalar()
        await tgt.commit()
        print(f"Cards: {len(card_map)} synced")

        # 3. Merchants: name -> target id
        r = await src.execute(text("SELECT id, name, category, city, image_url FROM merchants"))
        merchants = r.fetchall()
        merchant_map = {}  # old_id -> new_id
        for old_id, name, category, city, image_url in merchants:
            existing = await tgt.execute(
                text("SELECT id FROM merchants WHERE name = :n"), {"n": name}
            )
            row = existing.fetchone()
            if row:
                merchant_map[old_id] = row[0]
            else:
                ins = await tgt.execute(
                    text(
                        "INSERT INTO merchants (name, category, city, image_url) "
                        "VALUES (:n, :cat, :city, :img) RETURNING id"
                    ),
                    {"n": name, "cat": category or "Retail", "city": city or "Karachi", "img": image_url},
                )
                merchant_map[old_id] = ins.scalar()
        await tgt.commit()
        print(f"Merchants: {len(merchant_map)} synced")

        # 4. Discounts: insert with ON CONFLICT DO NOTHING
        r = await src.execute(
            text(
                "SELECT merchant_id, card_id, discount_percent, conditions, valid_from, valid_to "
                "FROM discounts"
            )
        )
        discounts = r.fetchall()
        inserted = 0
        skipped_fk = 0
        processed = 0
        for mid, cid, pct, cond, vf, vt in discounts:
            new_mid = merchant_map.get(mid)
            new_cid = card_map.get(cid)
            if not new_mid or not new_cid:
                skipped_fk += 1
                processed += 1
                continue
            res = await tgt.execute(
                text(
                    "INSERT INTO discounts (merchant_id, card_id, discount_percent, conditions, valid_from, valid_to) "
                    "VALUES (:mid, :cid, :pct, :cond, :vf, :vt) "
                    "ON CONFLICT ON CONSTRAINT uq_discount_unique DO NOTHING"
                ),
                {
                    "mid": new_mid,
                    "cid": new_cid,
                    "pct": pct,
                    "cond": cond or "",
                    "vf": vf,
                    "vt": vt,
                },
            )
            if res.rowcount and res.rowcount > 0:
                inserted += 1
            processed += 1
            if processed % 500 == 0:
                await tgt.commit()
                print(f"  ... {processed} processed, {inserted} inserted")
        await tgt.commit()
        print(f"Discounts: {inserted} inserted, {skipped_fk} skipped (missing merchant/card in target)")

    await src_engine.dispose()
    await tgt_engine.dispose()
    print("\nMigration complete.")


if __name__ == "__main__":
    asyncio.run(migrate())
