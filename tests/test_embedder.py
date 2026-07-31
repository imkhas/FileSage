from __future__ import annotations

import numpy as np

from organizer import embedder


class _FakeModel:
    def __init__(self, dim: int = 4) -> None:
        self.dim = dim

    def encode(
        self,
        texts,
        show_progress_bar=False,
        normalize_embeddings=True,
    ) -> np.ndarray:
        arr = np.array(
            [
                [sum(ord(c) for c in text) + i for i in range(self.dim)]
                for text in texts
            ],
            dtype=np.float32,
        )
        if normalize_embeddings:
            arr = arr / np.linalg.norm(arr, axis=1, keepdims=True)
        return arr


def _patch_model(monkeypatch, dim: int = 4) -> None:
    monkeypatch.setattr(embedder, "get_model", lambda: _FakeModel(dim=dim))


def test_embed_texts_returns_normalized_matrix(monkeypatch):
    _patch_model(monkeypatch)
    result = embedder.embed_texts(["alpha", "beta"])
    assert result.shape == (2, 4)
    assert np.allclose(np.linalg.norm(result, axis=1), 1.0)


def test_embed_query_returns_single_vector(monkeypatch):
    _patch_model(monkeypatch)
    result = embedder.embed_query("some query")
    assert result.shape == (1, 4)
