from __future__ import annotations

import logging
import os

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

import numpy as np
from transformers.utils import logging as tf_logging

from sentence_transformers import SentenceTransformer

tf_logging.set_verbosity_error()
tf_logging.disable_progress_bar()

for _name in (
    "huggingface_hub",
    "huggingface_hub.utils._http",
    "httpx",
    "httpcore",
    "sentence_transformers",
):
    logging.getLogger(_name).setLevel(logging.ERROR)

MODEL_NAME = "all-MiniLM-L6-v2"
_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed_texts(texts: list[str]) -> np.ndarray:
    model = get_model()
    return model.encode(texts, show_progress_bar=False, normalize_embeddings=True)


def embed_query(query: str) -> np.ndarray:
    return embed_texts([query])
