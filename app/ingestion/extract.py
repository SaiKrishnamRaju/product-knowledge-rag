from pathlib import Path

import fitz


def extract_pages(path: str | Path) -> list[dict]:
    pages = []
    with fitz.open(path) as pdf:
        for i, page in enumerate(pdf):
            text = page.get_text("text").replace("\x00", " ").strip()
            pages.append({"page_number": i + 1, "text": text})
    return pages
