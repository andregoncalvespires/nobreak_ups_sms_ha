"""Low-level protocol helpers for the SMS Nobreak (Megatec/Voltronic-style
serial UPS protocol).

Command frame:  <cmd_byte> <4 param bytes> <checksum> 0x0D
Status frame:   0x3D <8 x 2-byte fields> <flags byte> <reserved byte> 0x0D

Reverse-engineered from the original Node-RED flow. The checksum is a
simple two's-complement of the sum of every preceding byte, which is
common to several UPS brands built on this protocol family - so this
module should keep working unmodified for other models, as long as the
field layout matches (only STATUS_FRAME_LENGTH / offsets would need
adjusting for a model that reports extra fields).
"""
from __future__ import annotations

from dataclasses import dataclass

from .const import STATUS_FRAME_LENGTH


def _checksum(payload: bytes) -> int:
    return (0x100 - (sum(payload) % 0x100)) & 0xFF


def build_command(cmd_byte: int, param_bytes: bytes = b"\xff\xff\xff\xff") -> bytes:
    """Build a full command frame, including checksum and terminator."""
    body = bytes([cmd_byte]) + param_bytes
    return body + bytes([_checksum(body)]) + b"\x0d"


@dataclass
class UpsStatus:
    last_input_vac: float
    input_vac: float
    output_vac: float
    output_power_percent: float
    output_hz: float
    battery_level: float
    temperature_c: float
    battery_in_use: bool
    battery_low: bool
    bypass: bool
    boost: bool
    ups_ok: bool
    test_active: bool
    shutdown_active: bool
    beep_on: bool


def parse_status(raw: bytes) -> UpsStatus | None:
    """Parse a status response frame. Returns None if the frame is invalid."""
    if not raw or len(raw) < STATUS_FRAME_LENGTH:
        return None
    if raw[0] != 0x3D or raw[STATUS_FRAME_LENGTH - 1] != 0x0D:
        return None

    def word(offset: int) -> int:
        return int.from_bytes(raw[offset : offset + 2], "big")

    flags = raw[15]

    return UpsStatus(
        last_input_vac=word(1) / 10,
        input_vac=word(3) / 10,
        output_vac=word(5) / 10,
        output_power_percent=word(7) / 10,
        output_hz=word(9) / 10,
        battery_level=word(11) / 10,
        temperature_c=word(13) / 10,
        battery_in_use=bool((flags >> 7) & 1),
        battery_low=bool((flags >> 6) & 1),
        bypass=bool((flags >> 5) & 1),
        boost=bool((flags >> 4) & 1),
        ups_ok=bool((flags >> 3) & 1),
        test_active=bool((flags >> 2) & 1),
        shutdown_active=bool((flags >> 1) & 1),
        beep_on=bool(flags & 1),
    )
