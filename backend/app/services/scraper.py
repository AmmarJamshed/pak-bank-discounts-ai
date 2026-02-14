import asyncio
import io
import json
import logging
import re
from dataclasses import dataclass
from datetime import date
from typing import Iterable

import httpx
from bs4 import BeautifulSoup
from dateutil import parser as date_parser
from PyPDF2 import PdfReader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.groq_client import GroqClient
from app.services.normalizer import normalize_category, normalize_city
from app.services.serp_client import SerpApiClient
from app.utils.text import clean_text, parse_discount_percent
from app.db.models import Bank, Card, Discount, Merchant

logger = logging.getLogger(__name__)


KNOWN_CITIES = [
    "Karachi",
    "Lahore",
    "Islamabad",
    "Rawalpindi",
    "Faisalabad",
    "Multan",
    "Peshawar",
    "Quetta",
    "Hyderabad",
    "Sialkot",
    "Gujranwala",
]

CARD_TIER_MAP = {
    "infinite": "Infinite",
    "signature": "Signature",
    "platinum": "Platinum",
    "gold": "Gold",
    "classic": "Classic",
    "basic": "Basic",
}
MAX_GROQ_FIXES = 50
# Peekaboo: fetch more entities per page and paginate more (target 4000+ deals)
PEEKABOO_PAGE_LIMIT = 50
PEEKABOO_MAX_PAGES = 30
MERCHANT_STOP_WORDS = re.compile(
    r"\b(with|using|via|when|till|until|valid|terms|conditions|offer|offers)\b",
    re.IGNORECASE,
)
MERCHANT_NOISE_WORDS = re.compile(
    r"\b(discount|cashback|off|deal|deals|promo|promotion|campaign)\b",
    re.IGNORECASE,
)
GENERIC_MERCHANT_PREFIXES = {
    "get",
    "enjoy",
    "now",
    "cash",
    "withdraw",
    "avail",
    "exclusive",
    "dining",
    "your",
    "a",
    "an",
    "up",
    "save",
    "profit",
    "rate",
    "earn",
    "pay",
    "from",
    "the",
    "ranging",
    "over",
}
GENERIC_MERCHANT_PHRASES = re.compile(
    r"\b(loan|facility|security|bank|account|credit|debit|card|discounts|offers|reward|balance|limit|statement|spending|categories|lifestyle)\b",
    re.IGNORECASE,
)


@dataclass
class BankSource:
    name: str
    website: str
    base_url: str
    peekaboo_base: str | None = None


@dataclass
class ScrapedDeal:
    merchant_name: str
    city: str
    category: str
    merchant_image_url: str | None
    discount_percent: float
    card_name: str
    card_tier: str
    card_type: str
    conditions: str
    valid_from: date | None
    valid_to: date | None


SOURCES = [
    BankSource(
        name="UBL",
        website="https://www.ubldigital.com/discounts",
        base_url="ubldigital.com",
    ),
    BankSource(
        name="Meezan Bank",
        website="https://www.meezanbank.com/card-discounts/",
        base_url="meezanbank.com",
        peekaboo_base="meezan-web.peekaboo.guru",
    ),
    BankSource(
        name="Bank Alfalah",
        website="https://www.bankalfalah.com/conventional/discounts-privileges/",
        base_url="bankalfalah.com",
        peekaboo_base="alfalah-web.peekaboo.guru",
    ),
    BankSource(
        name="HBL",
        website="https://www.hbl.com/personal/cards/hbl-deals-and-discounts",
        base_url="hbl.com",
        peekaboo_base="hbl-web.peekaboo.guru",
    ),
    BankSource(
        name="Bank of Punjab",
        website="https://www.bop.com.pk/Card-Discounts",
        base_url="bop.com.pk",
        peekaboo_base="bop-web.peekaboo.guru",
    ),
    BankSource(
        name="Standard Chartered Bank",
        website="https://www.sc.com/pk/promotions/",
        base_url="sc.com/pk",
    ),
    BankSource(
        name="BankIslami",
        website="https://bankislami.com.pk/discounts/",
        base_url="bankislami.com.pk",
    ),
    BankSource(
        name="JS Bank",
        website="https://www.jsbl.com/discounts/",
        base_url="jsbl.com",
    ),
    BankSource(
        name="Bank AL Habib",
        website="https://www.bankalhabib.com/discounts/",
        base_url="bankalhabib.com",
    ),
    BankSource(
        name="Habib Metro",
        website="https://www.habibmetro.com/discounts/",
        base_url="habibmetro.com",
    ),
]


