import asyncio
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.logging import configure_logging
from app.db.init_db import init_db
from app.db.session import get_session
from app.routers import admin, ai, banks, discounts
from app.services.rag import RAGService
from app.services.scraper import run_full_scrape
from app.tasks.scheduler import start_scheduler

configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="Pak Bank Discounts Intelligence API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(discounts.router)
app.include_router(banks.router)
app.include_router(ai.router)
app.include_router(admin.router)


@app.on_event("startup")
async def on_startup():
    await init_db()
    async def bootstrap_data():
        async for session in get_session():
            await run_full_scrape(session)
            await RAGService().rebuild_index(session)

    asyncio.create_task(bootstrap_data())
    start_scheduler(get_session)
    logger.info("Application started")


@app.get("/health")
async def health():
    return {"status": "ok"}
