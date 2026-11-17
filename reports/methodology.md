# Evaluation methodology

The 40 questions must be hand-verified and tied to immutable corpus/chunk identifiers. Compare vector-only, hybrid RRF, and hybrid+rerank on identical corpus and query sets. Macro recall@5 and hit@5 exclude unanswerable questions. Faithfulness requires independent claim-level labels; unsupported question refusal accuracy is separate. Record corpus checksum, model IDs, latency and provider cost before publishing a benchmark. No metrics are available until the experiment has run.
