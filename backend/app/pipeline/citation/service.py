from rapidfuzz import fuzz, process
from app.domain.models import ExtractedAttribute

def verify(attribute: ExtractedAttribute, chunks: list[str]) -> ExtractedAttribute:
    match = process.extractOne(attribute.citation_span, chunks, scorer=fuzz.token_sort_ratio)
    score, context = (float(match[1]), match[0]) if match else (0.0, "")
    attribute.verification_score, attribute.citation_verified, attribute.source_context = score, score >= 90, context
    return attribute
