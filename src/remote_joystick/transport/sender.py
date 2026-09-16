from __future__ import annotations

import socket
import time
from typing import Any

from remote_joystick.protocol.codec import encode_packet
from remote_joystick.protocol.messages import JoystickMessage
from remote_joystick.protocol.security import HMACSigner


class UDPSender:
    def __init__(self, host: str, port: int, key: bytes) -> None:
        self.host = host
        self.port = port
        self.key = key
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.signer = HMACSigner(self.key)

    def send(self, message: JoystickMessage) -> None:
        packet = encode_packet(message, self.signer)
        self.sock.sendto(packet, (self.host, self.port))

    def close(self) -> None:
        self.sock.close()
