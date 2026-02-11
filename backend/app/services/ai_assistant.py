import logging
import re
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Bank, Card, Discount, Merchant
from app.services.groq_client import GroqClient
from app.services.rag import RAGService
from app.services.recommender import rank_cards, rank_discounts
from app.services.serp_client import SerpApiClient

logger = logging.getLogger(__name__)


CITY_KEYWORDS = [
    "Karachi",
    "Lahore",
    "Islamabad",
    "Rawalpindi",
    "Faisalabad",
    "Multan",
    "Peshawar",
    "Quetta",
    "Hyderabad",
]

CATEGORY_KEYWORDS = {
    "food": "Food",
    "dining": "Food",
    "restaurant": "Food",
    "clothing": "Fashion",
    "fashion": "Fashion",
    "shopping": "Retail",
    "retail": "Retail",
    "travel": "Travel",
    "medical": "Medical",
    "health": "Medical",
    "grocery": "Grocery",
    "electronics": "Electronics",
}

MAX_TEXT_LEN = 240
STOPWORDS = {
    "best",
    "deals",
    "which",
    "what",
    "where",
    "who",
    "when",
    "is",
    "are",
    "the",
    "a",
    "an",
    "of",
    "in",
    "on",
    "for",
    "to",
    "and",
    "or",
    "with",
    "have",
    "has",
    "do",
    "does",
    "bank",
    "banks",
    "card",
    "cards",
    "credit",
    "debit",
    "discount",
    "discounts",
    "offer",
    "offers",
}

FOOD_TERMS = {
    "steak",
    "steaks",
    "steakhouse",
    "bbq",
    "barbecue",
    "burger",
    "burgers",
    "pizza",
    "pasta",
    "sushi",
    "shawarma",
    "kebab",
    "kebabs",
    "biryani",
    "coffee",
    "cafe",
    "cafes",
}


def parse_intent(query: str) -> dict[str, Any]:
    city = None
    for c in CITY_KEYWORDS:
        if re.search(rf"\b{re.escape(c)}\b", query, re.IGNORECASE):
            city = c
            break

    category = None
    for key, value in CATEGORY_KEYWORDS.items():
        if re.search(rf"\b{re.escape(key)}\b", query, re.IGNORECASE):
            category = value
            break
    if not category:
        for term in FOOD_TERMS:
            if re.search(rf"\b{re.escape(term)}\b", query, re.IGNORECASE):
                category = "Food"
                break

    occasion = None
    if "dinner" in query.lower() or "lunch" in query.lower():
        occasion = "Dining"
    if "shopping" in query.lower() or "clothing" in query.lower():
        occasion = "Shopping"
    if "travel" in query.lower():
        occasion = "Travel"
    if "medical" in query.lower() or "health" in query.lower():
        occasion = "Medical"
    if not occasion and category == "Food":
        occasion = "Dining"

    return {
        "city": city,
        "category": category,
        "occasion": occasion,
    }


def _safe_text(value: Any, max_len: int = MAX_TEXT_LEN) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(text) <= max_len:
        return text
    return f"{text[: max_len - 1]}…"


