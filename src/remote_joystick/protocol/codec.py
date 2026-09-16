from __future__ import annotations

import struct

from remote_joystick.protocol.messages import JoystickMessage, PacketType
from remote_joystick.protocol.security import HMACSigner

MAGIC = b"RJS1"
VERSION = 1
MAX_PACKET_SIZE = 4096
HEADER_FORMAT = "<4sBBHIBIQBBBB"


def _pack_bool_array(values: list[bool]) -> bytes:
    return bytes(1 if value else 0 for value in values)


def _unpack_bool_array(payload: bytes) -> list[bool]:
    return [bool(value) for value in payload]


def encode_packet(message: JoystickMessage, signer: HMACSigner) -> bytes:
    if len(message.device_id.encode("utf-8")) > 255:
        raise ValueError("device_id too long")
    if len(message.axes) > 8:
        raise ValueError("too many axes for protocol")
    if len(message.buttons) > 128:
        raise ValueError("too many buttons for protocol")
    if len(message.povs) > 4:
        raise ValueError("too many povs for protocol")
    if message.version != VERSION:
        raise ValueError("Unsupported protocol version")

    device_bytes = message.device_id.encode("utf-8")
    axes_bytes = b"".join(struct.pack("<f", float(axis)) for axis in message.axes)
    buttons_bytes = _pack_bool_array(message.buttons)
    povs_bytes = b"".join(struct.pack("<h", int(pov)) for pov in message.povs)
    header = struct.pack(
        HEADER_FORMAT,
        MAGIC,
        VERSION,
        int(message.message_type),
        message.session_id,
        message.sender_id,
        message.channel,
        message.sequence,
        message.timestamp_ms,
        len(device_bytes),
        len(message.axes),
        len(message.buttons),
        len(message.povs),
    )
    payload = header + device_bytes + axes_bytes + buttons_bytes + povs_bytes
    if len(payload) > MAX_PACKET_SIZE:
        raise ValueError("Packet exceeds maximum allowed size")
    signature = signer.sign(payload)
    return payload + signature


def decode_packet(raw: bytes, signer: HMACSigner) -> JoystickMessage:
    if len(raw) < 32:
        raise ValueError("Packet too short")
    if raw[:4] != MAGIC:
        raise ValueError("bad magic")

    payload = raw[:-32]
    signature = raw[-32:]
    if not signer.verify(payload, signature):
        raise ValueError("invalid HMAC signature")

    if len(payload) < struct.calcsize(HEADER_FORMAT):
        raise ValueError("packet header truncated")

    fields = struct.unpack_from(HEADER_FORMAT, payload)
    magic, version, message_type, session_id, sender_id, channel, sequence, timestamp_ms, device_len, axis_count, button_count, pov_count = fields
    if magic != MAGIC:
        raise ValueError("bad magic")
    if version != VERSION:
        raise ValueError("Unsupported protocol version")

    expected_size = struct.calcsize(HEADER_FORMAT) + device_len + axis_count * 4 + button_count + pov_count * 2
    if len(payload) != expected_size:
        raise ValueError("packet size mismatch")
    if message_type not in PacketType._value2member_map_:
        raise ValueError("unsupported packet type")
    if axis_count > 8 or button_count > 128 or pov_count > 4:
        raise ValueError("value count exceeds supported protocol limits")

    offset = struct.calcsize(HEADER_FORMAT)
    device_id = payload[offset : offset + device_len].decode("utf-8")
    offset += device_len
    axes = list(struct.unpack_from(f"<{axis_count}f", payload, offset)) if axis_count else []
    offset += axis_count * 4
    buttons = _unpack_bool_array(payload[offset : offset + button_count]) if button_count else []
    offset += button_count
    povs = list(struct.unpack_from(f"<{pov_count}h", payload, offset)) if pov_count else []

    return JoystickMessage(
        version=version,
        message_type=PacketType(message_type),
        session_id=session_id,
        sender_id=sender_id,
        channel=channel,
        device_id=device_id,
        sequence=sequence,
        timestamp_ms=timestamp_ms,
        axes=axes,
        buttons=buttons,
        povs=povs,
    )
