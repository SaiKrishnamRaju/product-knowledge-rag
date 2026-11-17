import csv
from pathlib import Path

from app.db.session import SessionLocal
from app.ingestion.download import download_pdf
from app.ingestion.pipeline import ingest_file

manifest = Path("data/sources/manifest.csv")
failures = 0
with manifest.open(newline="") as handle, SessionLocal() as db:
    for row in csv.DictReader(handle):
        try:
            path = Path("data/downloads") / (row["product_model"].replace("/", "_") + ".pdf")
            download_pdf(row["source_url"], path)
            doc, created = ingest_file(db, path, title=row["title"], source_url=row["source_url"],
                                       manufacturer=row["manufacturer"], product_model=row["product_model"])
            print(doc.title, "indexed" if created else "already present")
        except Exception as exc:  # noqa: BLE001 — report per-source failures and continue the batch
            failures += 1
            db.rollback()
            print(row.get("source_url"), "FAILED", exc)

if failures:
    raise SystemExit(f"{failures} source(s) failed to index")
