from __future__ import annotations

from dataclasses import dataclass, field, asdict
from hashlib import sha256
from typing import Any, Literal

SourceType = Literal["manufacturer_datasheet", "distributor_listing", "scraped_page"]
Stage = Literal["queued", "extracting", "verifying_citations", "resolving_entities", "adjudicating_contradictions", "validating", "completed", "failed"]

CONTROLLED_FIELDS = {"voltage", "current", "power", "resistance", "bore_diameter", "outer_diameter", "length", "total_length", "material", "density", "melting_point", "mpn", "product_name", "category"}

@dataclass
class SourceDocument:
    raw_text: str
    filename: str
    source_type: SourceType
    reliability_tier: int
    id: str = ""
    def __post_init__(self):
        self.id = self.id or sha256(self.raw_text.encode()).hexdigest()

@dataclass
class ExtractedAttribute:
    field_name: str
    value: float | str
    unit: str | None
    citation_span: str
    source_id: str = ""
    citation_verified: bool = False
    verification_score: float = 0.0
    source_context: str = ""
    plausibility_status: str = "unchecked"
    plausibility_reason: str = "Not evaluated yet"
    extraction_confidence: float = 1.0
    id: str = ""
    def __post_init__(self):
        if not self.id:
            signature = f"{self.source_id}|{self.field_name}|{self.value}|{self.unit}|{self.citation_span}"
            self.id = sha256(signature.encode()).hexdigest()

@dataclass
class Candidate:
    document: SourceDocument
    product_name: str
    category: str
    mpn: str | None
    attributes: list[ExtractedAttribute]

@dataclass
class Product:
    id: str
    resolved_name: str
    category: str
    mpn: str | None
    cluster_confidence: float
    documents: list[SourceDocument] = field(default_factory=list)
    attributes: list[ExtractedAttribute] = field(default_factory=list)
    contradictions: list[dict[str, Any]] = field(default_factory=list)
    def summary(self) -> dict[str, Any]:
        return {"id": self.id, "resolved_name": self.resolved_name, "category": self.category, "mpn": self.mpn, "cluster_confidence": self.cluster_confidence, "sources": len(self.documents), "contradictions": len(self.contradictions), "implausible": any(a.plausibility_status == "implausible" for a in self.attributes), "unverified": any(not a.citation_verified for a in self.attributes)}

@dataclass
class JobDocument:
    document_id: str
    filename: str
    source_type: str
    stage: Stage = "queued"
    error: str | None = None
    retries: int = 0

@dataclass
class Job:
    id: str
    documents: list[JobDocument]
    state: Literal["pending", "processing", "retrying", "completed", "failed"] = "pending"
    error: str | None = None
    def payload(self) -> dict[str, Any]: return asdict(self)
