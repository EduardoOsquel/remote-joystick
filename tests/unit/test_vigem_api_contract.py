from remote_joystick.output.vigem import VIGEM_ERROR_NONE, ViGEmBusBackend


class FakeClient:
    pass


class FakeTarget:
    pass


class FakeViGEmLib:
    def __init__(self):
        self.alloc_calls = 0
        self.connect_calls = []
        self.add_calls = []
        self.update_calls = []

    def vigem_alloc(self):
        self.alloc_calls += 1
        return FakeClient()

    def vigem_connect(self, client):
        self.connect_calls.append(client)
        return VIGEM_ERROR_NONE

    def vigem_target_x360_alloc(self):
        return FakeTarget()

    def vigem_target_add(self, client, target):
        self.add_calls.append((client, target))
        return VIGEM_ERROR_NONE

    def vigem_target_x360_update(self, client, target, report):
        self.update_calls.append((client, target, report))
        return VIGEM_ERROR_NONE


def test_vigem_connect_and_target_add_use_real_winapi_contract():
    backend = ViGEmBusBackend.__new__(ViGEmBusBackend)
    backend._lib = FakeViGEmLib()
    backend._api_available = True
    backend._connected = False
    backend._client = None
    backend._target = None

    assert backend._ensure_connected() is True
    assert len(backend._lib.connect_calls) == 1
    assert len(backend._lib.add_calls) == 1
    assert backend._connected is True