def _guess_city(text: str) -> str:
    for city in KNOWN_CITIES:
        if re.search(rf"\b{re.escape(city)}\b", text, re.IGNORECASE):
            return normalize_city(city)
    return "Karachi"


def _guess_category(text: str) -> str:
    lowered = text.lower()
    if any(word in lowered for word in ["restaurant", "dining", "cafe", "food"]):
        return normalize_category("Food")
    if any(word in lowered for word in ["travel", "flight", "hotel"]):
        return normalize_category("Travel")
    if any(word in lowered for word in ["fashion", "clothing", "apparel"]):
        return normalize_category("Fashion")
    if any(word in lowered for word in ["grocery", "mart", "supermarket"]):
        return normalize_category("Grocery")
    if any(word in lowered for word in ["electronics", "gadgets"]):
        return normalize_category("Electronics")
    if any(word in lowered for word in ["health", "medical", "pharmacy"]):
        return normalize_category("Medical")
    return normalize_category("Retail")


def _parse_card_type(text: str) -> tuple[str, str]:
    lowered = text.lower()
    if "credit" in lowered:
        card_type = "Credit"
    elif "debit" in lowered:
        card_type = "Debit"
    else:
        card_type = "Card"
    tier = "Basic"
    for key, value in CARD_TIER_MAP.items():
        if key in lowered:
            tier = value
            break
    return card_type, tier


def _parse_dates(text: str) -> tuple[date | None, date | None]:
    match = re.search(
        r"(valid|till|until|through)\s+([A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4})",
        text,
        re.IGNORECASE,
    )
    if match:
        try:
            return None, date_parser.parse(match.group(2)).date()
        except (ValueError, TypeError):
            return None, None
    return None, None


def _looks_garbled(text: str) -> bool:
    cleaned = clean_text(text)
    if not cleaned:
        return True
    letters = len(re.findall(r"[A-Za-z]", cleaned))
    digits = len(re.findall(r"\d", cleaned))
    total = len(re.sub(r"\s", "", cleaned))
    readable_ratio = (letters + digits) / total if total else 0
    return letters < 4 or readable_ratio < 0.7


