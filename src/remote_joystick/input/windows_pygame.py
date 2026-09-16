from __future__ import annotations

import platform
import time
from dataclasses import dataclass

import pygame

from remote_joystick.input.base import InputDevice
from remote_joystick.models.device import DeviceIdentity
from remote_joystick.models.state import ConnectionState


@dataclass(slots=True)
class WindowsJoystickState:
    logical_id: str
    physical_id: str
    name: str
    sequence: int
    timestamp_ms: int
    axes: list[float]
    buttons: list[bool]
    povs: list[int]
    connected: bool
    channel: int


class WindowsJoystickInputDevice(InputDevice):
    """Windows joystick adapter based on pygame gamepad support."""

    @staticmethod
    def _deduplicate_devices(devices: list[DeviceIdentity]) -> list[DeviceIdentity]:
        return list(devices)

    def __init__(self) -> None:
        self._devices: list[DeviceIdentity] = []
        self._joysticks: list[pygame.joystick.Joystick] = []
        self._discover_devices()

    def _normalize_axis(self, value: float) -> float:
        return max(-1.0, min(1.0, float(value)))

    def _discover_devices(self) -> None:
        if platform.system() != "Windows":
            self._devices = []
            self._joysticks = []
            return

        try:
            pygame.init()
            pygame.joystick.init()
        except Exception:
            self._devices = []
            self._joysticks = []
            return

        count = pygame.joystick.get_count()
        devices: list[DeviceIdentity] = []
        for index in range(count):
            joy = pygame.joystick.Joystick(index)
            joy.init()
            devices.append(
                DeviceIdentity(
                    name=joy.get_name() or f"Joystick {index + 1}",
                    persistent_id=f"windows:{index}",
                    physical_id=f"windows:{index}",
                    channel=index + 1,
                    vendor_id=str(index),
                    product_id=str(index),
                    axis_count=int(joy.get_numaxes()),
                    button_count=int(joy.get_numbuttons()),
                    pov_count=int(joy.get_numhats()),
                    source="windows",
                )
            )
            self._joysticks.append(joy)

        self._devices = self._deduplicate_devices(devices)

    def list_devices(self) -> list[DeviceIdentity]:
        return list(self._devices)

    def read_state(self, channel: int):
        if not self._devices:
            raise ValueError("Windows joystick input is unavailable on this platform")

        index = channel - 1
        if index < 0 or index >= len(self._joysticks):
            raise ValueError(f"Channel {channel} not found in Windows joystick input")

        joy = self._joysticks[index]
        pygame.event.pump()
        axes = [self._normalize_axis(joy.get_axis(axis)) for axis in range(joy.get_numaxes())]
        buttons = [bool(joy.get_button(button)) for button in range(joy.get_numbuttons())]
        povs: list[int] = []
        for hat_index in range(joy.get_numhats()):
            hat = joy.get_hat(hat_index)
            x, y = hat
            if x == 0 and y == 0:
                povs.append(-1)
            elif x == 0 and y == -1:
                povs.append(0)
            elif x == 1 and y == -1:
                povs.append(4500)
            elif x == 1 and y == 0:
                povs.append(9000)
            elif x == 1 and y == 1:
                povs.append(13500)
            elif x == 0 and y == 1:
                povs.append(18000)
            elif x == -1 and y == 1:
                povs.append(22500)
            elif x == -1 and y == 0:
                povs.append(27000)
            elif x == -1 and y == -1:
                povs.append(31500)
            else:
                povs.append(-1)

        sequence = int(time.time_ns() % (2**32))
        device = self._devices[index]
        return WindowsJoystickState(
            logical_id=device.physical_id,
            physical_id=device.physical_id,
            name=device.name,
            sequence=sequence,
            timestamp_ms=int(time.time() * 1000),
            axes=axes,
            buttons=buttons,
            povs=povs or [-1],
            connected=True,
            channel=device.channel,
        )

    @property
    def connection_state(self) -> ConnectionState:
        return ConnectionState(connected=bool(self._devices), last_seen_ms=int(time.time() * 1000))

    def close(self) -> None:
        for joy in self._joysticks:
            try:
                joy.quit()
            except Exception:
                pass
        self._devices.clear()
        self._joysticks.clear()
        try:
            pygame.joystick.quit()
        except Exception:
            pass
