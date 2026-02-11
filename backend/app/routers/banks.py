from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Bank, Card
from app.db.session import get_session

router = APIRouter(prefix="/banks", tags=["banks"])


@router.get("")
async def list_banks(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Bank))
    banks = [
        {"id": bank.id, "name": bank.name, "website": bank.website}
        for bank in result.scalars().all()
    ]
    return {"count": len(banks), "results": banks}


@router.get("/{bank_id}")
async def get_bank(bank_id: int, session: AsyncSession = Depends(get_session)):
    bank = (await session.execute(select(Bank).where(Bank.id == bank_id))).scalar_one()
    cards = (
        await session.execute(select(Card).where(Card.bank_id == bank_id))
    ).scalars()
    return {
        "id": bank.id,
        "name": bank.name,
        "website": bank.website,
        "cards": [
            {
                "id": card.id,
                "name": card.name,
                "tier": card.tier,
                "type": card.type,
            }
            for card in cards
        ],
    }
