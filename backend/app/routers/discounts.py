import re

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Bank, Card, Discount, Merchant
from app.db.session import get_session
from app.services.recommender import rank_discounts

router = APIRouter(prefix="/discounts", tags=["discounts"])

# Cities that appear in data - used to extract city from search intent (e.g. "DHA Karachi" -> Karachi)
KNOWN_CITIES = [
    "Karachi", "Lahore", "Islamabad", "Rawalpindi", "Faisalabad", "Multan",
    "Peshawar", "Quetta", "Hyderabad", "Sialkot", "Gujranwala", "Bahawalpur",
    "Sargodha", "Sukkur", "Larkana", "Mingora", "Muzaffarabad", "Mirpur",
    "Abbottabad", "Dera Ismail Khan",
]


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


def _extract_city_from_intent(intent: str | None) -> tuple[str | None, str]:
    """If intent contains a known city (e.g. 'DHA Karachi'), extract city and remaining keywords."""
    if not intent or not intent.strip():
        return None, ""
    words = [w.strip() for w in intent.split() if w.strip()]
    found_city = None
    remaining = []
    for w in words:
        for c in KNOWN_CITIES:
            if w.lower() == c.lower():
                found_city = c
                break
        else:
            remaining.append(w)
    return found_city, " ".join(remaining).strip()


@router.get("/filter-options")
async def list_filter_options(
    bank: str | None = None,
    card_type: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    """Return available card tiers (and types) for given bank and card type.
    Used to make filter dropdowns intelligent: e.g. HBL Debit has no Platinum."""
    q = (
        select(Card.tier, Card.type)
        .join(Bank, Card.bank_id == Bank.id)
        .join(Discount, Discount.card_id == Card.id)
        .distinct()
    )
    if bank:
        q = q.where(func.lower(Bank.name) == bank.lower())
    if card_type:
        q = q.where(
            or_(
                func.lower(Card.type) == card_type.lower(),
                Card.name.ilike(f"%{card_type}%"),
            )
        )
    result = await session.execute(q)
    tiers = set()
    types_seen = set()
    for row in result.all():
        if row.tier and str(row.tier).strip():
            tiers.add(str(row.tier).strip())
        if row.type and str(row.type).strip():
            t = str(row.type).strip().lower()
            if t in ("credit", "debit"):
                types_seen.add(t.title())
    tier_order = ["Basic", "Classic", "Gold", "Platinum", "Signature", "Infinite"]
    sorted_tiers = [t for t in tier_order if t in tiers] + [t for t in sorted(tiers) if t not in tier_order]
    return {
        "card_tiers": sorted_tiers,
        "card_types": list(types_seen) if types_seen else ["Credit", "Debit"],
    }


@router.get("/cards")
async def list_cards_with_discounts(
    bank: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    """Return distinct card names that have discounts. Optional bank filter."""
    q = (
        select(Card.name, Bank.name.label("bank_name"))
        .join(Bank, Card.bank_id == Bank.id)
        .join(Discount, Discount.card_id == Card.id)
        .distinct()
    )
    if bank:
        q = q.where(func.lower(Bank.name) == bank.lower())
    result = await session.execute(q)
    cards = [{"card_name": row.name, "bank": row.bank_name} for row in result.all()]
    return {"count": len(cards), "results": cards}


@router.get("")
async def list_discounts(
    city: str | None = None,
    category: str | None = None,
    bank: str | None = None,
    card_type: str | None = None,
    card_tier: str | None = None,
    card: str | None = None,
    intent: str | None = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    # When user searches "DHA Karachi" without selecting city, extract city from intent
    effective_city = city
    effective_intent = intent
    if intent and intent.strip() and not city:
        parsed_city, remaining = _extract_city_from_intent(intent)
        if parsed_city:
            effective_city = parsed_city
            effective_intent = remaining if remaining else None

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

    # Use partial match for city so "Karachi" matches "Karachi", "DHA Karachi", etc.
    if effective_city:
        pattern = f"%{effective_city}%"
        base = base.where(Merchant.city.ilike(pattern))
    if category:
        base = base.where(func.lower(Merchant.category) == category.lower())
    if bank:
        base = base.where(func.lower(Bank.name) == bank.lower())
    # Exact card filter: show all discounts for this specific card (skip type/tier when card selected)
    if card and card.strip():
        base = base.where(Card.name == card.strip())
    elif card_type or card_tier:
        # Match card type on Card.type OR card name (e.g. "Meezan Bank Debit Card" matches "Debit")
        if card_type:
            ct = card_type.lower()
            base = base.where(
                or_(
                    func.lower(Card.type) == ct,
                    Card.name.ilike(f"%{card_type}%"),
                )
            )
        # Match card tier on Card.tier OR card name (e.g. "Basic Debit Card", "Gold Credit Card")
        if card_tier:
            ct = card_tier.lower()
            base = base.where(
                or_(
                    func.lower(func.coalesce(Card.tier, "")) == ct,
                    Card.name.ilike(f"%{card_tier}%"),
                )
            )

    # Apply keyword filter: when city was extracted from intent (e.g. "DHA Karachi"),
    # remaining words ("DHA") are used for ranking only - don't exclude deals without them.
    # When intent was provided directly (user typed, no city extraction), filter by keywords.
    if effective_intent and effective_intent.strip() and (city or not effective_city):
        words = [w.strip() for w in effective_intent.split() if w.strip()]
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

    if intent or effective_intent:
        discounts = rank_discounts(discounts, effective_city or "", effective_intent or intent or "")
    return {"count": len(discounts), "total_count": total_count, "results": discounts}