def _sanitize_merchant_name(name: str, bank_name: str) -> str:
    cleaned = clean_text(name)
    if not cleaned:
        return ""
    cleaned = MERCHANT_STOP_WORDS.split(cleaned)[0]
    cleaned = MERCHANT_NOISE_WORDS.sub("", cleaned)
    cleaned = re.sub(r"\b(card|cards|credit|debit|visa|mastercard|amex)\b", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\b\d+(\.\d+)?\b", "", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip(" -|,.;")

    bank_tokens = [t for t in re.split(r"\W+", bank_name.lower()) if t]
    for token in bank_tokens:
        cleaned = re.sub(rf"\b{re.escape(token)}\b", "", cleaned, flags=re.IGNORECASE)
    for city in KNOWN_CITIES:
        cleaned = re.sub(rf"\b{re.escape(city)}\b", "", cleaned, flags=re.IGNORECASE)

    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip(" -|,.;")
    return cleaned


def _is_valid_merchant(name: str, bank_name: str) -> bool:
    cleaned = clean_text(name)
    if not cleaned or len(cleaned) < 3:
        return False
    words = cleaned.split()
    if len(words) > 6:
        return False
    if words and words[0].lower() in GENERIC_MERCHANT_PREFIXES:
        return False
    if not any(word[:1].isupper() for word in words if word):
        return False
    if _looks_garbled(cleaned):
        return False
    lower = cleaned.lower()
    if bank_name.lower() in lower:
        return False
    if re.search(r"\b(card|credit|debit|discount|cashback|offer|offers|deal|deals)\b", lower):
        return False
    if GENERIC_MERCHANT_PHRASES.search(lower):
        return False
    return True


def _extract_merchant_name(line: str, bank_name: str) -> str:
    cleaned = clean_text(line)
    if not cleaned:
        return ""

    patterns = [
        r"^(?P<name>.+?)\s*(?:-|–|—|\|)\s*(?:up to\s*)?\d{1,2}%",  # Name - 20%
        r"^(?P<name>.+?)\s*(?:-|–|—|\|)\s*(?:discount|cashback|off)\b",
        r"^(?P<name>[A-Z][A-Za-z0-9&'’\-\.\s]{2,60})\s+(?:up to\s*)?\d{1,2}%",
        r"^(?:up to\s*)?\d{1,2}%\s*(?:off\s*)?(?:at\s*)?(?P<name>.+)$",
        r"\bmerchant\s*:\s*(?P<name>[A-Za-z0-9&'’\-\.\s]{3,})",
    ]
    for pattern in patterns:
        match = re.search(pattern, cleaned, re.IGNORECASE)
        if not match:
            continue
        name = _sanitize_merchant_name(match.group("name"), bank_name)
        if _is_valid_merchant(name, bank_name):
            return name

    if "%" in cleaned:
        left = cleaned.split("%")[0]
        left = re.sub(r"\b(up|upto|up to)\b.*", "", left, flags=re.IGNORECASE).strip()
        name = _sanitize_merchant_name(left, bank_name)
        if _is_valid_merchant(name, bank_name):
            return name

    return ""


async def _normalize_deal_with_groq(deal: ScrapedDeal, source: BankSource) -> ScrapedDeal:
    groq = GroqClient()
    prompt = (
        "You clean scraped bank discount text into structured fields.\n"
        "Return JSON only with keys: merchant_name, category, city, conditions.\n"
        "Use category values like Food, Retail, Fashion, Travel, Medical, Electronics, Grocery, Entertainment.\n"
        "Use Pakistan city names when possible. If unknown, keep city empty.\n\n"
        f"Bank: {source.name}\n"
        f"Raw text: {deal.conditions}\n"
    )
    try:
        response = await groq.chat(
            [
                {"role": "system", "content": "You output JSON only."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
        )
        payload = json.loads(response)
    except Exception as exc:
        logger.warning("Groq normalization failed: %s", exc)
        return deal

    merchant_name = clean_text(str(payload.get("merchant_name", "")))
    category = clean_text(str(payload.get("category", "")))
    city = clean_text(str(payload.get("city", "")))
    conditions = clean_text(str(payload.get("conditions", "")))

    if merchant_name and not _looks_garbled(merchant_name):
        deal.merchant_name = merchant_name
    if category:
        deal.category = normalize_category(category)
    if city:
        deal.city = normalize_city(city)
    if conditions:
        deal.conditions = conditions[:300]

    return deal


def _extract_deals_from_text(text: str, bank_name: str) -> list[ScrapedDeal]:
    deals: list[ScrapedDeal] = []
    lines = [clean_text(line) for line in text.split("\n") if line.strip()]
    for line in lines:
        if "%" not in line:
            continue
        discount_percent = parse_discount_percent(line)
        if discount_percent <= 0:
            continue
        merchant_name = _extract_merchant_name(line, bank_name)
        if not merchant_name:
            continue
        city = _guess_city(line)
        category = _guess_category(line)
        card_type, tier = _parse_card_type(line)
        valid_from, valid_to = _parse_dates(line)
        card_label = f"{bank_name} {tier} {card_type} Card".replace(" Card Card", " Card")
        deals.append(
            ScrapedDeal(
                merchant_name=merchant_name,
                city=city,
                category=category,
                merchant_image_url=None,
                discount_percent=discount_percent,
                card_name=card_label.strip(),
                card_tier=tier,
                card_type=card_type,
                conditions=line,
                valid_from=valid_from,
                valid_to=valid_to,
            )
        )
    return deals


async def _fetch_page(url: str) -> str:
    async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.text


def _extract_peekaboo_base(html: str) -> str | None:
    matches = re.findall(r"https?://([a-z0-9.-]*peekaboo\.guru)", html, re.IGNORECASE)
    if matches:
        return matches[0]
    matches = re.findall(r"//([a-z0-9.-]*peekaboo\.guru)", html, re.IGNORECASE)
    if matches:
        return matches[0]
    return None


def _extract_text_from_pdf_bytes(data: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(data), strict=False)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as exc:
        logger.warning("Failed to parse PDF content: %s", exc)
        return ""


async def _fetch_content(url: str) -> tuple[str, str]:
    async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()
        content_type = (response.headers.get("content-type") or "").lower()
        if "application/pdf" in content_type or url.lower().endswith(".pdf"):
            if response.content.startswith(b"%PDF"):
                return _extract_text_from_pdf_bytes(response.content), "pdf"
            # Some bank sites return HTML for PDF links (bot protection).
            text = response.content.decode("utf-8", "ignore")
            return text, "html"
        return response.text, "html"


def _city_slug(city: str) -> str:
    return city.lower().replace(" ", "-")


async def _fetch_peekaboo_config(base: str) -> dict:
    html = await _fetch_page(f"https://{base}/")
    soup = BeautifulSoup(html, "lxml")
    script_srcs = [s.get("src") for s in soup.find_all("script") if s.get("src")]
    for src in script_srcs:
        script_url = src if src.startswith("http") else f"https://{base}{src}"
        try:
            content = await _fetch_page(script_url)
        except Exception:
            continue
        match = re.search(r"window.__pkbg__\s*=\s*(\{[\s\S]*\})", content)
        if not match:
            continue
        return json.loads(match.group(1))
    return {}


def _peekaboo_entity_payload(
    city: str,
    country: str,
    limit: int,
    offset: int,
) -> dict:
    return {
        "fksyd": city,
        "n4ja3s": country,
        "js6nwf": "0",
        "pan3ba": "0",
        "mstoaw": "en",
        "angaks": "All",
        "j87asn": "_all",
        "makthya": "discount",
        "mnakls": str(limit),
        "opmsta": str(offset),
        "lkasx7": "",
        "ju8an3g": False,
        "sindfks": False,
        "kaiwnua": "_all",
        "klaosw": False,
    }


async def _scrape_peekaboo(source: BankSource) -> list[ScrapedDeal]:
    if not source.peekaboo_base:
        return []

    config = await _fetch_peekaboo_config(source.peekaboo_base)
    if not config:
        return []

    domain = str(config.get("DOMAIN", "https://secure-sdk.peekaboo.guru/")).rstrip("/")
    owner_key = config.get("OWNER_KEY")
    if not owner_key:
        return []

    headers = {
        "ownerkey": owner_key,
        "medium": "IFRAME",
        "version": str(config.get("VERSION", "1.0.0")),
        "Content-Type": "application/json",
    }
    limit = max(int(config.get("LIMIT", 12)), PEEKABOO_PAGE_LIMIT)
    country = str(config.get("BASE_COUNTRY", "Pakistan"))

    deals: list[ScrapedDeal] = []
    async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
        for city in KNOWN_CITIES:
            offset = 0
            for _ in range(PEEKABOO_MAX_PAGES):
                payload = _peekaboo_entity_payload(city, country, limit, offset)
                try:
                    response = await client.post(
                        f"{domain}/uljin2s3nitoi89njkhklgkj5",
                        headers=headers,
                        json=payload,
                    )
                    response.raise_for_status()
                    entities = response.json()
                except Exception as exc:
                    logger.warning("Peekaboo fetch failed for %s: %s", city, exc)
                    break

                if not entities:
                    break

                for entity in entities:
                    max_discount = float(entity.get("maxDiscount") or 0)
                    if max_discount <= 0:
                        continue
                    merchant_name = _sanitize_merchant_name(entity.get("name", ""), source.name)
                    if not _is_valid_merchant(merchant_name, source.name):
                        continue
                    merchant_image = entity.get("logo") or entity.get("cover")
                    description = entity.get("description", "")
                    keywords = entity.get("keywords", "")
                    meta_text = f"{keywords} {description} {entity.get('name', '')}"
                    category = _guess_category(meta_text)
                    discount_flag = str(entity.get("discountFlag") or "Up to")
                    conditions = clean_text(f"{discount_flag} {max_discount}% off")[:300]
                    card_type, tier = _parse_card_type(meta_text)
                    card_label = f"{source.name} {tier} {card_type} Card".replace(" Card Card", " Card")
                    deals.append(
                        ScrapedDeal(
                            merchant_name=merchant_name,
                            city=normalize_city(city),
                            category=category,
                            merchant_image_url=merchant_image,
                            discount_percent=max_discount,
                            card_name=card_label.strip(),
                            card_tier=tier,
                            card_type=card_type,
                            conditions=conditions,
                            valid_from=None,
                            valid_to=None,
                        )
                    )

                if len(entities) < limit:
                    break
                offset += limit

    return deals


async def scrape_source(source: BankSource) -> list[ScrapedDeal]:
    if source.peekaboo_base:
        deals = await _scrape_peekaboo(source)
        if deals:
            logger.info("Scraped %s deals from %s (peekaboo)", len(deals), source.name)
            return deals

    serp = SerpApiClient()
    query = f"site:{source.base_url} discounts offers card"
    results = await serp.search(query, num=100)
    urls = {source.website}
    for result in results:
        link = result.get("link")
        if link and source.base_url in link:
            urls.add(link)

    deals: list[ScrapedDeal] = []
    tasks = [asyncio.create_task(_fetch_content(url)) for url in urls]
    for task, url in zip(tasks, urls, strict=False):
        try:
            text, kind = await task
        except Exception as exc:
            logger.warning("Failed to fetch %s: %s", url, exc)
            continue
        if not text:
            continue
        if kind == "html" and not source.peekaboo_base:
            peekaboo_base = _extract_peekaboo_base(text)
            if peekaboo_base:
                discovered = BankSource(
                    name=source.name,
                    website=source.website,
                    base_url=source.base_url,
                    peekaboo_base=peekaboo_base,
                )
                peekaboo_deals = await _scrape_peekaboo(discovered)
                if peekaboo_deals:
                    logger.info(
                        "Scraped %s deals from %s (peekaboo discovered)",
                        len(peekaboo_deals),
                        source.name,
                    )
                    return peekaboo_deals
        if kind == "html":
            soup = BeautifulSoup(text, "lxml")
            text = soup.get_text("\n")
        deals.extend(_extract_deals_from_text(text, source.name))
    logger.info("Scraped %s deals from %s", len(deals), source.name)

    fixes_used = 0
    for idx, deal in enumerate(deals):
        if fixes_used >= MAX_GROQ_FIXES:
            break
        if _looks_garbled(deal.merchant_name):
            deals[idx] = await _normalize_deal_with_groq(deal, source)
            fixes_used += 1

    return deals


async def upsert_deals(session: AsyncSession, source: BankSource, deals: Iterable[ScrapedDeal]) -> int:
    bank = (
        await session.execute(select(Bank).where(Bank.name == source.name))
    ).scalar_one_or_none()
    if not bank:
        bank = Bank(name=source.name, website=source.website)
        session.add(bank)
        await session.flush()

    inserted = 0
    for deal in deals:
        if _looks_garbled(deal.merchant_name):
            continue

        merchant = (
            await session.execute(
                select(Merchant).where(Merchant.name == deal.merchant_name)
            )
        ).scalar_one_or_none()
        if not merchant:
            merchant = Merchant(
                name=deal.merchant_name,
                category=deal.category,
                city=deal.city,
                image_url=deal.merchant_image_url,
            )
            session.add(merchant)
            await session.flush()
        elif deal.merchant_image_url and not merchant.image_url:
            merchant.image_url = deal.merchant_image_url

        card = (
            await session.execute(
                select(Card).where(
                    Card.bank_id == bank.id,
                    Card.name == deal.card_name,
                )
            )
        ).scalar_one_or_none()
        if not card:
            card = Card(
                bank_id=bank.id,
                name=deal.card_name,
                tier=deal.card_tier,
                type=deal.card_type,
            )
            session.add(card)
            await session.flush()

        existing = (
            await session.execute(
                select(Discount).where(
                    Discount.merchant_id == merchant.id,
                    Discount.card_id == card.id,
                    Discount.discount_percent == deal.discount_percent,
                    Discount.valid_from == deal.valid_from,
                    Discount.valid_to == deal.valid_to,
                )
            )
        ).scalar_one_or_none()
        if existing:
            continue

        discount = Discount(
            merchant_id=merchant.id,
            card_id=card.id,
            discount_percent=deal.discount_percent,
            conditions=deal.conditions,
            valid_from=deal.valid_from,
            valid_to=deal.valid_to,
        )
        session.add(discount)
        inserted += 1

    await session.commit()
    return inserted


async def run_full_scrape(session: AsyncSession) -> int:
    total_inserted = 0
    for source in SOURCES:
        deals = await scrape_source(source)
        if not deals:
            continue
        inserted = await upsert_deals(session, source, deals)
        total_inserted += inserted
    logger.info("Inserted %s new discounts", total_inserted)
    return total_inserted
