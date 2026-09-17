from remote_joystick.models.device import DeviceState
from remote_joystick.output.vigem import ViGEmBusBackend


class FakeViGEmLib:
    def __init__(self):
        self.calls = []

    def vigem_target_x360_update(self, client, target, report):
        self.calls.append((client, target, report))
        return 0


def test_vigem_backend_writes_xusb_report():
    backend = ViGEmBusBackend.__new__(ViGEmBusBackend)
    backend._lib = FakeViGEmLib()
    backend._client = object()
    backend._target = object()
    backend._api_available = True
    backend._connected = True

    state = DeviceState(
        logical_id="receiver-1",
        physical_id="physical-1",
        name="remote-controller",
        axes=[0.5, -0.25, 0.75, -1.0],
        buttons=[False] * 11 + [True] + [False] * 4,
        povs=[0],
    )

    backend.write_state(state)

    assert len(backend._lib.calls) == 1
    _, _, report = backend._lib.calls[0]
    assert report.wButtons == 0x1000
    assert report.sThumbLX == int(0.5 * 32767)
    assert report.sThumbLY == int(-0.25 * 32767)
    assert report.sThumbRX == int(0.75 * 32767)
    assert report.sThumbRY == int(-1.0 * 32767)
