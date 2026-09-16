from __future__ import annotations

import platform
import sys
from pathlib import Path


def get_system_summary() -> dict[str, str]:
    return {
        "platform": platform.platform(),
        "python_version": sys.version,
        "architecture": platform.machine(),
        "windows": platform.system(),
    }


def assert_windows64() -> None:
    if platform.system() != "Windows":
        raise RuntimeError("This project is intended for Windows only")
    if platform.machine() not in {"AMD64", "x86_64"}:
        raise RuntimeError("Windows 64-bit architecture is required")


def get_log_directory() -> Path:
    return Path.cwd() / "logs"
