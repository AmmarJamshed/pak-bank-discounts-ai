import re

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Bank, Card, Discount, Merchant
from app.db.session import get_session
from app.services.recommender import rank_discounts

router = APIRouter(prefix="/discounts", tags=["discounts"])


def _is_readable(text: str) -> bool:
    """Filter only empty/null. Show all deals to reach 4000+ target."""
    cleaned = re.sub(r"\s+", " ", (text or "").strip())
    return bool(cleaned)


@router.get("")
async def list_discounts(
    city: str | None = None,
    category: str | None = None,
    bank: str | None = None,
    card_type: str | None = None,
    card_tier: str | None = None,
    intent: str | None = None,
    limit: int = Query(5000, ge=1, le=5000),
    session: AsyncSession = Depends(get_session),
):
    query = (
        select(
            Discount.id,
            Discount.discount_percent,
            Discount.conditions,
            Discount.valid_from,
            Discount.valid_to,
            Merchant.name.label("merchant"),
            Merchant.city,
            Merchant.category,
            Merchant.image_url.label("merchant_image_url"),
            Card.name.label("card_name"),
            Card.type.label("card_type"),
            Card.tier.label("card_tier"),
            Bank.name.label("bank"),
        )
        .join(Merchant, Discount.merchant_id == Merchant.id)
        .join(Card, Discount.card_id == Card.id)
        .join(Bank, Card.bank_id == Bank.id)
    )

    if city:
        query = query.where(func.lower(Merchant.city) == city.lower())
    if category:
        query = query.where(func.lower(Merchant.category) == category.lower())
    if bank:
        query = query.where(func.lower(Bank.name) == bank.lower())
    if card_type:
        query = query.where(func.lower(Card.type) == card_type.lower())
    if card_tier:
        query = query.where(func.lower(Card.tier) == card_tier.lower())

    result = await session.execute(query.limit(limit))
    discounts = [
        {
            "discount_id": row.id,
            "discount_percent": row.discount_percent,
            "conditions": row.conditions,
            "valid_from": row.valid_from.isoformat() if row.valid_from else None,
            "valid_to": row.valid_to.isoformat() if row.valid_to else None,
            "merchant": row.merchant,
            "city": row.city,
            "category": row.category,
            "merchant_image_url": row.merchant_image_url,
            "card_name": row.card_name,
            "card_type": row.card_type,
            "card_tier": row.card_tier,
            "bank": row.bank,
        }
        for row in result.all()
    ]

    # No filter - show all deals from DB
    if intent:
        discounts = rank_discounts(discounts, city or "", intent)
    return {"count": len(discounts), "results": discounts}
