from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class NetworkConfig:
    bind_host: str = "0.0.0.0"
    target_host: str = "127.0.0.1"
    port: int = 26760
    send_rate_hz: float = 125.0
    heartbeat_ms: int = 250
    timeout_ms: int = 750
    max_packet_age_ms: int = 500


@dataclass(slots=True)
class ApplicationConfig:
    mode: str = "sender"
    log_level: str = "INFO"


@dataclass(slots=True)
class SecurityConfig:
    shared_key: str = "CHANGE_ME"


@dataclass(slots=True)
class JoystickConfig:
    channel: int = 1
    physical_device_id: str = ""
    vjoy_device_id: int = 1
    disconnect_axis_value: float = 0.0
    disconnect_throttle_value: float = -1.0
    mapping: dict[str, list[dict[str, object]]] = field(default_factory=dict)


@dataclass(slots=True)
class Config:
    application: ApplicationConfig = field(default_factory=ApplicationConfig)
    network: NetworkConfig = field(default_factory=NetworkConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    joysticks: list[JoystickConfig] = field(default_factory=list)

    @classmethod
    def load(cls, path: str | Path) -> "Config":
        with Path(path).open("rb") as fh:
            data = tomllib.load(fh)
        cfg = cls()
        app = data.get("application", {})
        cfg.application = ApplicationConfig(**app)
        net = data.get("network", {})
        cfg.network = NetworkConfig(**net)
        sec = data.get("security", {})
        cfg.security = SecurityConfig(**sec)
        cfg.joysticks = [JoystickConfig(**item) for item in data.get("joysticks", [])]
        for cfg_item in cfg.joysticks:
            cfg_item.mapping = {}
        return cfg

    def validate(self) -> None:
        if self.network.port < 1 or self.network.port > 65535:
            raise ValueError("Network port must be between 1 and 65535")
        if not 1.0 <= self.network.send_rate_hz <= 1000.0:
            raise ValueError("send_rate_hz must be between 1 and 1000")
        if self.security.shared_key in {"", "CAMBIAR_POR_UNA_CLAVE_SEGURA", "CHANGE_ME"}:
            raise ValueError("shared_key must be changed from the example value")
        channels = {item.channel for item in self.joysticks}
        if len(channels) != len(self.joysticks):
            raise ValueError("Joystick channel values must be unique")
        vjoy_ids = {item.vjoy_device_id for item in self.joysticks}
        if len(vjoy_ids) != len(self.joysticks):
            raise ValueError("vJoy device IDs must be unique")
        physical_ids = {item.physical_device_id for item in self.joysticks}
        if len(physical_ids) != len(self.joysticks):
            raise ValueError("Physical device IDs must be unique")
