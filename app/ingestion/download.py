import hashlib
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.parse import urlparse

import httpx


def download_pdf(url: str, destination: Path, max_bytes: int = 25_000_000) -> str:
    if urlparse(url).scheme != "https":
        raise ValueError("Only HTTPS PDF sources are accepted")

    destination.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    total = 0

    # Stage the download beside its destination so replacement is atomic.
    with NamedTemporaryFile(dir=destination.parent, delete=False) as handle:
        staged = Path(handle.name)
    try:
        with httpx.stream("GET", url, follow_redirects=True, timeout=45) as response:
            response.raise_for_status()
            if urlparse(str(response.url)).scheme != "https":
                raise ValueError("Insecure redirect")
            with staged.open("wb") as handle:
                for block in response.iter_bytes():
                    total += len(block)
                    if total > max_bytes:
                        raise ValueError("PDF too large")
                    digest.update(block)
                    handle.write(block)

        with staged.open("rb") as handle:
            if handle.read(5) != b"%PDF-":
                raise ValueError("Not a PDF")
        staged.replace(destination)
        return digest.hexdigest()
    finally:
        staged.unlink(missing_ok=True)
