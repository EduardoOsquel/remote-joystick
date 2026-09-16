import pytest

from remote_joystick.protocol.codec import encode_packet, decode_packet
from remote_joystick.protocol.messages import JoystickMessage, PacketType
from remote_joystick.protocol.security import HMACSigner


@pytest.fixture
def signer():
    return HMACSigner(b"test-shared-key")


def test_codec_round_trip_valid(signer):
    original = JoystickMessage(
        version=1,
        message_type=PacketType.STATE,
        session_id=42,
        sender_id=7,
        channel=1,
        device_id="device-A",
        sequence=99,
        timestamp_ms=1234,
        axes=[0.25, -0.5, 0.0, 1.0],
        buttons=[True, False, True],
        povs=[0, 9000, 18000],
        key=b"test-shared-key",
    )
    encoded = encode_packet(original, signer)
    decoded = decode_packet(encoded, signer)
    assert decoded.device_id == original.device_id
    assert decoded.sequence == original.sequence
    assert decoded.axes == original.axes
    assert decoded.buttons == original.buttons
    assert decoded.povs == original.povs
    assert decoded.channel == original.channel


def test_invalid_hmac_rejected(signer):
    original = JoystickMessage(
        version=1,
        message_type=PacketType.STATE,
        session_id=42,
        sender_id=7,
        channel=1,
        device_id="device-A",
        sequence=99,
        timestamp_ms=1234,
        axes=[0.0, 0.25],
        buttons=[True],
        povs=[0],
        key=b"test-shared-key",
    )
    encoded = encode_packet(original, signer)
    encoded = b"X" + encoded[1:]
    with pytest.raises(ValueError):
        decode_packet(encoded, signer)


def test_truncated_packet_rejected(signer):
    with pytest.raises(ValueError):
        decode_packet(b"bad", signer)


def test_version_rejected(signer):
    original = JoystickMessage(
        version=1,
        message_type=PacketType.STATE,
        session_id=42,
        sender_id=7,
        channel=1,
        device_id="device-A",
        sequence=99,
        timestamp_ms=1234,
        axes=[0.0],
        buttons=[True],
        povs=[0],
        key=b"test-shared-key",
    )
    encoded = encode_packet(original, signer)
    tampered = bytearray(encoded)
    tampered[5] = 99
    with pytest.raises(ValueError):
        decode_packet(bytes(tampered), signer)
