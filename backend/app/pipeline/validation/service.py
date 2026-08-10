from __future__ import annotations
from app.domain.models import ExtractedAttribute

MATERIALS = {"steel": (7600, 8050, 1370, 1530), "stainless steel": (7700, 8050, 1375, 1530), "aluminum": (2600, 2800, 630, 700), "brass": (8400, 8800, 900, 950), "copper": (8700, 9000, 1060, 1100), "cast iron": (6800, 7800, 1120, 1200), "titanium": (4400, 4600, 1650, 1700), "nylon": (1100, 1200, 190, 270), "ptfe": (2100, 2300, 320, 340), "zinc": (7000, 7200, 410, 430)}
def validate(attributes: list[ExtractedAttribute]) -> None:
    by = {a.field_name: a for a in attributes if isinstance(a.value, (float,int))}
    def fail(fields, reason):
        for f in fields:
            if f in by: by[f].plausibility_status, by[f].plausibility_reason = "implausible", reason
    for a in attributes:
        if a.plausibility_status == "unchecked": a.plausibility_status, a.plausibility_reason = "plausible", "No applicable validation rule failed"
    if all(x in by for x in ("voltage", "current", "power")):
        expected = by["voltage"].value * by["current"].value
        if abs(by["power"].value - expected) / max(expected, .001) > .05: fail(("voltage","current","power"), f"P=VI mismatch: expected {expected:g} W")
    if all(x in by for x in ("voltage", "current", "resistance")):
        expected = by["current"].value * by["resistance"].value
        if abs(by["voltage"].value - expected) / max(expected,.001) > .05: fail(("voltage","current","resistance"), f"V=IR mismatch: expected {expected:g} V")
    if "bore_diameter" in by and "outer_diameter" in by and by["bore_diameter"].value >= by["outer_diameter"].value: fail(("bore_diameter","outer_diameter"), "Bore diameter must be less than outer diameter")
    for name in ("length", "total_length"):
        if name in by and by[name].value <= 0: fail((name,), f"{name.replace('_',' ')} must be positive")
    if "length" in by and "total_length" in by and by["total_length"].value < by["length"].value: fail(("length","total_length"), "Total length must be at least length")
