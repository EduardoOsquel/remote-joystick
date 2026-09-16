from remote_joystick.models.device import DeviceState
from remote_joystick.services.bridge import BridgeService


class FakeInput:
    def __init__(self) -> None:
        self._state = type(
            "State",
            (),
            {
                "logical_id": "logic-a",
                "physical_id": "phys-a",
                "name": "Fake Stick",
                "sequence": 4,
                "timestamp_ms": 5678,
                "axes": [0.2, -0.8, 0.0],
                "buttons": [True, False],
                "povs": [0, 18000],
                "connected": True,
                "channel": 1,
            },
        )()

    def read_state(self, channel: int):
        return self._state

    def close(self) -> None:
        return None

    @property
    def connection_state(self):
        return type("ConnectionState", (), {"connected": True})()


class FakeOutput:
    def __init__(self) -> None:
        self.last_state = None

    def write_state(self, state: DeviceState) -> None:
        self.last_state = state

    def reset_to_safe_state(self, reason: str) -> None:
        self.last_state = None

    def close(self) -> None:
        return None


def test_bridge_service_normalizes_and_forwards_state() -> None:
    input_device = FakeInput()
    output_device = FakeOutput()
    bridge = BridgeService(input_device, output_device)

    result = bridge.write_next(1)

    assert result.channel == 1
    assert result.axes[0] == 0.2
    assert result.buttons == [True, False]
    assert output_device.last_state == result
