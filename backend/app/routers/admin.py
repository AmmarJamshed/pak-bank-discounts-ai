from datetime import date, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Bank, Card, Discount, Merchant
from app.db.session import get_session
from app.services.scrape_state import is_maintenance, set_scraping

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/maintenance")
async def maintenance_status():
    """Returns maintenance flag for weekly scrape window (used by frontend banner)."""
    ok, msg = is_maintenance()
    return {"maintenance": ok, "message": msg}


@router.post("/trigger-scrape")
async def trigger_scrape(background_tasks: BackgroundTasks):
    """Trigger scraper in background. Use from cron (GitHub Actions etc) or manually."""

    def _run():
        import asyncio
        from app.db.session import AsyncSessionLocal
        from app.services.rag import RAGService
        from app.services.scraper import run_full_scrape
        from app.tasks.scheduler import expire_old_discounts

        set_scraping(True)
        try:
            async def _scrape():
                async with AsyncSessionLocal() as session:
                    inserted = await run_full_scrape(session)
                    await expire_old_discounts(session)
                    try:
                        await RAGService().rebuild_index(session)
                    except Exception:
                        pass
                    return inserted

            asyncio.run(_scrape())
        finally:
            set_scraping(False)

    background_tasks.add_task(_run)
    return {"status": "started", "message": "Scraper running in background"}


@router.get("/analytics")
async def analytics(session: AsyncSession = Depends(get_session)):
    total_discounts = (
        await session.execute(select(func.count(Discount.id)))
    ).scalar_one()
    avg_discount = (
        await session.execute(select(func.avg(Discount.discount_percent)))
    ).scalar_one()
    top_categories = (
        await session.execute(
            select(Merchant.category, func.count(Discount.id))
            .join(Discount, Discount.merchant_id == Merchant.id)
            .group_by(Merchant.category)
            .order_by(func.count(Discount.id).desc())
            .limit(5)
        )
    ).all()
    top_cities = (
        await session.execute(
            select(Merchant.city, func.count(Discount.id))
            .join(Discount, Discount.merchant_id == Merchant.id)
            .group_by(Merchant.city)
            .order_by(func.count(Discount.id).desc())
            .limit(5)
        )
    ).all()
    top_banks = (
        await session.execute(
            select(Bank.name, func.count(Discount.id))
            .join(Card, Card.bank_id == Bank.id)
            .join(Discount, Discount.card_id == Card.id)
            .group_by(Bank.name)
            .order_by(func.count(Discount.id).desc())
            .limit(5)
        )
    ).all()
    expiring_soon = (
        await session.execute(
            select(func.count(Discount.id)).where(
                Discount.valid_to.is_not(None),
                Discount.valid_to <= date.today() + timedelta(days=7),
            )
        )
    ).scalar_one()

    return {
        "total_discounts": int(total_discounts or 0),
        "average_discount": round(float(avg_discount or 0), 2),
        "top_categories": [
            {"category": row[0], "count": row[1]} for row in top_categories
        ],
        "top_cities": [{"city": row[0], "count": row[1]} for row in top_cities],
        "top_banks": [{"bank": row[0], "count": row[1]} for row in top_banks],
        "expiring_soon": int(expiring_soon or 0),
    }


@router.get("/trends")
async def trends(session: AsyncSession = Depends(get_session)):
    rows = (
        await session.execute(
            select(
                func.date_trunc("week", Discount.valid_from).label("week"),
                func.count(Discount.id),
            )
            .where(Discount.valid_from.is_not(None))
            .group_by(func.date_trunc("week", Discount.valid_from))
            .order_by(func.date_trunc("week", Discount.valid_from))
        )
    ).all()
    series = [{"week": row[0].date().isoformat(), "count": row[1]} for row in rows]
    if len(series) >= 3:
        last_three = [item["count"] for item in series[-3:]]
        forecast = int(sum(last_three) / len(last_three))
    else:
        forecast = int(series[-1]["count"]) if series else 0
    return {"series": series, "forecast_next_week": forecast}


@router.get("/insights")
async def insights(session: AsyncSession = Depends(get_session)):
    rows = (
        await session.execute(
            select(
                Bank.name,
                func.count(Discount.id),
                func.sum(Discount.discount_percent),
                func.count(func.distinct(Merchant.category)),
            )
            .join(Card, Card.bank_id == Bank.id)
            .join(Discount, Discount.card_id == Card.id)
            .join(Merchant, Discount.merchant_id == Merchant.id)
            .group_by(Bank.name)
            .order_by(func.sum(Discount.discount_percent).desc())
        )
    ).all()
    insights = []
    for row in rows:
        affiliate_ready = row[1] >= 20 and row[3] >= 3
        insights.append(
            {
                "bank": row[0],
                "discount_count": int(row[1]),
                "total_discount_value": float(row[2] or 0),
                "category_coverage": int(row[3]),
                "affiliate_ready": affiliate_ready,
            }
        )
    return {"banks": insights}
