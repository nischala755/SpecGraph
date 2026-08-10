from __future__ import annotations
import asyncio, uuid
from app.domain.models import Job, JobDocument, SourceDocument

class JobManager:
    def __init__(self, processor): self.processor=processor; self.jobs: dict[str,Job]={}
    def start(self, documents: list[SourceDocument]) -> Job:
        job=Job(str(uuid.uuid4()),[JobDocument(d.id,d.filename,d.source_type) for d in documents]);self.jobs[job.id]=job; asyncio.create_task(self._run(job,documents));return job
    async def _run(self, job, documents):
        job.state="processing"
        try:
            await self.processor(job,documents); job.state="completed" if all(d.stage=="completed" for d in job.documents) else "failed"
        except Exception as e: job.state="failed";job.error=str(e)
    def get(self, job_id: str) -> Job | None: return self.jobs.get(job_id)
