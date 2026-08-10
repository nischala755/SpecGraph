from pathlib import Path
from app.domain.models import SourceDocument

TIERS={'manufacturer_datasheet':1,'distributor_listing':2,'scraped_page':3}
def load_seed_documents() -> list[SourceDocument]:
    root=Path(__file__).resolve().parents[2]/'seed'; docs=[]
    for path in sorted(root.rglob('*.md')):
        source_type=next(x for x in TIERS if x in path.name)
        docs.append(SourceDocument(path.read_text(encoding='utf8'),path.name,source_type,TIERS[source_type]))
    return docs
