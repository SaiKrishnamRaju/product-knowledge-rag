import json
from pathlib import Path

categories = ["exact"] * 10 + ["semantic"] * 10 + ["disambiguation"] * 8 + ["multi_passage"] * 6 + ["unanswerable"] * 6
path = Path("data/eval/questions.jsonl")
if path.exists() and path.stat().st_size:
    raise SystemExit("Refusing to overwrite existing labels")
with path.open("w") as out:
    for i, category in enumerate(categories, 1):
        out.write(json.dumps({"id": f"q{i:02}", "category": category, "question": "",
                              "answerable": category != "unanswerable", "relevant_chunk_ids": [],
                              "reference_answer": "", "verified": False}) + "\n")
print("Created 40 UNLABELED templates; manual verification required before scoring")