def _clean_response(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\uFFFD", "")
    text = re.sub(r"[\u0000-\u0009\u000B-\u001F\u007F-\u009F]", "", text)
    return text.strip()


def _extract_keywords(query: str) -> list[str]:
    tokens = re.findall(r"[A-Za-z]{3,}", query.lower())
    keywords = [token for token in tokens if token not in STOPWORDS]
    expanded: list[str] = []
    for token in keywords:
        expanded.append(token)
        if token.endswith("s") and len(token) > 3:
            expanded.append(token[:-1])
    deduped = list(dict.fromkeys(expanded))
    return deduped[:6]


def _filter_by_keywords(discounts: list[dict], keywords: list[str]) -> list[dict]:
    if not keywords:
        return discounts
    filtered = []
    for item in discounts:
        haystack = " ".join(
            [
                str(item.get("merchant", "")),
                str(item.get("category", "")),
                str(item.get("conditions", "")),
                str(item.get("card_name", "")),
                str(item.get("bank", "")),
                str(item.get("city", "")),
            ]
        ).lower()
        if any(keyword in haystack for keyword in keywords):
            filtered.append(item)
    return filtered


def _format_card_type(card_type: str) -> str:
    lowered = card_type.lower()
    if lowered == "credit":
        return "credit card"
    if lowered == "debit":
        return "debit card"
    return "card"


def _format_discount(value: Any) -> str:
    if value is None:
        return "discounts available"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "discounts available"
    if number.is_integer():
        return f"{int(number)}% off"
    return f"{number:.1f}% off"


def _card_label(bank: str, card_name: str) -> str:
    if bank and bank.lower() not in card_name.lower():
        return f"{bank} {card_name}".strip()
    return card_name or bank


def _keywords_for_search(keywords: list[str], intent: dict[str, Any]) -> list[str]:
    city_keyword = (intent.get("city") or "").lower()
    return [keyword for keyword in keywords if keyword != city_keyword]


def _keywords_for_display(keywords: list[str]) -> list[str]:
    cleaned: list[str] = []
    for keyword in sorted(keywords, key=len):
        if not any(keyword in existing or existing in keyword for existing in cleaned):
            cleaned.append(keyword)
    return cleaned


def _compact_discount(discount: dict) -> dict[str, Any]:
    return {
        "merchant": _safe_text(discount.get("merchant")),
        "discount_percent": discount.get("discount_percent"),
        "bank": _safe_text(discount.get("bank")),
        "card_name": _safe_text(discount.get("card_name")),
        "card_type": _safe_text(discount.get("card_type")),
        "city": _safe_text(discount.get("city")),
        "category": _safe_text(discount.get("category")),
        "valid_to": discount.get("valid_to"),
    }


def _compact_serp_item(item: dict) -> dict[str, Any]:
    return {
        "title": _safe_text(item.get("title")),
        "link": _safe_text(item.get("link"), 180),
        "snippet": _safe_text(item.get("snippet")),
    }


def _wants_card_reco(query: str) -> bool:
    lowered = query.lower()
    return any(
        phrase in lowered
        for phrase in [
            "which card",
            "which credit",
            "which debit",
            "best card",
            "recommend card",
            "suggest card",
        ]
    )


def _build_human_response(
    query: str, ranked: list[dict], cards: list[dict], intent: dict[str, Any]
) -> str:
    city = intent.get("city") or "your city"
    category = intent.get("category")
    category_text = f" for {category.lower()}" if category else ""
    keywords = _extract_keywords(query)
    display_keywords = _keywords_for_display(
        _keywords_for_search(keywords, intent)
    )

    if not ranked:
        if keywords:
            keyword_text = ", ".join(display_keywords[:3] or keywords[:3])
            return (
                f"I couldn’t find an exact match for {keyword_text}. "
                "Tell me a city or the restaurant name and I’ll narrow it down."
            )
        return (
            "I couldn’t find matching discounts yet. "
            "Tell me a city or a restaurant name and I’ll narrow it down."
        )

    top_merchants: dict[str, list[dict]] = {}
    for item in ranked:
        merchant = _safe_text(item.get("merchant"))
        if not merchant:
            continue
        top_merchants.setdefault(merchant, []).append(item)
        if len(top_merchants) >= 5:
            break

    if keywords and intent.get("keyword_focus"):
        keyword_text = ", ".join(display_keywords[:3] or keywords[:3])
        intro = (
            f"Here are {keyword_text} restaurants with bank card discounts in {city}:"
        )
        lines = [intro.strip()]
    elif keywords:
        keyword_text = ", ".join(display_keywords[:3] or keywords[:3])
        intro = f"Looking for {keyword_text} deals in {city}."
        followup = "Here are the closest matches I found:"
        lines = [intro.strip(), followup]
    else:
        intro = f"Here are the best{category_text} deals I found in {city}:"
        lines = [intro.strip()]
    for merchant, items in top_merchants.items():
        cards_for_merchant = []
        for item in items[:3]:
            bank = _safe_text(item.get("bank"))
            card_name = _safe_text(item.get("card_name"))
            card_type = _format_card_type(_safe_text(item.get("card_type")))
            card_tier = _safe_text(item.get("card_tier"))
            discount = _format_discount(item.get("discount_percent"))
            card_label = _card_label(bank, card_name)
            details = []
            if card_type and card_type != "card" and card_type not in card_label.lower():
                details.append(card_type)
            if card_tier:
                details.append(f"Tier: {card_tier}")
            detail_text = f" ({', '.join(details)})" if details else ""
            cards_for_merchant.append(
                f"{card_label}{detail_text} - {discount}"
            )
        lines.append(f"\n{merchant}")
        for card_line in cards_for_merchant:
            lines.append(f"- {card_line}")

    if _wants_card_reco(query) and cards:
        lines.append("\nIf you want a single best card overall, try:")
        for item in cards[:3]:
            bank = _safe_text(item.get("bank"))
            card_name = _safe_text(item.get("card_name"))
            card_type = _format_card_type(_safe_text(item.get("card_type")))
            card_tier = _safe_text(item.get("card_tier"))
            card_label = _card_label(bank, card_name)
            details = []
            if card_type and card_type != "card" and card_type not in card_label.lower():
                details.append(card_type)
            if card_tier:
                details.append(f"Tier: {card_tier}")
            detail_text = f" ({', '.join(details)})" if details else ""
            lines.append(f"- {card_label}{detail_text}")

    if not intent.get("city"):
        lines.append("\nTip: add a city for more accurate results.")
    lines.append("\nWant me to filter by a specific restaurant, area, or bank?")
    return "\n".join(lines)


async def _fetch_discount_candidates(
    session: AsyncSession, city: str | None, category: str | None
) -> list[dict]:
    counts = (
        await session.execute(
            select(Merchant.id, func.count(Discount.id))
            .join(Discount, Discount.merchant_id == Merchant.id)
            .group_by(Merchant.id)
        )
    ).all()
    count_map = {row[0]: int(row[1]) for row in counts}
    max_count = max(count_map.values(), default=1)

    query = (
        select(
            Discount.id.label("discount_id"),
            Discount.discount_percent,
            Discount.conditions,
            Discount.valid_from,
            Discount.valid_to,
            Merchant.name.label("merchant_name"),
            Merchant.id.label("merchant_id"),
            Merchant.city.label("merchant_city"),
            Merchant.category.label("merchant_category"),
            Card.name.label("card_name"),
            Card.type.label("card_type"),
            Card.tier.label("card_tier"),
            Bank.name.label("bank_name"),
        )
        .join(Merchant, Discount.merchant_id == Merchant.id)
        .join(Card, Discount.card_id == Card.id)
        .join(Bank, Card.bank_id == Bank.id)
    )
    if city:
        query = query.where(func.lower(Merchant.city) == city.lower())
    if category:
        query = query.where(func.lower(Merchant.category) == category.lower())

    result = await session.execute(query)
    discounts = []
    for row in result.all():
        discounts.append(
            {
                "discount_id": row.discount_id,
                "discount_percent": row.discount_percent,
                "conditions": row.conditions,
                "valid_from": row.valid_from.isoformat() if row.valid_from else None,
                "valid_to": row.valid_to.isoformat() if row.valid_to else None,
                "merchant": row.merchant_name,
                "city": row.merchant_city,
                "category": row.merchant_category,
                "card_name": row.card_name,
                "card_type": row.card_type,
                "card_tier": row.card_tier,
                "bank": row.bank_name,
                "merchant_popularity": count_map.get(row.merchant_id, 1) / max_count,
            }
        )
    return discounts


async def _build_card_suggestions(session: AsyncSession) -> list[dict]:
    query = (
        select(
            Card.name.label("card_name"),
            Card.type.label("card_type"),
            Card.tier.label("card_tier"),
            Bank.name.label("bank_name"),
            func.count(Discount.id).label("discount_count"),
            func.sum(Discount.discount_percent).label("discount_sum"),
            func.count(func.distinct(Merchant.city)).label("city_count"),
        )
        .join(Bank, Card.bank_id == Bank.id)
        .join(Discount, Discount.card_id == Card.id)
        .join(Merchant, Discount.merchant_id == Merchant.id)
        .group_by(Card.id, Bank.name)
    )
    result = await session.execute(query)
    cards = []
    for row in result.all():
        cards.append(
            {
                "card_name": row.card_name,
                "card_type": row.card_type,
                "card_tier": row.card_tier,
                "bank": row.bank_name,
                "merchant_coverage": float(row.discount_count),
                "total_discount_value": float(row.discount_sum or 0),
                "city_coverage": float(row.city_count),
            }
        )
    return rank_cards(cards)


async def run_assistant(
    session: AsyncSession, query: str, use_rag: bool = True
) -> dict[str, Any]:
    intent = parse_intent(query)
    rag_service = RAGService()
    serp_client = SerpApiClient()
    keywords = _extract_keywords(query)
    search_keywords = _keywords_for_search(keywords, intent)

    rag_hits = rag_service.search(query, top_k=6) if use_rag else []
    discounts = await _fetch_discount_candidates(
        session, intent.get("city"), intent.get("category")
    )

    if not discounts and rag_hits:
        discounts = rag_hits

    if search_keywords:
        filtered = _filter_by_keywords(discounts, search_keywords)
        if filtered:
            discounts = filtered
            intent["keyword_focus"] = True
        else:
            intent["keyword_focus"] = False

    ranked = rank_discounts(discounts, intent.get("city") or "", query)
    cards = await _build_card_suggestions(session)

    serp_fallback = []
    if not ranked:
        serp_fallback = await serp_client.search(query, num=5)

    response = _build_human_response(query, ranked[:12], cards, intent)

    return {
        "intent": intent,
        "recommendations": ranked[:10],
        "card_suggestions": cards[:5],
        "serp_fallback": serp_fallback,
        "response": _clean_response(response),
    }
