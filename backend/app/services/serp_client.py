import logging
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings

logger = logging.getLogger(__name__)


class SerpApiClient:
    def __init__(self) -> None:
        self.base_url = "https://serpapi.com/search.json"
        self.api_key = settings.serp_api_key

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    async def search(self, query: str, num: int = 10) -> list[dict[str, Any]]:
        params = {
            "engine": "google",
            "q": query,
            "api_key": self.api_key,
            "num": num,
        }
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(self.base_url, params=params)
            response.raise_for_status()
            payload = response.json()
        results = payload.get("organic_results", []) or []
        logger.info("SERP API results for %s: %s", query, len(results))
        return results
