"""Measure a cold inference pass. In a container, read the cgroup limit and peak."""
import platform
import resource
from pathlib import Path
from types import SimpleNamespace

from app.config import get_settings
from app.retrieval.embed import embed_texts
from app.retrieval.rerank import rerank


def main():
    settings = get_settings()
    question = "What voltage is required for the device?"
    embedding = embed_texts([question])[0]
    assert len(embedding) == 384
    candidates = [
        SimpleNamespace(content=f"Page {i}: " + "The device operates on 24 volts. " * 70)
        for i in range(settings.fusion_top_k)
    ]
    assert len(rerank(question, candidates, settings.final_top_k)) == min(
        settings.final_top_k, len(candidates)
    )
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    peak_bytes = peak if platform.system() == "Darwin" else peak * 1024
    print(f"Python process peak RSS: {peak_bytes / 2**20:.1f} MiB")
    for name in ("memory.max", "memory.peak"):
        path = Path("/sys/fs/cgroup") / name
        if path.exists():
            print(f"Container {name} (bytes): {path.read_text().strip()}")


if __name__ == "__main__":
    main()
