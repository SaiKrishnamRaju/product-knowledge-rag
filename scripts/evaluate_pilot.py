"""Compare retrieval modes on manually labeled source pages."""
import argparse
import csv
from pathlib import Path

from sqlalchemy import select

from app.db.models import Chunk, Document
from app.db.session import SessionLocal
from app.evaluation import recall_at_k
from app.retrieval.service import retrieve

MODES = ("vector", "hybrid", "hybrid_rerank")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=Path("data/eval/pilot.tsv"))
    args = parser.parse_args()
    with args.cases.open(newline="") as file:
        cases = list(csv.DictReader(file, delimiter="\t"))
    if not cases or len({case["question"] for case in cases}) != len(cases):
        raise SystemExit("Evaluation requires a nonempty set of unique questions")
    totals = dict.fromkeys(MODES, 0)
    recalls = dict.fromkeys(MODES, 0.0)
    with SessionLocal() as db:
        for case in cases:
            page = int(case["page"])
            candidates = db.scalars(
                select(Chunk).join(Document).where(
                    Document.product_model == case["product_model"], Chunk.page_number == page
                )
            )
            evidence = {
                chunk.id for chunk in candidates
                if case["evidence_anchor"].casefold() in chunk.content.casefold()
            }
            if not evidence:
                raise SystemExit(f"Missing indexed evidence for {case['question']}")
            matches = []
            for mode in MODES:
                # Compare unfiltered retrieval. Model names come from each question.
                hits = retrieve(db, case["question"], mode, 5)
                retrieved_ids = [str(chunk.id) for chunk in hits]
                recalls[mode] += recall_at_k({str(chunk_id) for chunk_id in evidence}, retrieved_ids, 5)
                if evidence.intersection(chunk.id for chunk in hits):
                    totals[mode] += 1
                    matches.append(mode)
            print(f"{case['product_model']} p{page} | {case['question']} | {', '.join(matches)}")
    for mode, hits in totals.items():
        print(f"{mode}: {hits}/{len(cases)} canonical evidence hits at 5, recall@5={recalls[mode] / len(cases):.3f}")


if __name__ == "__main__":
    main()
