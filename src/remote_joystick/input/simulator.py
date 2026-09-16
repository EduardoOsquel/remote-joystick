from __future__ import annotations

import math
import time
from dataclasses import dataclass

from remote_joystick.input.base import InputDevice
from remote_joystick.models.device import DeviceIdentity
from remote_joystick.models.state import ConnectionState


@dataclass(slots=True)
class SimulatedDeviceState:
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


class SimulatedJoystick:
    def __init__(self, channel: int, name: str, axes: int = 4, buttons: int = 12, povs: int = 2) -> None:
        self.channel = channel
        self.name = name
        self.physical_id = f"sim-device-{channel}"
        self.axes = axes
        self.buttons = buttons
        self.povs = povs
        self.sequence = 0
        self._tick = 0

    def read_state(self) -> SimulatedDeviceState:
        self._tick += 1
        self.sequence += 1
        ts = int(time.time() * 1000)
        phase = self._tick / 20.0
        axes = [
            round(math.sin(phase + idx) * 0.9, 4)
            for idx in range(self.axes)
        ]
        buttons = [bool((self._tick + idx) % 3 == 0) for idx in range(self.buttons)]
        povs = [int((self._tick * 2250) % 36000) for _ in range(self.povs)]
        return SimulatedDeviceState(
            logical_id=f"sim-{self.channel}",
            physical_id=f"sim-device-{self.channel}",
            name=self.name,
            sequence=self.sequence,
            timestamp_ms=ts,
            axes=axes,
            buttons=buttons,
            povs=povs,
            connected=True,
            channel=self.channel,
        )


class SimulatorInputDevice(InputDevice):
    def __init__(self, device_count: int = 2) -> None:
        self._devices = [
            SimulatedJoystick(channel=idx + 1, name=f"Simulated Joystick {idx + 1}")
            for idx in range(device_count)
        ]

    def list_devices(self) -> list[DeviceIdentity]:
        return [
            DeviceIdentity(
                name=device.name,
                persistent_id=device.physical_id,
                physical_id=device.physical_id,
                channel=device.channel,
                vendor_id="SIM",
                product_id="SIM",
                serial=f"sim-{device.channel}",
                hid_path=f"/sim/{device.channel}",
                axis_count=device.axes,
                button_count=device.buttons,
                pov_count=device.povs,
                source="simulator",
            )
            for device in self._devices
        ]

    def read_state(self, channel: int):
        for device in self._devices:
            if device.channel == channel:
                return device.read_state()
        raise ValueError(f"Channel {channel} not found in simulator")

    @property
    def connection_state(self) -> ConnectionState:
        return ConnectionState(connected=True, last_seen_ms=int(time.time() * 1000))

    def close(self) -> None:
        self._devices.clear()
