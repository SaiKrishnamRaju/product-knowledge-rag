import json
from pathlib import Path

from app.db.session import SessionLocal
from app.evaluation import hit_at_k, recall_at_k
from app.retrieval.service import retrieve

cases = [json.loads(line) for line in Path("data/eval/questions.jsonl").read_text().splitlines() if line.strip()]
if len(cases) != 40 or not all(c.get("verified") and c.get("question") for c in cases):
    raise SystemExit("40 verified labeled questions required; no metrics published")
answerable = [case for case in cases if case["answerable"]]
if not answerable or any(not case.get("relevant_chunk_ids") for case in answerable):
    raise SystemExit("Answerable questions must have verified relevant chunk IDs")
results = {}
with SessionLocal() as db:
    for mode in ("vector", "hybrid", "hybrid_rerank"):
        records = []
        for case in answerable:
            ids = [str(c.id) for c in retrieve(db, case["question"], mode, 5)]
            relevant = case["relevant_chunk_ids"]
            records.append({"id": case["id"], "recall_at_5": recall_at_k(relevant, ids, 5),
                            "hit_at_5": hit_at_k(relevant, ids, 5)})
        results[mode] = {"recall_at_5": sum(r["recall_at_5"] for r in records) / len(records),
                         "hit_at_5": sum(r["hit_at_5"] for r in records) / len(records),
                         "per_question": records}
Path("reports/results.json").write_text(json.dumps(results, indent=2))
print(json.dumps({m: {k:v for k,v in r.items() if k != "per_question"} for m,r in results.items()}, indent=2))
print("Faithfulness requires separate claim-level annotation; not measured here")
