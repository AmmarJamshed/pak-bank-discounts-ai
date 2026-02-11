import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Bank, Card, Discount, Merchant
from app.services.embeddings import EmbeddingService

logger = logging.getLogger(__name__)


class RAGService:
    def __init__(self) -> None:
        self.embedding_service = EmbeddingService()

    async def rebuild_index(self, session: AsyncSession) -> int:
        query = (
            select(
                Discount.id.label("discount_id"),
                Discount.discount_percent,
                Discount.conditions,
                Discount.valid_from,
                Discount.valid_to,
                Merchant.name.label("merchant_name"),
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
        result = await session.execute(query)
        rows = result.all()

        texts = []
        metadata = []
        for row in rows:
            text = (
                f"{row.merchant_name} {row.merchant_city} {row.merchant_category} "
                f"{row.discount_percent}% {row.card_name} {row.card_type} {row.card_tier} "
                f"Bank {row.bank_name} {row.conditions or ''}"
            )
            texts.append(text)
            metadata.append(
                {
                    "discount_id": row.discount_id,
                    "merchant": row.merchant_name,
                    "city": row.merchant_city,
                    "category": row.merchant_category,
                    "discount_percent": row.discount_percent,
                    "card_name": row.card_name,
                    "card_type": row.card_type,
                    "card_tier": row.card_tier,
                    "bank": row.bank_name,
                    "conditions": row.conditions,
                    "valid_from": row.valid_from.isoformat() if row.valid_from else None,
                    "valid_to": row.valid_to.isoformat() if row.valid_to else None,
                }
            )
        self.embedding_service.build_index(texts, metadata)
        logger.info("Rebuilt FAISS index with %s entries", len(texts))
        return len(texts)

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        return self.embedding_service.search(query, top_k=top_k)
