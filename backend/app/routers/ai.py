import asyncio
import logging

from fastapi import APIRouter, Body, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.services.ai_assistant import run_assistant

router = APIRouter(prefix="/ai", tags=["ai"])


class ChatRequest(BaseModel):
    query: str


@router.post("/chat")
async def chat(
    query: str | None = None,
    payload: ChatRequest | None = Body(default=None),
    session: AsyncSession = Depends(get_session),
):
    final_query = query or (payload.query if payload else None)
    if not final_query:
        return {"response": "Missing query."}
    try:
        return await run_assistant(session, final_query)
    except Exception as exc:
        logging.getLogger(__name__).exception("AI assistant error: %s", exc)
        return {
            "intent": {},
            "recommendations": [],
            "card_suggestions": [],
            "serp_fallback": [],
            "response": "The AI assistant is temporarily unavailable. Please try again in a moment.",
        }


@router.get("/stream")
async def stream(
    query: str = Query(..., min_length=3),
    session: AsyncSession = Depends(get_session),
):
    async def event_generator():
        response = await run_assistant(session, query)
        text = response.get("response", "")
        text = text.replace("\n", "\\n")
        for i in range(0, len(text), 40):
            chunk = text[i : i + 40]
            yield f"data: {chunk}\n\n"
            await asyncio.sleep(0.03)
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
