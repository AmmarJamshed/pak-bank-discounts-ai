import logging
from datetime import date

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import Discount
from app.services.rag import RAGService
from app.services.scraper import run_full_scrape

logger = logging.getLogger(__name__)


async def expire_old_discounts(session: AsyncSession) -> int:
    stmt = delete(Discount).where(Discount.valid_to.is_not(None), Discount.valid_to < date.today())
    result = await session.execute(stmt)
    await session.commit()
    return result.rowcount or 0


def start_scheduler(get_session):
    scheduler = AsyncIOScheduler()

    async def scheduled_job():
        async for session in get_session():
            inserted = await run_full_scrape(session)
            expired = await expire_old_discounts(session)
            await RAGService().rebuild_index(session)
            logger.info(
                "Scheduler: inserted %s, expired %s discounts", inserted, expired
            )

    scheduler.add_job(
        scheduled_job, "interval", hours=settings.scrape_interval_hours, next_run_time=None
    )
    scheduler.start()
    return scheduler
