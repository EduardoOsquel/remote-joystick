import ctypes

from remote_joystick.output.vigem import ViGEmBusBackend


class FakePointerLibrary:
    def __init__(self):
        self.calls = []

    def vigem_alloc(self):
        return ctypes.c_void_p(0x1234)

    def vigem_connect(self, client):
        self.calls.append(("connect", client))
        return 0x20000000

    def vigem_target_x360_alloc(self):
        return ctypes.c_void_p(0x5678)

    def vigem_target_add(self, client, target):
        self.calls.append(("add", client, target))
        return 0x20000000

    def vigem_target_x360_update(self, client, target, report):
        self.calls.append(("update", client, target, report))
        return 0x20000000


def test_vigem_sets_pointer_signatures_for_handles():
    backend = ViGEmBusBackend.__new__(ViGEmBusBackend)
    backend._lib = FakePointerLibrary()
    backend._api_available = True
    backend._connected = False

    assert backend._ensure_connected() is True
    assert int(backend._client) == 0x1234
    assert int(backend._target) == 0x5678
