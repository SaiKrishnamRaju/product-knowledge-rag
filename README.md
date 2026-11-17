# Product Knowledge RAG

**Status** · The local Apple Silicon setup was verified with PostgreSQL, pgvector, and MiniLM.

The starter corpus contains seven official Raspberry Pi documents. The project target
is 100–300 public product manuals or spec sheets. Live Claude and deployment are pending.

## Architecture

```mermaid
flowchart TD
  PDFs[Public PDFs] --> Extract[Page-aware extraction and chunking]
  Extract --> Embed[Local embeddings]
  Embed --> DB[(PostgreSQL + pgvector + FTS)]
  User[Browser / API] --> FastAPI
  FastAPI --> Vector[Vector search]
  FastAPI --> Lexical[Full-text search]
  DB --> Vector
  DB --> Lexical
  Vector --> RRF[RRF fusion]
  Lexical --> RRF
  RRF --> Rerank[Cross-encoder reranking]
  Rerank --> Claude[Claude grounded generation]
  Claude --> Verify[Citation validation]
  Verify --> User
```

## Setup

Extract the Phase 2 ZIP and open Terminal in the `product-knowledge-rag` folder.
Use native Python 3.12 on Apple Silicon. Install and open the Apple Silicon edition
of [Docker Desktop](https://docs.docker.com/desktop/setup/install/mac-install/).
Run PostgreSQL in Docker and Python directly on macOS.

```bash
uname -m                         # arm64 on Apple Silicon
python3.12 --version
docker info --format '{{.Architecture}}'
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
test -f .env || cp .env.example .env
docker compose up -d --wait db
python -m alembic upgrade head
python -m pytest -q
```

For the PostgreSQL integration test, create a separate disposable database.
Run the `createdb` command once per Compose volume.

```bash
docker compose exec -T db createdb -U app product_rag_test
TEST_DATABASE_URL=postgresql+psycopg://app:app@127.0.0.1:5432/product_rag_test python -m pytest -q
```

The database test generates a PDF locally, runs the migration, and exercises
ingestion, pgvector, full-text search, retrieval modes and page citations.
It substitutes deterministic model outputs by default. Set `TEST_REAL_MODELS=1`
to exercise the real embedder and reranker. Both variants simulate Claude.

Add reviewed, legally usable HTTPS PDF sources to `data/sources/manifest.csv` before
ingesting. The first real model run downloads the public MiniLM weights.

```bash
python -m scripts.ingest
python -m uvicorn app.main:app --reload
```

Open [the local app](http://localhost:8000), [API docs](http://localhost:8000/docs),
or [database readiness](http://localhost:8000/ready). With Claude disabled,
use `POST /api/v1/search` to check retrieved passages and page numbers.
Keep `.env` private and leave live generation disabled for a public demo.
Claude calls may incur charges.

## API

- `GET /health` — process health
- `GET /ready` — database connectivity
- `GET /api/v1/stats` — document and chunk counts
- `GET /api/v1/documents` — indexed manuals
- `POST /api/v1/search` — retrieval candidates
- `POST /api/v1/ask` — grounded answer or refusal

Example:

```bash
curl -X POST http://localhost:8000/api/v1/ask -H 'Content-Type: application/json' -d '{"question":"What voltage does model X require?","retrieval_mode":"hybrid_rerank","top_k":5}'
```

## Evaluation

```bash
python -m scripts.build_eval_set
# Manually label and verify all 40 cases; add actual relevant chunk IDs
python -m scripts.evaluate
python -m scripts.export_results
python -m pytest -q
```

The evaluator refuses to publish results unless 40 verified cases exist. `reports/results-template.md` is a placeholder, not evidence. Faithfulness and refusal accuracy need additional evaluators before they can be reported.

## Deployment

[Neon Free](https://neon.com/blog/neon-free-plan-1-gb-per-project) documents 1 GB of
Postgres storage per project and [supports pgvector](https://neon.com/docs/extensions/pgvector).
Render's [free PostgreSQL expires after 30 days](https://render.com/docs/free).
For a hosted smoke test, use a Neon Free test database, run the migration using its
direct TLS connection with the `postgresql+psycopg://` scheme, and verify the vector
extension, retrieval, and storage with the intended dataset. Keep the connection
string in an environment variable and out of Git.

Render's [free web service](https://render.com/pricing) has 512 MB RAM. The configured
reranker and embedder each have roughly 91 MB of weights. Model runtime, both loaded
models, inference activations, and server overhead need to fit the same limit.

```bash
python -m scripts.check_model_memory
docker build --platform linux/amd64 -t product-knowledge-rag .
docker run --rm --platform linux/amd64 --memory=512m --memory-swap=512m \
  product-knowledge-rag python -m scripts.check_model_memory
```

On November 17, 2026, the standalone probe peaked at 504.5 MiB process RSS on
Apple Silicon. The CPU-only Linux/amd64 image was killed by Docker at 512 MiB
with swap disabled. Under a 1 GiB cap, it completed with 722.0 MiB process RSS
and 909,332,480 bytes of peak container memory (approximately 867 MiB). The
probe runs one embedding and reranks 20 candidates with locally cached model
files. The CPU-only image in this checkpoint exceeds the free Render limit.

The standalone probe is a first gate. A passing probe still needs a cold start
and representative concurrent API requests under the same limit before deployment.
Measure with the serving image and full model configuration. If it exceeds the
limit, retest a smaller or quantized runtime before committing to the free service.

## Limitations

- The local prototype has no production release.
- The seven-document corpus is below the 100–300 document target; the current 40 questions cover answerable retrieval only.
- No rate limiter or hard spending cap is implemented yet; do not expose paid generation publicly.
- Citation ID checks do not establish factual faithfulness.
- PDF downloader should only be run on a trusted, reviewed manifest.
- Langfuse request events were tested locally with a simulated client. Hosted export is pending.
- Hosted database, live Claude calls, and the deployed API still need verification.
- No public URL has been created or tested.

MIT licensed code. Public PDF copyright remains with the respective rights holders.

### Four-document retrieval pilot

The included manifest links four Raspberry Pi datasheets. After ingesting them,
run `python -m scripts.evaluate_pilot` to compare unfiltered retrieval on 12
questions labeled against specific PDF pages. On the local 153-chunk index,
the canonical evidence appeared in the first five results for 11/12 vector,
6/12 hybrid, and 11/12 hybrid-plus-rerank queries. The pilot measures evidence
hits for these questions only. It does not call Claude.

### 40-question retrieval evaluation

After ingesting the seven documents in the manifest, run:

```bash
python -m scripts.evaluate_pilot --cases data/eval/raspberry-pi-40.tsv
```

All questions are answerable and labeled with a model, PDF page, expected answer,
and evidence anchor. The evaluator checks each anchor in the local index and
searches the entire corpus without a product filter. Recall is measured against
the matching chunks on the labeled page. Other pages can contain valid evidence.

| Retrieval mode | Evidence in top 5 | Recall@5 |
| --- | ---: | ---: |
| Vector | 28/40 | 0.700 |
| Hybrid | 20/40 | 0.500 |
| Hybrid with reranking | 34/40 | 0.850 |

These results cover the seven-document, 250-chunk Raspberry Pi corpus. This run
did not measure answer faithfulness or unsupported-question refusals.

### Request telemetry

Search and answer requests log retrieval mode, chunk count, and latency.
Answer requests also log outcome and citation count when available.
To export these events, set both Langfuse keys in your local environment, give
`LANGFUSE_BASE_URL` your project's endpoint if needed, and restart the app.
Questions, passages, and answer text are excluded from these events.

### Quantized Linux image

`Dockerfile.onnx` is an opt-in image for memory-constrained hosting. It uses
the model publishers' quantized MiniLM exports and excludes PyTorch. The
default local runtime still uses PyTorch. The Render blueprint selects the quantized image.
The amd64 build uses the AVX2 export. Use an AVX2-capable deployment CPU.

```bash
docker build --platform linux/amd64 -f Dockerfile.onnx -t product-knowledge-rag:onnx .
docker run --rm --platform linux/amd64 --memory=512m --memory-swap=512m --cpus=0.5 \
  product-knowledge-rag:onnx python -m scripts.check_model_memory
```

The standalone Linux probe used approximately 413 MiB peak container memory.
On Apple Silicon, quantized queries against the existing 250-chunk index
scored 70.0% (vector), 52.5% (hybrid), and 82.5% (hybrid with reranking)
recall@5 on the same 40 questions. The local index used PyTorch embeddings.

A local Linux/amd64 API smoke test used a separate PostgreSQL/pgvector container
with the seven-document index. All eight reranked searches returned the
expected Pico evidence, with up to four requests in flight. The app container
peaked at 510,824,448 bytes (about 487 MiB), including the local probe client,
under a 512 MiB cap with swap disabled and a half-CPU quota. This leaves about
25 MiB of headroom in this run. The test used one short question repeatedly.
Hosted startup, broader workloads, and live Claude remain unverified.
