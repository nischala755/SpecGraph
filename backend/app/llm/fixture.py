from app.domain.models import SourceDocument, Candidate, ExtractedAttribute
class SeedFixtureExtractionProvider:
    """Test-only provider; permitted for the deliberately wrong-citation fixture."""
    async def extract(self, document: SourceDocument) -> Candidate:
        lines=dict(line.split(":",1) for line in document.raw_text.splitlines() if ":" in line)
        attrs=[]
        for key, field, unit in [("Voltage","voltage","V"),("Current","current","A"),("Power","power","W"),("Bore","bore_diameter","mm"),("Outer","outer_diameter","mm"),("Length","length","mm"),("Total Length","total_length","mm"),("Material","material",None)]:
            if key in lines:
                raw=lines[key].strip(); bits=raw.split(); value=float(bits[0]) if bits and bits[0].replace('.','',1).isdigit() else raw
                attrs.append(ExtractedAttribute(field,value,unit, f"{key}: {raw}",document.id))
        if "wrong_citation_fixture" in document.filename and attrs: attrs[0].citation_span="Bore: 999 mm"
        return Candidate(document, lines.get("Product",document.filename).strip(), lines.get("Category","unknown").strip(), lines.get("MPN",None),attrs)
