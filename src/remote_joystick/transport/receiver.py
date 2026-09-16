from __future__ import annotations

import socket
from typing import Any

from remote_joystick.protocol.codec import decode_packet
from remote_joystick.protocol.messages import JoystickMessage
from remote_joystick.protocol.security import HMACSigner


class UDPReceiver:
    def __init__(self, bind_host: str, port: int, key: bytes) -> None:
        self.bind_host = bind_host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((bind_host, port))
        self.signer = HMACSigner(key)

    def recv(self, timeout: float | None = None) -> JoystickMessage | None:
        self.sock.settimeout(timeout)
        try:
            data, _ = self.sock.recvfrom(4096)
        except socket.timeout:
            return None
        return decode_packet(data, self.signer)

    def close(self) -> None:
        self.sock.close()
