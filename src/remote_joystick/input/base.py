from __future__ import annotations

from abc import ABC, abstractmethod

from remote_joystick.models.device import DeviceIdentity
from remote_joystick.models.state import ConnectionState


class InputDevice(ABC):
    @abstractmethod
    def list_devices(self) -> list[DeviceIdentity]:
        raise NotImplementedError

    @abstractmethod
    def read_state(self, channel: int):
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        raise NotImplementedError

    @property
    @abstractmethod
    def connection_state(self) -> ConnectionState:
        raise NotImplementedError
