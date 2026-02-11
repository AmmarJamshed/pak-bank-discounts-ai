from app.utils.text import clean_text


CITY_ALIASES = {
    "karachi": "Karachi",
    "lahore": "Lahore",
    "islamabad": "Islamabad",
    "rawalpindi": "Rawalpindi",
    "faisalabad": "Faisalabad",
    "multan": "Multan",
    "peshawar": "Peshawar",
    "quetta": "Quetta",
}

CATEGORY_ALIASES = {
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
    "electronics": "Electronics",
    "grocery": "Grocery",
    "entertainment": "Entertainment",
}


def normalize_city(city: str) -> str:
    city = clean_text(city).lower()
    return CITY_ALIASES.get(city, city.title())


def normalize_category(category: str) -> str:
    category = clean_text(category).lower()
    return CATEGORY_ALIASES.get(category, category.title())
