# SpecGraph Intelligence Engine

SpecGraph is an industrial product-evidence workbench. It does not ask an LLM to decide what is true: Mistral extracts bounded claims from source chunks, then deterministic, inspectable stages verify citation text, resolve product identity, surface source disagreement, and validate physical plausibility. Neo4j stores the provenance graph that makes each conclusion traceable.

## What the demo proves

- 54 plain-text source documents resolve into 18 industrial products: bearings, relays/contactors, and fasteners.
- Source claims retain their exact cited text, nearest source context, verification score, source filename, type, and reliability tier.
- Conflicting values remain visible; tier 1 manufacturer evidence is preferred automatically but never overwrites the other claim.
- Electrical and dimensional rules independently flag physically implausible claims.
- Identity clustering uses MinHash LSH before scoring candidate pairs; no N×N comparison is performed.

## Architecture

```
Source markdown → Mistral extraction (chunked JSON) → citation verification
                → MinHash candidates + local embedding/MPN/category scoring
                → deterministic contradiction + physics checks → Neo4j graph
                                                               ↓
                                                 FastAPI evidence API → React workbench
```

Only `pipeline/extraction` imports the LLM layer. `entity_resolution`, `contradiction`, and `validation` are pure deterministic Python modules; `python -m app.check_boundaries` is enforced by the test command.

## Run locally

Prerequisites: Docker, Python 3.12, [uv](https://docs.astral.sh/uv/), Node 22+, and a Mistral API key.

```bash
cp .env.example .env
docker compose up -d
cd backend && uv sync && uv run uvicorn app.main:app --reload
# another terminal
cd frontend && npm install && npm run dev
```

Set the values in `.env` in your shell or deployment environment. Do not commit it. `POST /api/demo/reset` deliberately fails per ordinary document if `MISTRAL_API_KEY` is absent: fixture extraction is never used as an ordinary fallback.

## Demo route

1. Open the catalog and select **Ingest** → **Reset demo dataset**.
2. Watch real document stages via the two-second `/api/jobs/{id}` poll.
3. Open a row to inspect field evidence rails and source disagreement.
4. Expand an unverified citation to compare the claimed snippet to nearest actual source text.
5. Open the provenance graph to follow Product → AttributeValue → SourceDocument links.

## Tests

```bash
cd backend && uv sync --group dev && uv run pytest
cd frontend && npm install && npm test
```

The backend suite verifies seed shape, the wrong-citation fixture, explicit conversions, contradiction/physics behavior, static LLM boundaries, and reduced candidate comparisons for 1,000 records.

## Deploy free

1. Create one AuraDB Free instance and retain its Bolt URI, username, and password.
2. Push this repository to GitHub.
3. In Render, create a Blueprint from the repository; it detects `render.yaml`.
4. Populate `NEO4J_*` and `MISTRAL_API_KEY` as Render secret environment variables.
5. Deploy, wait for `/health` to report Neo4j connectivity, then reset the demo dataset from the application.

Render’s free web service spins down after idle time, so allow a cold start before a demo. AuraDB and Render credentials are intentionally not included in this repository.
