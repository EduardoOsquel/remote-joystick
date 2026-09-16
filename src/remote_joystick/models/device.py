from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass(slots=True)
class DeviceIdentity:
    name: str
    persistent_id: str
    physical_id: str = ""
    channel: int = 1
    vendor_id: str | None = None
    product_id: str | None = None
    serial: str | None = None
    hid_path: str | None = None
    axis_count: int = 0
    button_count: int = 0
    pov_count: int = 0
    source: str = "unknown"


@dataclass(slots=True)
class AxisConfig:
    physical_axis: int = 0
    vjoy_axis: int = 0
    invert: bool = False
    dead_zone: float = 0.05
    min_dead_zone: float = 0.0
    max_dead_zone: float = 0.0
    saturation: float = 1.0
    curve: Literal["linear", "exponential"] = "linear"
    safe_value: float = 0.0


@dataclass(slots=True)
class ButtonMapping:
    physical_button: int = 0
    vjoy_button: int = 1


@dataclass(slots=True)
class PovMapping:
    physical_pov: int = 0
    vjoy_pov: int = 0
    safe_value: int = -1


@dataclass(slots=True)
class DeviceState:
    logical_id: str
    physical_id: str
    name: str
    sequence: int = 0
    timestamp_ms: int = 0
    axes: list[float] = field(default_factory=list)
    buttons: list[bool] = field(default_factory=list)
    povs: list[int] = field(default_factory=list)
    connected: bool = True
    channel: int = 1
