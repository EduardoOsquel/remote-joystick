from __future__ import annotations

import ctypes
import platform
import time
from dataclasses import dataclass

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


class _JOYINFOEX(ctypes.Structure):
    _fields_ = [
        ("dwSize", ctypes.c_uint),
        ("dwFlags", ctypes.c_uint),
        ("dwXpos", ctypes.c_uint),
        ("dwYpos", ctypes.c_uint),
        ("dwZpos", ctypes.c_uint),
        ("dwRpos", ctypes.c_uint),
        ("dwUpos", ctypes.c_uint),
        ("dwVpos", ctypes.c_uint),
        ("dwButtons", ctypes.c_uint),
        ("dwButtonNumber", ctypes.c_uint),
        ("dwPOV", ctypes.c_uint),
        ("dwReserved1", ctypes.c_uint),
        ("dwReserved2", ctypes.c_uint),
    ]


class _JOYCAPS(ctypes.Structure):
    _fields_ = [
        ("wMid", ctypes.c_ushort),
        ("wPid", ctypes.c_ushort),
        ("szPname", ctypes.c_wchar * 32),
        ("wXmin", ctypes.c_uint),
        ("wXmax", ctypes.c_uint),
        ("wYmin", ctypes.c_uint),
        ("wYmax", ctypes.c_uint),
        ("wZmin", ctypes.c_uint),
        ("wZmax", ctypes.c_uint),
        ("wNumButtons", ctypes.c_uint),
        ("wPeriodMin", ctypes.c_uint),
        ("wPeriodMax", ctypes.c_uint),
        ("wRmin", ctypes.c_uint),
        ("wRmax", ctypes.c_uint),
        ("wUmin", ctypes.c_uint),
        ("wUmax", ctypes.c_uint),
        ("wVmin", ctypes.c_uint),
        ("wVmax", ctypes.c_uint),
        ("wCaps", ctypes.c_uint),
        ("wMaxAxes", ctypes.c_uint),
        ("wNumAxes", ctypes.c_uint),
        ("wMaxButtons", ctypes.c_uint),
        ("szRegKey", ctypes.c_wchar * 32),
        ("szOEMVxD", ctypes.c_wchar * 260),
    ]


class WindowsJoystickInputDevice(InputDevice):
    """Real Windows HID joystick adapter using the WinMM API."""

    def __init__(self) -> None:
        self._devices: list[DeviceIdentity] = []
        self._winmm = None
        self._discover_devices()

    def _normalize_axis(self, value: int, minimum: int, maximum: int) -> float:
        if maximum <= minimum:
            return 0.0
        span = maximum - minimum
        if span == 0:
            return 0.0
        normalized = (value - minimum) / span
        return min(1.0, max(-1.0, (normalized * 2.0) - 1.0))

    def _discover_devices(self) -> None:
        if platform.system() != "Windows":
            self._devices = []
            return

        try:
            self._winmm = ctypes.WinDLL("winmm.dll")
            self._winmm.joyGetNumDevs.restype = ctypes.c_uint
            count = int(self._winmm.joyGetNumDevs())
        except (AttributeError, OSError):
            self._devices = []
            self._winmm = None
            return

        devices: list[DeviceIdentity] = []
        for index in range(count):
            caps = _JOYCAPS()
            result = self._winmm.joyGetDevCapsW(index, ctypes.byref(caps), ctypes.sizeof(caps))
            if result != 0:
                continue
            name = (caps.szPname or f"Joystick {index + 1}").strip()
            if not name:
                name = f"Joystick {index + 1}"
            devices.append(
                DeviceIdentity(
                    name=name,
                    persistent_id=f"windows:{index}",
                    physical_id=f"windows:{index}",
                    channel=index + 1,
                    vendor_id=str(caps.wMid),
                    product_id=str(caps.wPid),
                    axis_count=int(getattr(caps, "wNumAxes", 0)),
                    button_count=int(getattr(caps, "wNumButtons", 0)),
                    pov_count=1,
                    source="windows",
                )
            )
        self._devices = devices

    def list_devices(self) -> list[DeviceIdentity]:
        return list(self._devices)

    def read_state(self, channel: int):
        if self._winmm is None:
            raise ValueError("Windows joystick input is unavailable on this platform")

        for device in self._devices:
            if device.channel != channel:
                continue
            caps = _JOYCAPS()
            rc = self._winmm.joyGetDevCapsW(channel - 1, ctypes.byref(caps), ctypes.sizeof(caps))
            if rc != 0:
                raise ValueError(f"Unable to query joystick {channel}")

            state = _JOYINFOEX()
            state.dwSize = ctypes.sizeof(state)
            state.dwFlags = 0xFF
            rc = self._winmm.joyGetPosEx(channel - 1, ctypes.byref(state))
            if rc != 0:
                raise ValueError(f"Unable to read joystick state for channel {channel}")

            axes = [
                self._normalize_axis(state.dwXpos, caps.wXmin, caps.wXmax),
                self._normalize_axis(state.dwYpos, caps.wYmin, caps.wYmax),
                self._normalize_axis(state.dwZpos, caps.wZmin, caps.wZmax),
                self._normalize_axis(state.dwRpos, caps.wRmin, caps.wRmax),
                self._normalize_axis(state.dwUpos, caps.wUmin, caps.wUmax),
                self._normalize_axis(state.dwVpos, caps.wVmin, caps.wVmax),
            ]
            button_count = max(device.button_count, 1)
            buttons = [bool((state.dwButtons >> idx) & 1) for idx in range(button_count)]
            pov = [-1]
            if state.dwPOV != 0xFFFF:
                pov = [int(state.dwPOV)]
            return WindowsJoystickState(
                logical_id=device.physical_id,
                physical_id=device.physical_id,
                name=device.name,
                sequence=int(time.time() * 1000),
                timestamp_ms=int(time.time() * 1000),
                axes=[axis for axis in axes[: max(device.axis_count, 1)]],
                buttons=buttons,
                povs=pov,
                connected=True,
                channel=device.channel,
            )
        raise ValueError(f"Channel {channel} not found in Windows joystick input")

    @property
    def connection_state(self) -> ConnectionState:
        return ConnectionState(connected=bool(self._devices), last_seen_ms=int(time.time() * 1000))

    def close(self) -> None:
        self._devices.clear()
        self._winmm = None
