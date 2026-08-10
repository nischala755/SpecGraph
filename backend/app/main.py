from __future__ import annotations
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from app.api.routes import router
from app.graph.repository import GraphRepository
from app.jobs.manager import JobManager
from app.pipeline.ingestion.service import IngestionService
from app.llm.mistral import MistralExtractionProvider
from app.llm.fixture import SeedFixtureExtractionProvider
from app.seed import load_seed_documents

def provider_for(document):
    if document.filename == 'bearing_uc206_wrong_citation_fixture_scraped_page.md': return SeedFixtureExtractionProvider()
    return MistralExtractionProvider()
@asynccontextmanager
async def lifespan(app):
    repo=GraphRepository(); app.state.startup_error=None
    try: repo.initialize()
    except Exception as error: app.state.startup_error=f"Neo4j initialization failed: {error}"
    app.state.repo=repo;app.state.seed_documents=load_seed_documents
    app.state.jobs=JobManager(IngestionService(repo,provider_for).process,repo);yield;repo.close()
app=FastAPI(title='SpecGraph Intelligence Engine',lifespan=lifespan);app.include_router(router)
@app.get('/health')
async def health():
    connected=app.state.repo.check();return JSONResponse({"status":"ok" if connected else "degraded","neo4j":"connected" if connected else "disconnected","mistral_configured":bool(os.getenv('MISTRAL_API_KEY'))},status_code=200 if connected else 503)
if os.path.isdir('static'): app.mount('/',StaticFiles(directory='static',html=True),name='static')
