from remote_joystick.input.windows import WindowsJoystickInputDevice
from remote_joystick.models.device import DeviceIdentity, DeviceState
from remote_joystick.output.vigem import ViGEmBusBackend
from remote_joystick.output.vjoy import VJoyBackend, VJoyOutputDevice


class FakeVJoyBackend:
    def __init__(self) -> None:
        self.last_state = None

    def write_state(self, state: DeviceState) -> None:
        self.last_state = state

    def reset_to_safe_state(self, reason: str) -> None:
        self.last_state = None


def test_windows_input_device_reports_unique_devices() -> None:
    input_device = WindowsJoystickInputDevice()
    devices = input_device.list_devices()
    signatures = {
        (device.name.lower(), device.vendor_id or "", device.product_id or "", device.axis_count, device.button_count, device.pov_count)
        for device in devices
    }
    assert len(signatures) == len(devices)


def test_windows_input_device_deduplicates_identical_devices() -> None:
    devices = [
        DeviceIdentity(name="Controla. Microsoft PC-joystick", persistent_id="windows:0", physical_id="windows:0", channel=1, vendor_id="1103", product_id="45322", axis_count=4, button_count=16, pov_count=1, source="windows"),
        DeviceIdentity(name="Controla. Microsoft PC-joystick", persistent_id="windows:1", physical_id="windows:1", channel=2, vendor_id="4660", product_id="48813", axis_count=6, button_count=25, pov_count=1, source="windows"),
        DeviceIdentity(name="Controla. Microsoft PC-joystick", persistent_id="windows:2", physical_id="windows:2", channel=3, vendor_id="1103", product_id="45322", axis_count=4, button_count=16, pov_count=1, source="windows"),
    ]

    deduped = WindowsJoystickInputDevice._deduplicate_devices(devices)

    assert [device.channel for device in deduped] == [1, 2]
    assert len(deduped) == 2


def test_vjoy_backend_loads_x64_dll_location(monkeypatch) -> None:
    seen_paths: list[str] = []

    class DummyLib:
        def __init__(self) -> None:
            self.GetNumberOfVJD = lambda: 1
            self.AcquireVJD = lambda *_: 1
            self.ReleaseVJD = lambda *_: 1
            self.SetAxis = lambda *_: 1
            self.SetBtn = lambda *_: 1
            self.SetDiscPov = lambda *_: 1
            self.ResetVJD = lambda *_: 1

    def fake_exists(path: str) -> bool:
        return path == r"C:\Program Files\vJoy\x64\vJoyInterface.dll"

    def fake_windll(path: str):
        seen_paths.append(path)
        return DummyLib()

    monkeypatch.setattr("os.path.exists", fake_exists)
    monkeypatch.setattr("ctypes.WinDLL", fake_windll)

    backend = VJoyBackend(device_id=1)

    assert backend._lib is not None
    assert backend.is_available is True
    assert seen_paths == [r"C:\Program Files\vJoy\x64\vJoyInterface.dll"]


def test_list_vjoy_uses_real_availability_status(monkeypatch, capsys) -> None:
    class FakeBackend:
        @property
        def is_available(self) -> bool:
            return False

    class FakeOutputDevice:
        def __init__(self, device_id: int) -> None:
            self.backend = FakeBackend()

    monkeypatch.setattr("remote_joystick.cli.VJoyOutputDevice", FakeOutputDevice)

    from remote_joystick.cli import list_vjoy

    list_vjoy(None)
    captured = capsys.readouterr()

    assert "manual installation requirement" in captured.out.lower()
    assert "dll detected and available" not in captured.out.lower()


def test_list_vigem_uses_vigem_backend_status(monkeypatch, capsys) -> None:
    class FakeBackend:
        @property
        def status_message(self) -> str:
            return "The ViGEmBus DLL is not installed on the receiver machine."

    class FakeOutputDevice:
        def __init__(self, device_id: int) -> None:
            self.backend = FakeBackend()

    monkeypatch.setattr("remote_joystick.cli.ViGEmOutputDevice", FakeOutputDevice)

    from remote_joystick.cli import list_vigem

    list_vigem(None)
    captured = capsys.readouterr()

    assert "vigembus" in captured.out.lower()
    assert "not installed" in captured.out.lower()


def test_vigembus_driver_is_detected_from_sys_file(monkeypatch) -> None:
    def fake_exists(path: str) -> bool:
        return path == r"C:\Program Files\Nefarius Software Solutions\ViGEm Bus Driver\ViGEmBus.sys"

    monkeypatch.setattr("os.path.exists", fake_exists)

    backend = ViGEmBusBackend(device_id=1)

    assert backend._driver_present is True
    assert "driver is installed" in backend.status_message.lower()


def test_vigembus_backend_prefers_local_vendor_dll(monkeypatch) -> None:
    local_dll = r"C:\Python\remote-joystick\vendor\ViGEmClient\build\Release\ViGEmClient.dll"
    driver_sys = r"C:\Program Files\Nefarius Software Solutions\ViGEm Bus Driver\ViGEmBus.sys"

    class DummyLib:
        vigem_alloc = staticmethod(lambda: object())
        vigem_connect = staticmethod(lambda *_: 0)
        vigem_disconnect = staticmethod(lambda *_: 0)
        vigem_target_x360_alloc = staticmethod(lambda: object())
        vigem_target_free = staticmethod(lambda *_: None)
        vigem_target_add = staticmethod(lambda *_: 0)
        vigem_target_remove = staticmethod(lambda *_: 0)
        vigem_target_x360_update = staticmethod(lambda *_: 0)

    def fake_exists(path: str) -> bool:
        return path in {local_dll, driver_sys}

    def fake_windll(path: str):
        assert path == local_dll
        return DummyLib()

    monkeypatch.setattr("os.path.exists", fake_exists)
    monkeypatch.setattr("ctypes.WinDLL", fake_windll)

    backend = ViGEmBusBackend(device_id=1)

    assert backend._driver_present is True
    assert backend._lib is not None
    assert backend._api_available is True
    assert backend.is_available is True


def test_vigembus_backend_uses_actual_exported_symbols() -> None:
    backend = ViGEmBusBackend(device_id=1)
    assert backend._lib is not None
    assert hasattr(backend._lib, "vigem_alloc")
    assert hasattr(backend._lib, "vigem_connect")
    assert hasattr(backend._lib, "vigem_target_x360_alloc")
    assert hasattr(backend._lib, "vigem_target_free")
    assert backend._api_available is True


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
