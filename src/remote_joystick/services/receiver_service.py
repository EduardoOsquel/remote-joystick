from __future__ import annotations

from remote_joystick.output.base import OutputDevice
from remote_joystick.protocol.messages import JoystickMessage


class ReceiverService:
    def __init__(self, output_device: OutputDevice) -> None:
        self.output_device = output_device

    def handle_packet(self, packet: JoystickMessage) -> None:
        self.output_device.write_state(
            type(
                "StateShim",
                (),
                {
                    "logical_id": packet.device_id,
                    "physical_id": packet.device_id,
                    "name": packet.device_id,
                    "sequence": packet.sequence,
                    "timestamp_ms": packet.timestamp_ms,
                    "axes": packet.axes,
                    "buttons": packet.buttons,
                    "povs": packet.povs,
                    "connected": True,
                    "channel": packet.channel,
                },
            )()
        )

    def close(self) -> None:
        self.output_device.close()
