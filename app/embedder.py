from __future__ import annotations

import hashlib
import math
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings

from app.config import settings


_INDEX_DIR = Path("vector_store") / "faiss_index"


class LocalHashEmbeddings(Embeddings):
    def __init__(self, dim: int = 512):
        if dim <= 0:
            raise ValueError("local embedding dim must be > 0")
        self.dim = dim

    def _embed_text(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        for token in (text or "").lower().split():
            h = hashlib.sha256(token.encode("utf-8")).digest()
            idx = int.from_bytes(h[:4], "little") % self.dim
            sign = 1.0 if (h[4] & 1) == 0 else -1.0
            vec[idx] += sign

        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_text(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed_text(text)

    def __call__(self, text: str) -> list[float]:
        return self.embed_query(text)


def _get_embeddings():
    api_key = settings.openrouter_api_key or (settings.openai_api_key if settings.use_openai else "")
    if settings.use_local_embeddings or not api_key:
        return LocalHashEmbeddings(dim=settings.local_embedding_dim)

    base_url = settings.openrouter_base_url if settings.openrouter_api_key else None
    return OpenAIEmbeddings(model=settings.embedding_model, api_key=api_key, base_url=base_url)


def build_vector_store(chunks: list) -> FAISS:
    _INDEX_DIR.parent.mkdir(parents=True, exist_ok=True)

    embeddings = _get_embeddings()
    vector_store = FAISS.from_documents(chunks, embeddings)
    vector_store.save_local(str(_INDEX_DIR))
    return vector_store


def load_vector_store() -> FAISS:
    index_faiss = _INDEX_DIR / "index.faiss"
    index_pkl = _INDEX_DIR / "index.pkl"

    if not index_faiss.exists() or not index_pkl.exists():
        raise FileNotFoundError(
            f"FAISS index not found at '{_INDEX_DIR}'. Run 'python ingest.py' first."
        )

    embeddings = _get_embeddings()
    return FAISS.load_local(
        str(_INDEX_DIR),
        embeddings,
        allow_dangerous_deserialization=True,
    )
