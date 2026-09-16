from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class JoystickMetrics:
    packets_per_second: float = 0.0
    packet_loss_estimate: float = 0.0
    last_packet_age_ms: float = 0.0
    jitter_ms: float = 0.0
    last_error: str = ""


@dataclass(slots=True)
class ConnectionState:
    connected: bool = False
    last_seen_ms: int = 0
    last_sequence: int = 0
    last_packet_age_ms: float = 0.0
    reset_reason: str = ""
    seen_packets: int = 0
    dropped_packets: int = 0


@dataclass(slots=True)
class RateWindow:
    values: list[float] = field(default_factory=list)

    def add(self, value: float) -> None:
        self.values.append(value)
        if len(self.values) > 32:
            self.values.pop(0)

    @property
    def average(self) -> float:
        if not self.values:
            return 0.0
        return sum(self.values) / len(self.values)


@dataclass(slots=True)
class SessionState:
    session_id: int = 0
    sender_id: int = 0
    channels: dict[int, Any] = field(default_factory=dict)
