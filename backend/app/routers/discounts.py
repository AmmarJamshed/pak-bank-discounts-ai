import re

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Bank, Card, Discount, Merchant
from app.db.session import get_session
from app.services.recommender import rank_discounts

router = APIRouter(prefix="/discounts", tags=["discounts"])


def _is_readable(text: str) -> bool:
    """Filter only empty/null. Show all deals to reach 4000+ target."""
    cleaned = re.sub(r"\s+", " ", (text or "").strip())
    return bool(cleaned)


def _keyword_filter(term: str):
    """Build OR condition: term matches merchant, category, city, conditions, or card name."""
    pattern = f"%{term}%"
    return or_(
        Merchant.name.ilike(pattern),
        Merchant.category.ilike(pattern),
        Merchant.city.ilike(pattern),
        Card.name.ilike(pattern),
        func.coalesce(Discount.conditions, "").ilike(pattern),
    )


@router.get("")
async def list_discounts(
    city: str | None = None,
    category: str | None = None,
    bank: str | None = None,
    card_type: str | None = None,
    card_tier: str | None = None,
    intent: str | None = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    base = (
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
        base = base.where(func.lower(Merchant.city) == city.lower())
    if category:
        base = base.where(func.lower(Merchant.category) == category.lower())
    if bank:
        base = base.where(func.lower(Bank.name) == bank.lower())
    if card_type:
        base = base.where(func.lower(Card.type) == card_type.lower())
    if card_tier:
        base = base.where(func.lower(Card.tier) == card_tier.lower())

    if intent and intent.strip():
        words = [w.strip() for w in intent.split() if w.strip()]
        if words:
            for word in words:
                base = base.where(_keyword_filter(word))

    # Total count (before pagination)
    subq = base.subquery()
    count_q = select(func.count()).select_from(subq)
    total_result = await session.execute(count_q)
    total_count = total_result.scalar() or 0

    # Paginated results
    result = await session.execute(base.offset(offset).limit(limit))
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

    if intent:
        discounts = rank_discounts(discounts, city or "", intent)
    return {"count": len(discounts), "total_count": total_count, "results": discounts}
