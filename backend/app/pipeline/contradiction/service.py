from __future__ import annotations
import re
from itertools import combinations
from app.domain.models import ExtractedAttribute, CONTROLLED_FIELDS

def _string(v: object) -> str: return re.sub(r"[\W_]", "", str(v).lower())
def contradictions(attributes: list[ExtractedAttribute], tiers: dict[str, int]) -> list[dict]:
    grouped: dict[str, list[ExtractedAttribute]] = {}
    for attr in attributes:
        if attr.field_name in CONTROLLED_FIELDS and (attr.field_name in {"mpn", "material", "category"} or isinstance(attr.value, (float, int))):
            grouped.setdefault(attr.field_name, []).append(attr)
    found = []
    for field, values in grouped.items():
        for a, b in combinations(values, 2):
            if isinstance(a.value, (float, int)) and isinstance(b.value, (float, int)):
                equivalent = abs(a.value-b.value) / max(abs(a.value), abs(b.value), 0.00001) <= .02
            else: equivalent = _string(a.value) == _string(b.value)
            if not equivalent:
                preferred, other = sorted((a,b), key=lambda x: tiers.get(x.source_id, 3))
                found.append({"field_name": field, "left": a.id, "right": b.id, "resolution_status": "preferred_by_reliability", "preferred": preferred.id, "reason": f"Source tier {tiers.get(preferred.source_id, 3)} preferred over tier {tiers.get(other.source_id, 3)}"})
    return found
