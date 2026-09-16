from __future__ import annotations

from abc import ABC, abstractmethod

from remote_joystick.models.device import DeviceState


class OutputDevice(ABC):
    @abstractmethod
    def write_state(self, state: DeviceState) -> None:
        raise NotImplementedError

    @abstractmethod
    def reset_to_safe_state(self, reason: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        raise NotImplementedError
