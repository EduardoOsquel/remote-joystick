from remote_joystick.input.windows import WindowsJoystickInputDevice
from remote_joystick.models.device import DeviceState
from remote_joystick.output.vjoy import VJoyOutputDevice


class FakeVJoyBackend:
    def __init__(self) -> None:
        self.last_state = None

    def write_state(self, state: DeviceState) -> None:
        self.last_state = state

    def reset_to_safe_state(self, reason: str) -> None:
        self.last_state = None


def test_windows_input_device_reports_empty_when_not_available() -> None:
    input_device = WindowsJoystickInputDevice()
    devices = input_device.list_devices()
    assert devices == []


def test_vjoy_output_device_tracks_last_state() -> None:
    backend = FakeVJoyBackend()
    output = VJoyOutputDevice(device_id=1, backend=backend)
    state = DeviceState(
        logical_id="joystick-1",
        physical_id="joystick-1",
        name="Test Stick",
        sequence=3,
        timestamp_ms=12345,
        axes=[0.25, -0.5, 0.0, 1.0],
        buttons=[True, False, True],
        povs=[0, 9000],
        connected=True,
        channel=1,
    )

    output.write_state(state)
    assert backend.last_state == state

    output.reset_to_safe_state("test reset")
    assert backend.last_state is None
