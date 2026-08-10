from __future__ import annotations
import asyncio, uuid
from app.domain.models import Job, JobDocument, SourceDocument

class JobManager:
    def __init__(self, processor, repository): self.processor=processor; self.repository=repository; self.jobs: dict[str,Job]={}
    def start(self, documents: list[SourceDocument]) -> Job:
        job=Job(str(uuid.uuid4()),[JobDocument(d.id,d.filename,d.source_type) for d in documents]);self.jobs[job.id]=job;self.repository.save_job(job);asyncio.create_task(self._run(job,documents));return job
    async def _run(self, job, documents):
        job.state="processing";self.repository.save_job(job)
        try:
            await self.processor(job,documents); job.state="completed" if all(d.stage=="completed" for d in job.documents) else "failed"
        except Exception as e: job.state="failed";job.error=str(e)
        finally: self.repository.save_job(job)
    def get(self, job_id: str) -> Job | None:
        if job_id in self.jobs: return self.jobs[job_id]
        job=self.repository.load_job(job_id)
        if job and job.state in {"pending","processing","retrying"}:
            job.state="failed"; job.error="Service restart interrupted this in-process job. Partial graph writes were retained; retry the ingestion."; self.repository.save_job(job)
        return job
