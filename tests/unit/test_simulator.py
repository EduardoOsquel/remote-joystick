from remote_joystick.input.simulator import SimulatedJoystick, SimulatorInputDevice


def test_simulator_has_two_independent_devices():
    sim = SimulatorInputDevice(device_count=2)
    devices = sim.list_devices()
    assert len(devices) == 2
    assert {device.channel for device in devices} == {1, 2}
    assert devices[0].physical_id != devices[1].physical_id


def test_simulator_state_updates():
    sim = SimulatorInputDevice(device_count=1)
    state = sim.read_state(1)
    assert state is not None
    assert -1.0 <= state.axes[0] <= 1.0
    assert len(state.buttons) >= 1
    assert len(state.povs) >= 1


def test_simulated_joystick_sequence_progresses():
    stick = SimulatedJoystick(channel=1, name="Sim 1", axes=4, buttons=8, povs=2)
    first = stick.read_state()
    second = stick.read_state()
    assert first.sequence != second.sequence
    assert first.timestamp_ms <= second.timestamp_ms
