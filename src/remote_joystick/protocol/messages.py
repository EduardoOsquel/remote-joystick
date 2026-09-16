from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum


class PacketType(IntEnum):
    STATE = 1
    HEARTBEAT = 2
    DISCONNECT = 3
    SESSION = 4


@dataclass(slots=True)
class JoystickMessage:
    version: int
    message_type: PacketType
    session_id: int
    sender_id: int
    channel: int
    device_id: str
    sequence: int
    timestamp_ms: int
    axes: list[float] = field(default_factory=list)
    buttons: list[bool] = field(default_factory=list)
    povs: list[int] = field(default_factory=list)
    key: bytes | None = None
    signature: bytes | None = None
