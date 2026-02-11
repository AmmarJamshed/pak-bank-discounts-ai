import json
import logging
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self) -> None:
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.index_path = Path(settings.faiss_index_path)
        self.meta_path = Path(settings.faiss_metadata_path)
        self.index: faiss.Index | None = None
        self.metadata: list[dict] = []

    def embed(self, texts: list[str]) -> np.ndarray:
        return np.array(self.model.encode(texts, show_progress_bar=False)).astype("float32")

    def build_index(self, texts: list[str], metadata: list[dict]) -> None:
        if not texts:
            self.index = faiss.IndexFlatIP(384)
            self.metadata = []
            return
        vectors = self.embed(texts)
        faiss.normalize_L2(vectors)
        self.index = faiss.IndexFlatIP(vectors.shape[1])
        self.index.add(vectors)
        self.metadata = metadata
        self.save()

    def save(self) -> None:
        if not self.index:
            return
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(self.index_path))
        self.meta_path.write_text(json.dumps(self.metadata, ensure_ascii=False, indent=2))
        logger.info("FAISS index saved: %s", self.index_path)

    def load(self) -> None:
        if self.index_path.exists() and self.meta_path.exists():
            self.index = faiss.read_index(str(self.index_path))
            self.metadata = json.loads(self.meta_path.read_text())
            logger.info("FAISS index loaded: %s", self.index_path)

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        if not self.index:
            self.load()
        if not self.index:
            return []
        vector = self.embed([query])
        faiss.normalize_L2(vector)
        scores, indices = self.index.search(vector, top_k)
        results: list[dict] = []
        for idx, score in zip(indices[0], scores[0], strict=False):
            if idx == -1:
                continue
            record = self.metadata[idx].copy()
            record["score"] = float(score)
            results.append(record)
        return results
