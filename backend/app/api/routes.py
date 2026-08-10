from __future__ import annotations
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from app.domain.models import SourceDocument
router=APIRouter(prefix="/api")
class InputDocument(BaseModel): raw_text:str;filename:str;source_type:str;reliability_tier:int
class IngestRequest(BaseModel): documents:list[InputDocument]
@router.post('/ingest')
async def ingest(body: IngestRequest, request: Request):
    docs=[SourceDocument(**d.model_dump()) for d in body.documents]; return request.app.state.jobs.start(docs).payload()
@router.get('/jobs/{job_id}')
async def job(job_id:str,request:Request):
    result=request.app.state.jobs.get(job_id)
    if not result: raise HTTPException(404,'Job not found')
    return result.payload()
@router.get('/products')
async def products(request:Request,q:str|None=None):
    try:return request.app.state.repo.products(q)
    except Exception as e:raise HTTPException(503,f'Graph query failed: {e}')
@router.get('/products/{product_id}')
async def product(product_id:str,request:Request):
    result=request.app.state.repo.product(product_id)
    if not result: raise HTTPException(404,'Product not found')
    return result
@router.get('/products/{product_id}/graph')
async def graph(product_id:str,request:Request): return request.app.state.repo.graph(product_id)
@router.post('/demo/reset')
async def reset(request:Request):
    if request.app.state.read_only_demo:
        raise HTTPException(409,'This hosted demo serves a precomputed, provenance-verified dataset. Reset is disabled to protect the free deployment; run ingestion locally to refresh it.')
    try: request.app.state.repo.clear(); docs=request.app.state.seed_documents(); return request.app.state.jobs.start(docs).payload()
    except Exception as e:raise HTTPException(503,f'Demo reset failed: {e}')
