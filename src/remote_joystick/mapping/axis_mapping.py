from __future__ import annotations


def clamp(value: float, minimum: float = -1.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


def normalize_axis(raw: float, invert: bool = False, dead_zone: float = 0.05, saturation: float = 1.0) -> float:
    value = float(raw)
    if value > -dead_zone and value < dead_zone:
        value = 0.0
    if invert:
        value = -value
    value = clamp(value * saturation, -1.0, 1.0)
    return value


def axis_to_vjoy(value: float) -> float:
    return clamp(value, -1.0, 1.0)
