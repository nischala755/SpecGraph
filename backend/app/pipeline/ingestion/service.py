from __future__ import annotations
import asyncio, hashlib
from app.domain.models import SourceDocument, Product
from app.domain.units import normalize
from app.pipeline.citation.service import verify
from app.pipeline.entity_resolution.service import clusters
from app.pipeline.contradiction.service import contradictions
from app.pipeline.validation.service import validate
from app.llm.fixture import SeedFixtureExtractionProvider

class IngestionService:
    def __init__(self, repository, provider_factory): self.repository,self.provider_factory=repository,provider_factory;self.last_candidate_pairs=0
    def _persist(self, job): self.repository.save_job(job)
    async def process(self, job, docs: list[SourceDocument]):
        candidates=[]
        for record, document in zip(job.documents,docs):
            try:
                record.stage="extracting"; self._persist(job); candidate=await self.provider_factory(document).extract(document)
                record.stage="verifying_citations"; self._persist(job)
                chunks=[document.raw_text[i:i+3000] for i in range(0,len(document.raw_text),3000)]
                for attr in candidate.attributes:
                    verify(attr,chunks); attr.value,attr.unit,unit_error=normalize(attr.field_name,attr.value,attr.unit)
                    if unit_error: attr.plausibility_status,attr.plausibility_reason="implausible",unit_error
                candidates.append(candidate)
            except Exception as e:
                transient=isinstance(e,(TimeoutError,ConnectionError)) or "429" in str(e)
                for attempt in range(3 if transient else 0):
                    record.retries=attempt+1;job.state="retrying";self._persist(job);await asyncio.sleep(2**attempt)
                    try: candidate=await self.provider_factory(document).extract(document); candidates.append(candidate);break
                    except Exception as retry_error: e=retry_error
                else: record.stage="failed";record.error=str(e);self._persist(job)
        for r in job.documents:
            if r.stage not in ("failed",): r.stage="resolving_entities"
        self._persist(job)
        grouped,self.last_candidate_pairs=await asyncio.to_thread(clusters,candidates)
        for cluster in grouped:
            group=[candidates[i] for i in cluster]; source_ids=sorted(c.document.id for c in group); pid=hashlib.sha256('|'.join(source_ids).encode()).hexdigest()
            attrs=[a for c in group for a in c.attributes]; tiers={c.document.id:c.document.reliability_tier for c in group}
            for r in job.documents:
                if r.document_id in source_ids:r.stage="adjudicating_contradictions"
            self._persist(job)
            conflicts=contradictions(attrs,tiers)
            for r in job.documents:
                if r.document_id in source_ids:r.stage="validating"
            self._persist(job)
            validate(attrs)
            product=Product(pid,group[0].product_name,group[0].category,group[0].mpn,1.0 if len(group)==1 else .9,[c.document for c in group],attrs,conflicts);self.repository.save_product(product)
            for r in job.documents:
                if r.document_id in source_ids:r.stage="completed"
            self._persist(job)
