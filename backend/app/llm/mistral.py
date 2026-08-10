from __future__ import annotations
import os, json, httpx
from app.domain.models import SourceDocument, Candidate, ExtractedAttribute

SCHEMA = '{"product_name":"string","category":"string","mpn":"string or null","attributes":[{"field_name":"controlled vocabulary value","value":"number|string","unit":"string or null, raw pre-normalization","citation_span":"exact substring copied from the source chunk"}]}'
class MistralExtractionProvider:
    def __init__(self):
        self.key=os.getenv("MISTRAL_API_KEY"); self.model=os.getenv("MISTRAL_MODEL", "mistral-small-latest")
        if not self.key: raise RuntimeError("MISTRAL_API_KEY is required for ordinary document ingestion")
    async def extract(self, document: SourceDocument) -> Candidate:
        chunks=[document.raw_text[i:i+3000] for i in range(0,len(document.raw_text),3000)]
        extracted=[]; name=category=None; mpn=None
        async with httpx.AsyncClient(timeout=45) as client:
            for chunk in chunks:
                payload={"model":self.model,"temperature":0,"response_format":{"type":"json_object"},"messages":[{"role":"system","content":"Extract product claims. Return only JSON schema: "+SCHEMA},{"role":"user","content":chunk}]}
                r=await client.post("https://api.mistral.ai/v1/chat/completions", headers={"Authorization":f"Bearer {self.key}"}, json=payload); r.raise_for_status(); data=json.loads(r.json()["choices"][0]["message"]["content"])
                name=name or data["product_name"]; category=category or data["category"]; mpn=mpn or data.get("mpn")
                extracted.extend(ExtractedAttribute(source_id=document.id, **a) for a in data.get("attributes",[]))
        return Candidate(document, name or "Unknown", category or "Uncategorized", mpn, extracted)
