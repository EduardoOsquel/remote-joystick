from __future__ import annotations

from remote_joystick.models.device import DeviceState
from remote_joystick.output.base import OutputDevice


class DebugOutputDevice(OutputDevice):
    def __init__(self) -> None:
        self.history: list[DeviceState] = []

    def write_state(self, state: DeviceState) -> None:
        self.history.append(state)

    def reset_to_safe_state(self, reason: str) -> None:
        self.history.append(DeviceState(logical_id="reset", physical_id="reset", name="reset", connected=False, channel=1))

    def close(self) -> None:
        self.history.clear()
