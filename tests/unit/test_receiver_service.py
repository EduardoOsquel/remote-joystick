from remote_joystick.protocol.messages import JoystickMessage, PacketType
from remote_joystick.services.receiver_service import ReceiverService


class RecordingOutput:
    def __init__(self):
        self.states = []

    def write_state(self, state):
        self.states.append(state)

    def reset_to_safe_state(self, reason):
        pass

    def close(self):
        pass


def test_receiver_service_forwards_packet_to_output():
    output = RecordingOutput()
    service = ReceiverService(output)

    packet = JoystickMessage(
        version=1,
        message_type=PacketType.STATE,
        session_id=10,
        sender_id=3,
        channel=1,
        device_id="device-A",
        sequence=7,
        timestamp_ms=123,
        axes=[0.1, -0.2, 0.3],
        buttons=[True, False, True],
        povs=[0],
    )

    service.handle_packet(packet)

    assert len(output.states) == 1
    state = output.states[0]
    assert state.axes == packet.axes
    assert state.buttons == packet.buttons
    assert state.povs == packet.povs
    assert state.channel == packet.channel
