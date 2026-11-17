import csv
from pathlib import Path

path = Path("data/sources/manifest.csv")
with path.open(newline="") as handle:
    rows = list(csv.DictReader(handle))
required = {"title", "manufacturer", "product_model", "source_url"}
assert all(required <= set(row) for row in rows)
assert len({row["source_url"] for row in rows}) == len(rows)
print(f"Manifest contains {len(rows)} unique source URLs (target: 100–300)")
