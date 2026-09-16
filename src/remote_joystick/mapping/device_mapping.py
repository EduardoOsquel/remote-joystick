from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class DeviceMapping:
    channel: int
    physical_device_id: str
    vjoy_device_id: int
    axes: list[dict[str, object]] = field(default_factory=list)
    buttons: list[dict[str, object]] = field(default_factory=list)
    povs: list[dict[str, object]] = field(default_factory=list)
