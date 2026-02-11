from __future__ import annotations

from datetime import date

from rapidfuzz import fuzz


CARD_ACCESSIBILITY = {
    "debit": 1.0,
    "basic": 0.9,
    "classic": 0.85,
    "gold": 0.8,
    "platinum": 0.7,
    "signature": 0.6,
    "infinite": 0.5,
}


def _validity_window(valid_to: str | None) -> float:
    if not valid_to:
        return 0.6
    try:
        valid_date = date.fromisoformat(valid_to)
    except ValueError:
        return 0.6
    remaining = max((valid_date - date.today()).days, 0)
    if remaining >= 60:
        return 1.0
    if remaining >= 30:
        return 0.8
    if remaining >= 7:
        return 0.6
    return 0.4


def _location_proximity(user_city: str, merchant_city: str) -> float:
    if not user_city or not merchant_city:
        return 0.5
    score = fuzz.partial_ratio(user_city.lower(), merchant_city.lower()) / 100.0
    return max(0.2, score)


def _intent_match(intent: str, text: str) -> float:
    if not intent:
        return 0.4
    score = fuzz.token_set_ratio(intent.lower(), text.lower()) / 100.0
    return max(0.3, score)


def rank_discounts(
    discounts: list[dict], user_city: str, intent: str
) -> list[dict]:
    for discount in discounts:
        merchant_popularity = min(discount.get("merchant_popularity", 0.6), 1.0)
        location_proximity = _location_proximity(user_city, discount.get("city", ""))
        card_accessibility = CARD_ACCESSIBILITY.get(
            (discount.get("card_type") or "debit").lower(), 0.7
        )
        if discount.get("card_tier"):
            card_accessibility = min(
                card_accessibility,
                CARD_ACCESSIBILITY.get(discount["card_tier"].lower(), card_accessibility),
            )
        validity_window = _validity_window(discount.get("valid_to"))
        user_intent_match = _intent_match(
            intent,
            f"{discount.get('merchant')} {discount.get('category')} {discount.get('conditions')}",
        )

        discount_factor = min(discount.get("discount_percent", 0) / 100, 1.0)
        score = 100 * (
            discount_factor * 0.35
            + merchant_popularity * 0.15
            + location_proximity * 0.15
            + card_accessibility * 0.15
            + validity_window * 0.10
            + user_intent_match * 0.10
        )
        discount["score"] = round(score, 2)
    return sorted(discounts, key=lambda x: x["score"], reverse=True)


def rank_cards(cards: list[dict]) -> list[dict]:
    for card in cards:
        total_discount_value = card.get("total_discount_value", 0.0)
        merchant_coverage = card.get("merchant_coverage", 0.0)
        city_coverage = card.get("city_coverage", 0.0)
        score = (
            total_discount_value * 0.4
            + merchant_coverage * 0.35
            + city_coverage * 0.25
        )
        card["card_score"] = round(score, 2)
    return sorted(cards, key=lambda x: x["card_score"], reverse=True)
