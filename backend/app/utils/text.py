import re


def clean_text(value: str) -> str:
    if not value:
        return ""
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def parse_discount_percent(text: str) -> float:
    if not text:
        return 0.0
    match = re.search(r"(\d{1,3})(?:\.\d+)?\s*%+", text)
    if match:
        return float(match.group(1))
    match = re.search(r"(\d{1,3})\s*percent", text, re.IGNORECASE)
    if match:
        return float(match.group(1))
    return 0.0


def extract_validity(text: str) -> tuple[str | None, str | None]:
    if not text:
        return None, None
    match = re.search(
        r"(valid|till|until|through)\s+([A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4})",
        text,
        re.IGNORECASE,
    )
    if match:
        return None, match.group(2)
    return None, None
