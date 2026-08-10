from typing import Protocol
from app.domain.models import SourceDocument, Candidate
class ExtractionProvider(Protocol):
    async def extract(self, document: SourceDocument) -> Candidate: ...
