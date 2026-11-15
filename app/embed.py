"""Embedding behind a small interface, so Azure OpenAI embeddings can replace it later."""

from __future__ import annotations

from collections.abc import Sequence
from functools import lru_cache
from typing import Protocol

from app.config import EMBED_MODEL, FASTEMBED_CACHE


class Embedder(Protocol):
    model_name: str

    def embed(self, texts: Sequence[str]) -> list[list[float]]: ...


class FastEmbedEmbedder:
    def __init__(self, model_name: str = EMBED_MODEL) -> None:
        from fastembed import TextEmbedding

        self.model_name = model_name
        self._model = TextEmbedding(model_name, cache_dir=str(FASTEMBED_CACHE))

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return [v.tolist() for v in self._model.embed(list(texts))]


@lru_cache(maxsize=1)
def default_embedder() -> Embedder:
    return FastEmbedEmbedder()
