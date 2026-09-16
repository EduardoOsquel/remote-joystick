from __future__ import annotations

from remote_joystick.input.base import InputDevice
from remote_joystick.protocol.messages import JoystickMessage


class SenderService:
    def __init__(self, input_device: InputDevice) -> None:
        self.input_device = input_device

    def send_next(self, channel: int) -> JoystickMessage | None:
        state = self.input_device.read_state(channel)
        return JoystickMessage(
            version=1,
            message_type=1,
            session_id=1,
            sender_id=1,
            channel=channel,
            device_id=state.physical_id,
            sequence=state.sequence,
            timestamp_ms=state.timestamp_ms,
            axes=state.axes,
            buttons=state.buttons,
            povs=state.povs,
        )

    def close(self) -> None:
        self.input_device.close()
