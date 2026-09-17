from __future__ import annotations

import ctypes
import os
from typing import Any

from remote_joystick.models.device import DeviceState
from remote_joystick.output.base import OutputDevice


class _XUSB_REPORT(ctypes.Structure):
    _fields_ = [
        ("wButtons", ctypes.c_ushort),
        ("bLeftTrigger", ctypes.c_ubyte),
        ("bRightTrigger", ctypes.c_ubyte),
        ("sThumbLX", ctypes.c_short),
        ("sThumbLY", ctypes.c_short),
        ("sThumbRX", ctypes.c_short),
        ("sThumbRY", ctypes.c_short),
    ]


VIGEM_ERROR_NONE = 0x20000000


class ViGEmBusBackend:
    """ViGEmBus-backed output adapter for the receiver side.

    In the real Windows installation, the bus driver is shipped as a kernel driver
    package with ViGEmBus.sys and an INF file, not necessarily as a client DLL in the
    same directory. The code now detects the actual driver layout and reports the
    backend state accordingly instead of assuming the DLL is always present.
    """

    @property
    def is_available(self) -> bool:
        return self._driver_present and self._api_available

    @property
    def status_message(self) -> str:
        if not self._driver_present:
            return "The ViGEmBus driver is not installed on the receiver machine."
        if not self._api_available:
            return "The ViGEmBus driver is installed, but the client API is not available in this system."
        return "ViGEmBus driver installed and client API available on the receiver machine."

    def __init__(self, device_id: int = 1) -> None:
        self.device_id = device_id
        self._lib: Any | None = None
        self._client: Any | None = None
        self._target: Any | None = None
        self._api_available = False
        self._driver_present = False
        self._connected = False
        self._load_library()

    def _configure_function_signatures(self) -> None:
        if self._lib is None:
            return

        signatures = {
            "vigem_alloc": (ctypes.c_void_p, []),
            "vigem_connect": (ctypes.c_uint32, [ctypes.c_void_p]),
            "vigem_disconnect": (None, [ctypes.c_void_p]),
            "vigem_target_x360_alloc": (ctypes.c_void_p, []),
            "vigem_target_free": (None, [ctypes.c_void_p]),
            "vigem_target_add": (ctypes.c_uint32, [ctypes.c_void_p, ctypes.c_void_p]),
            "vigem_target_remove": (ctypes.c_uint32, [ctypes.c_void_p, ctypes.c_void_p]),
            "vigem_target_x360_update": (ctypes.c_uint32, [ctypes.c_void_p, ctypes.c_void_p, _XUSB_REPORT]),
        }

        for name, (restype, argtypes) in signatures.items():
            func = getattr(self._lib, name, None)
            if func is None:
                continue
            func.restype = restype
            func.argtypes = argtypes

    def _load_library(self) -> None:
        if os.name != "nt":
            self._driver_present = False
            self._lib = None
            self._api_available = False
            return

        driver_paths = [
            r"C:\Program Files\Nefarius Software Solutions\ViGEm Bus Driver\ViGEmBus.sys",
            r"C:\Program Files\Nefarius Software Solutions\ViGEm Bus Driver\ViGEmBus.inf",
            r"C:\Program Files\Nefarius Software Solutions\ViGEm Bus Driver\ViGEmBus.pdb",
            r"C:\Program Files\Nefarius Software Solutions\ViGEm Bus Driver\ViGEmBus.cat",
            r"C:\Program Files\ViGEm\ViGEmBus.sys",
            r"C:\Program Files\ViGEm\ViGEmBus.inf",
            r"C:\Program Files\Nefarius\ViGEm\ViGEmBus.sys",
            r"C:\Program Files\Nefarius\ViGEmBus\ViGEmBus.sys",
        ]

        self._driver_present = any(os.path.exists(path) for path in driver_paths)

        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        local_dll_candidates = [
            os.path.join(project_root, "runtime", "vigem", "ViGEmClient.dll"),
            os.path.join(project_root, "vendor", "ViGEmClient", "build", "Release", "ViGEmClient.dll"),
            os.path.join(project_root, "vendor", "ViGEmClient", "build", "Debug", "ViGEmClient.dll"),
            os.path.join(project_root, "vendor", "ViGEmClient", "ViGEmClient.dll"),
        ]

        candidate_paths = []
        for candidate in local_dll_candidates:
            if os.path.exists(candidate):
                candidate_paths.append(candidate)

        # Fall back to the default system installation locations only if the project-local
        # build is not present. This keeps the receiver working against the actual DLL we
        # just built in the repo instead of forcing the app to hunt through the Windows driver
        # installation tree.
        candidate_paths.extend([
            r"C:\Program Files\Nefarius Software Solutions\ViGEm Bus Driver\ViGEmClient.dll",
            r"C:\Program Files\Nefarius\ViGEm\ViGEmClient.dll",
            r"C:\Program Files\Nefarius\ViGEmBus\ViGEmClient.dll",
            r"C:\Program Files\ViGEm\ViGEmClient.dll",
            r"C:\Program Files\ViGEm\ViGEmBus\ViGEmClient.dll",
            r"C:\Program Files\ViGEm\x64\ViGEmClient.dll",
        ])

        seen: set[str] = set()
        for path in candidate_paths:
            if path in seen:
                continue
            seen.add(path)
            if not os.path.exists(path):
                continue
            try:
                lib = ctypes.WinDLL(path)
                required_symbols = [
                    "vigem_alloc",
                    "vigem_connect",
                    "vigem_disconnect",
                    "vigem_target_x360_alloc",
                    "vigem_target_free",
                    "vigem_target_add",
                    "vigem_target_remove",
                    "vigem_target_x360_update",
                ]
                missing = [symbol for symbol in required_symbols if not hasattr(lib, symbol)]
                if missing:
                    self._lib = lib
                    self._api_available = False
                    return
                self._lib = lib
                self._configure_function_signatures()
                self._api_available = True
                return
            except (AttributeError, OSError):
                self._lib = None
                self._api_available = False
                return

        self._lib = None
        self._api_available = False

    def _ensure_connected(self) -> bool:
        if self._lib is None or not self._api_available:
            return False
        if self._connected:
            return True

        try:
            client_factory = getattr(self._lib, "vigem_alloc")
            self._client = client_factory()
            if self._client is None:
                return False
            connect = getattr(self._lib, "vigem_connect")
            result = connect(self._client)
            if result != VIGEM_ERROR_NONE:
                self._connected = False
                return False
            target_factory = getattr(self._lib, "vigem_target_x360_alloc")
            self._target = target_factory()
            add_target = getattr(self._lib, "vigem_target_add")
            if add_target(self._client, self._target) != VIGEM_ERROR_NONE:
                self._connected = False
                return False
            self._connected = True
            return True
        except (AttributeError, TypeError, OSError, ValueError):
            self._connected = False
            return False

    def write_state(self, state: DeviceState) -> None:
        if not self._ensure_connected() or self._lib is None or self._client is None or self._target is None:
            return

        report = _XUSB_REPORT()
        report.wButtons = 0
        report.bLeftTrigger = 0
        report.bRightTrigger = 0

        button_bits = [
            0x0001, 0x0002, 0x0004, 0x0008,
            0x0010, 0x0020, 0x0040, 0x0080,
            0x0100, 0x0200, 0x0400, 0x1000,
            0x2000, 0x4000, 0x8000, 0x0000,
        ]
        for index, pressed in enumerate(state.buttons[: len(button_bits)]):
            if pressed and index < len(button_bits):
                report.wButtons |= button_bits[index]

        if len(state.axes) >= 1:
            report.sThumbLX = int(max(-1.0, min(1.0, float(state.axes[0]))) * 32767)
        if len(state.axes) >= 2:
            report.sThumbLY = int(max(-1.0, min(1.0, float(state.axes[1]))) * 32767)
        if len(state.axes) >= 3:
            report.sThumbRX = int(max(-1.0, min(1.0, float(state.axes[2]))) * 32767)
        if len(state.axes) >= 4:
            report.sThumbRY = int(max(-1.0, min(1.0, float(state.axes[3]))) * 32767)

        update = getattr(self._lib, "vigem_target_x360_update")
        update(self._client, self._target, report)

    def reset_to_safe_state(self, reason: str) -> None:
        if self._lib is None or not self._api_available:
            return
        try:
            if self._connected and self._client is not None:
                remove = getattr(self._lib, "vigem_target_remove")
                remove(self._client, self._target)
                disconnect = getattr(self._lib, "vigem_disconnect")
                disconnect(self._client)
        except (AttributeError, TypeError, OSError):
            pass
        finally:
            self._connected = False
            self._target = None
            self._client = None

    def close(self) -> None:
        self.reset_to_safe_state("closed")


class ViGEmOutputDevice(OutputDevice):
    def __init__(self, device_id: int, backend: ViGEmBusBackend | None = None) -> None:
        self.device_id = device_id
        self.backend = backend or ViGEmBusBackend(device_id=device_id)

    def write_state(self, state: DeviceState) -> None:
        self.backend.write_state(state)

    def reset_to_safe_state(self, reason: str) -> None:
        self.backend.reset_to_safe_state(reason)

    def close(self) -> None:
        self.backend.close()


ViGEmBusOutputDevice = ViGEmOutputDevice
VJoyOutputDevice = ViGEmOutputDevice
