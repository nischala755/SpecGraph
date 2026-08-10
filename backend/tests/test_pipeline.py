from pathlib import Path
from app.domain.models import Candidate, ExtractedAttribute, SourceDocument
from app.domain.units import normalize
from app.pipeline.citation.service import verify
from app.pipeline.contradiction.service import contradictions
from app.pipeline.entity_resolution.service import clusters, mpn_similarity
from app.pipeline.validation.service import validate
from app.seed import load_seed_documents
from app.llm.fixture import SeedFixtureExtractionProvider
from app.check_boundaries import test_boundaries

def test_seed_dataset_has_exact_source_shape():
    docs=load_seed_documents()
    assert len(docs)==54
    assert {d.source_type for d in docs}=={'manufacturer_datasheet','distributor_listing','scraped_page'}
    assert all(d.filename and d.id for d in docs)

def test_wrong_fixture_citation_is_unverified():
    doc=next(d for d in load_seed_documents() if 'wrong_citation_fixture' in d.filename)
    candidate=__import__('asyncio').run(SeedFixtureExtractionProvider().extract(doc))
    a=verify(candidate.attributes[0],[doc.raw_text])
    assert a.citation_verified is False and a.verification_score<90

def test_units_contradiction_and_physics_are_deterministic():
    assert normalize('length',1,'in')==(25.4,'mm',None)
    assert normalize('power',1,'V')[2]=='unit mismatch for field type'
    source=SourceDocument('x','x.md','manufacturer_datasheet',1)
    a=ExtractedAttribute('power',60,'W','Power: 60 W',source.id);v=ExtractedAttribute('voltage',24,'V','Voltage: 24 V',source.id);i=ExtractedAttribute('current',2,'A','Current: 2 A',source.id)
    validate([a,v,i]);assert a.plausibility_status=='implausible' and 'P=VI' in a.plausibility_reason
    b=ExtractedAttribute('outer_diameter',54,'mm','Outer: 54 mm','two');c=ExtractedAttribute('outer_diameter',52,'mm','Outer: 52 mm',source.id)
    assert len(contradictions([b,c],{'two':2,source.id:1}))==1

def test_lsh_reduces_comparisons_for_large_catalog():
    docs=[SourceDocument(str(i),f'{i}.md','scraped_page',3) for i in range(1000)]
    records=[Candidate(d,f'Product-{i:04d}','bearing',f'MPN-{i:04d}',[]) for i,d in enumerate(docs)]
    _, compared=clusters(records, embedding_similarity=lambda i,j: 1.0 if i==j else 0.0)
    assert compared < 1000*999//2
    test_boundaries()

def test_mpn_series_numbers_do_not_overcluster():
    assert mpn_similarity('UC201','UC202') == 0
    assert mpn_similarity('K20-024','000K20 024') == 1
