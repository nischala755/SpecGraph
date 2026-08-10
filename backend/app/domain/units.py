from __future__ import annotations
import re

CONVERSIONS = {
    "length": {"mm": (1, "mm"), "cm": (10, "mm"), "m": (1000, "mm"), "in": (25.4, "mm"), "inch": (25.4, "mm")},
    "total_length": {"mm": (1, "mm"), "cm": (10, "mm"), "m": (1000, "mm"), "in": (25.4, "mm")},
    "bore_diameter": {"mm": (1, "mm"), "cm": (10, "mm"), "in": (25.4, "mm")},
    "outer_diameter": {"mm": (1, "mm"), "cm": (10, "mm"), "in": (25.4, "mm")},
    "power": {"w": (1, "W"), "kw": (1000, "W")}, "voltage": {"v": (1, "V"), "kv": (1000, "V")},
    "current": {"a": (1, "A"), "ma": (.001, "A")}, "resistance": {"ohm": (1, "ohm"), "ω": (1, "ohm"), "kohm": (1000, "ohm")},
    "density": {"kg/m3": (1, "kg/m³"), "kg/m³": (1, "kg/m³"), "g/cm3": (1000, "kg/m³"), "g/cm³": (1000, "kg/m³")},
    "melting_point": {"c": (1, "°C"), "°c": (1, "°C")},
}

def normalize(field: str, value: float | str, unit: str | None) -> tuple[float | str, str | None, str | None]:
    if isinstance(value, str) and field in CONVERSIONS and re.fullmatch(r"[-+]?\d+(?:\.\d+)?", value.strip()):
        value=float(value)
    if not isinstance(value, (float, int)) or field not in CONVERSIONS: return value, unit, None
    key = (unit or "").strip().lower().replace("³", "3")
    conversion = CONVERSIONS[field].get(key)
    if not conversion: return value, unit, "unit mismatch for field type"
    return float(value) * conversion[0], conversion[1], None
