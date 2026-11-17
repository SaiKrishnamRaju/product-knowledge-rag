"""Fetch the quantized MiniLM exports and their tokenizers."""
import argparse
import shutil
from pathlib import Path

from huggingface_hub import hf_hub_download

MODELS = {
    "embedder": "sentence-transformers/all-MiniLM-L6-v2",
    "reranker": "cross-encoder/ms-marco-MiniLM-L6-v2",
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--architecture", choices=("amd64", "arm64"), required=True)
    args = parser.parse_args()
    variant = {
        "amd64": "model_quint8_avx2.onnx",
        "arm64": "model_qint8_arm64.onnx",
    }[args.architecture]
    for kind, repo in MODELS.items():
        directory = args.output / kind
        directory.mkdir(parents=True, exist_ok=True)
        for source, destination in ((f"onnx/{variant}", "model.onnx"), ("tokenizer.json", "tokenizer.json")):
            shutil.copyfile(hf_hub_download(repo, source), directory / destination)


if __name__ == "__main__":
    main()
