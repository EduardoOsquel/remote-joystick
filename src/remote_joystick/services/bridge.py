from __future__ import annotations

from remote_joystick.input.base import InputDevice
from remote_joystick.mapping.axis_mapping import axis_to_vjoy, normalize_axis
from remote_joystick.models.device import DeviceState
from remote_joystick.output.base import OutputDevice


class BridgeService:
    """Bridge a device input stream into a target output device.

    This layer intentionally keeps the logic simple: it normalizes values from the
    source device into a DeviceState and forwards the result to the output device.
    The implementation remains abstract so that the real Windows HID and vJoy
    adapters can be plugged in later without changing the service contract.
    """

    def __init__(self, input_device: InputDevice, output_device: OutputDevice) -> None:
        self.input_device = input_device
        self.output_device = output_device

    def write_next(self, channel: int) -> DeviceState:
        raw_state = self.input_device.read_state(channel)
        state = DeviceState(
            logical_id=getattr(raw_state, "logical_id", f"channel-{channel}"),
            physical_id=getattr(raw_state, "physical_id", f"channel-{channel}"),
            name=getattr(raw_state, "name", f"Channel {channel}"),
            sequence=getattr(raw_state, "sequence", 0),
            timestamp_ms=getattr(raw_state, "timestamp_ms", 0),
            axes=[axis_to_vjoy(normalize_axis(value)) for value in getattr(raw_state, "axes", [])],
            buttons=[bool(value) for value in getattr(raw_state, "buttons", [])],
            povs=[int(value) for value in getattr(raw_state, "povs", [])],
            connected=getattr(raw_state, "connected", True),
            channel=getattr(raw_state, "channel", channel),
        )
        self.output_device.write_state(state)
        return state

    def reset_to_safe_state(self, reason: str) -> None:
        self.output_device.reset_to_safe_state(reason)

    def close(self) -> None:
        self.output_device.close()
        self.input_device.close()
