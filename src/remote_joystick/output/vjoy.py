from __future__ import annotations

import ctypes
import os
from typing import Any

from remote_joystick.models.device import DeviceState
from remote_joystick.output.base import OutputDevice


VJOY_AXIS_X = 0x30
VJOY_AXIS_Y = 0x31
VJOY_AXIS_Z = 0x32
VJOY_AXIS_RX = 0x33
VJOY_AXIS_RY = 0x34
VJOY_AXIS_RZ = 0x35
VJOY_AXIS_SL0 = 0x36
VJOY_AXIS_SL1 = 0x37


class VJoyBackend:
    """Real vJoy backend binding for the receiver side."""

    def __init__(self, device_id: int = 1) -> None:
        self.device_id = device_id
        self._lib: Any | None = None
        self._acquired = False
        self._load_library()

    def _load_library(self) -> None:
        if os.name != "nt":
            self._lib = None
            return

        candidate_paths = [
            r"C:\vJoy\vJoyInterface.dll",
            r"C:\Program Files\vJoy\vJoyInterface.dll",
            r"C:\Program Files (x86)\vJoy\vJoyInterface.dll",
        ]
        for path in candidate_paths:
            if not os.path.exists(path):
                continue
            try:
                lib = ctypes.WinDLL(path)
                lib.GetNumberOfVJD.restype = ctypes.c_int
                lib.AcquireVJD.restype = ctypes.c_int
                lib.ReleaseVJD.restype = ctypes.c_int
                lib.SetAxis.restype = ctypes.c_int
                lib.SetBtn.restype = ctypes.c_int
                lib.SetDiscPov.restype = ctypes.c_int
                lib.ResetVJD.restype = ctypes.c_int
                self._lib = lib
                return
            except (AttributeError, OSError):
                self._lib = None
                return
        self._lib = None

    def _ensure_acquired(self) -> bool:
        if self._lib is None:
            return False
        if self._acquired:
            return True
        try:
            result = self._lib.AcquireVJD(self.device_id)
            self._acquired = result == 1
            return self._acquired
        except (AttributeError, ValueError):
            return False

    def _axis_value(self, value: float) -> int:
        scaled = int(round((value + 1.0) * 32767.5))
        return max(0, min(65535, scaled))

    def write_state(self, state: DeviceState) -> None:
        if self._lib is None:
            return
        if not self._ensure_acquired():
            return

        axis_ids = [VJOY_AXIS_X, VJOY_AXIS_Y, VJOY_AXIS_Z, VJOY_AXIS_RX, VJOY_AXIS_RY, VJOY_AXIS_RZ]
        for axis_index, axis_value in enumerate(state.axes[: len(axis_ids)]):
            axis_id = axis_ids[axis_index]
            self._lib.SetAxis(self._axis_value(float(axis_value)), self.device_id, axis_id)

        for button_index, is_pressed in enumerate(state.buttons, start=1):
            self._lib.SetBtn(1 if bool(is_pressed) else 0, self.device_id, button_index)

        for pov_index, pov_value in enumerate(state.povs):
            if pov_value < 0:
                self._lib.SetDiscPov(-1, self.device_id, pov_index)
            else:
                self._lib.SetDiscPov(int(pov_value), self.device_id, pov_index)

    def reset_to_safe_state(self, reason: str) -> None:
        if self._lib is None:
            return
        try:
            self._lib.ResetVJD(self.device_id)
            self._lib.ReleaseVJD(self.device_id)
        except AttributeError:
            return
        finally:
            self._acquired = False


class VJoyOutputDevice(OutputDevice):
    def __init__(self, device_id: int, backend: VJoyBackend | None = None) -> None:
        self.device_id = device_id
        self.backend = backend or VJoyBackend(device_id=device_id)

    def write_state(self, state: DeviceState) -> None:
        self.backend.write_state(state)

    def reset_to_safe_state(self, reason: str) -> None:
        self.backend.reset_to_safe_state(reason)

    def close(self) -> None:
        self.backend.reset_to_safe_state("closed")
