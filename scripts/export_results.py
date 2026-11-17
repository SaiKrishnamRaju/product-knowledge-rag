import csv
import json
from pathlib import Path

path = Path("reports/results.json")
if not path.exists():
    raise SystemExit("No measured results; run evaluate.py with verified labels")
data = json.loads(path.read_text())
with Path("reports/results.csv").open("w", newline="") as out:
    writer = csv.writer(out)
    writer.writerow(["method", "recall_at_5", "hit_at_5"])
    for name, metrics in data.items():
        writer.writerow([name, metrics["recall_at_5"], metrics["hit_at_5"]])
