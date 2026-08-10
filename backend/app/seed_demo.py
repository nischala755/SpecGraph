"""Run the full, real pipeline once against the configured graph database.

Designed for precomputing the AuraDB-backed read-only demo on a machine with
enough RAM for local MiniLM inference. Credentials are read only from env vars.
"""
from __future__ import annotations
import asyncio
import uuid
from app.domain.models import Job, JobDocument
from app.graph.repository import GraphRepository
from app.llm.fixture import SeedFixtureExtractionProvider
from app.llm.mistral import MistralExtractionProvider
from app.pipeline.ingestion.service import IngestionService
from app.seed import load_seed_documents

def provider_for(document):
    if document.filename == "bearing_uc206_wrong_citation_fixture_scraped_page.md": return SeedFixtureExtractionProvider()
    return MistralExtractionProvider()

async def main():
    repo=GraphRepository(); repo.initialize(); docs=load_seed_documents(); repo.clear()
    job=Job(str(uuid.uuid4()),[JobDocument(d.id,d.filename,d.source_type) for d in docs],state="processing")
    repo.save_job(job)
    try:
        await IngestionService(repo,provider_for).process(job,docs)
        job.state="completed" if all(d.stage=="completed" for d in job.documents) else "failed"
    except Exception as error:
        job.state="failed"; job.error=str(error)
    finally:
        repo.save_job(job); repo.close()
    print(f"seed job {job.id}: {job.state}")
    if job.error: print(job.error)

if __name__ == "__main__": asyncio.run(main())
