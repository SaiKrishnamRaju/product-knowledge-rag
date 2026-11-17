"""Quantized MiniLM inference using ONNX Runtime without PyTorch."""
from functools import lru_cache
from pathlib import Path
from threading import Lock

import numpy as np

inference_lock = Lock()


@lru_cache(maxsize=2)
def _load(directory: Path, max_length: int):
    import onnxruntime as ort
    from tokenizers import Tokenizer

    tokenizer = Tokenizer.from_file(str(directory / "tokenizer.json"))
    tokenizer.enable_truncation(max_length=max_length)
    tokenizer.enable_padding(pad_id=0, pad_token="[PAD]")
    options = ort.SessionOptions()
    options.intra_op_num_threads = 1
    options.inter_op_num_threads = 1
    session = ort.InferenceSession(
        str(directory / "model.onnx"), options, providers=["CPUExecutionProvider"]
    )
    return tokenizer, session


def _infer(directory: Path, items, max_length: int):
    tokenizer, session = _load(directory, max_length)
    encoded = tokenizer.encode_batch(items)
    inputs = {
        "input_ids": np.asarray([item.ids for item in encoded], dtype=np.int64),
        "attention_mask": np.asarray([item.attention_mask for item in encoded], dtype=np.int64),
        "token_type_ids": np.asarray([item.type_ids for item in encoded], dtype=np.int64),
    }
    output = session.run(None, {input.name: inputs[input.name] for input in session.get_inputs()})
    return output[0], inputs["attention_mask"]


def embed(directory: Path, texts: list[str]) -> list[list[float]]:
    vectors = []
    with inference_lock:
        for start in range(0, len(texts), 16):
            tokens, mask = _infer(directory, texts[start:start + 16], max_length=256)
            pooled = (tokens * mask[:, :, None]).sum(axis=1) / mask.sum(axis=1, keepdims=True)
            normalized = pooled / np.maximum(np.linalg.norm(pooled, axis=1, keepdims=True), 1e-12)
            vectors.extend(normalized.tolist())
    return vectors


def score(directory: Path, pairs: list[tuple[str, str]]) -> list[float]:
    scores = []
    with inference_lock:
        for start in range(0, len(pairs), 4):
            logits, _ = _infer(directory, pairs[start:start + 4], max_length=512)
            scores.extend(logits.reshape(-1).tolist())
    return scores
