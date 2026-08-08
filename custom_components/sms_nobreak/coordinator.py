"""Serial API client and DataUpdateCoordinator for the SMS Nobreak integration."""
from __future__ import annotations

import logging
from datetime import timedelta

import serial

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CMD_STATUS,
    CMD_STOP_TEST,
    CMD_TEST,
    CMD_TEST_UNTIL_LOW,
    DOMAIN,
    STATUS_FRAME_LENGTH,
    TEST_10S_PARAMS,
    TEST_5M_PARAMS,
)
from .protocol import UpsStatus, build_command, parse_status

_LOGGER = logging.getLogger(__name__)

SERIAL_TIMEOUT = 3  # seconds


class SmsNobreakApi:
    """Thin synchronous wrapper around the serial link.

    All methods are blocking and must be called via
    hass.async_add_executor_job from the event loop.
    """

    def __init__(self, port: str, baudrate: int) -> None:
        self._port = port
        self._baudrate = baudrate
        self._conn: serial.Serial | None = None

    def _ensure_open(self) -> serial.Serial:
        if self._conn is None or not self._conn.is_open:
            self._conn = serial.Serial(
                self._port,
                self._baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=SERIAL_TIMEOUT,
            )
        return self._conn

    def _send(self, frame: bytes) -> bytes:
        conn = self._ensure_open()
        conn.reset_input_buffer()
        conn.write(frame)
        return conn.read(STATUS_FRAME_LENGTH)

    def query_status(self) -> UpsStatus:
        raw = self._send(build_command(CMD_STATUS))
        status = parse_status(raw)
        if status is None:
            raise UpdateFailed(f"Resposta inválida ou vazia do nobreak: {raw!r}")
        return status

    def start_test_10s(self) -> None:
        self._send(build_command(CMD_TEST, TEST_10S_PARAMS))

    def start_test_5m(self) -> None:
        self._send(build_command(CMD_TEST, TEST_5M_PARAMS))

    def start_test_until_low(self) -> None:
        self._send(build_command(CMD_TEST_UNTIL_LOW))

    def stop_test(self) -> None:
        self._send(build_command(CMD_STOP_TEST))

    def close(self) -> None:
        if self._conn is not None and self._conn.is_open:
            self._conn.close()


class SmsNobreakCoordinator(DataUpdateCoordinator[UpsStatus]):
    """Polls the UPS on a timer and hands parsed status to entities."""

    def __init__(self, hass: HomeAssistant, api: SmsNobreakApi, scan_interval: int) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self.api = api

    async def _async_update_data(self) -> UpsStatus:
        try:
            return await self.hass.async_add_executor_job(self.api.query_status)
        except serial.SerialException as err:
            raise UpdateFailed(f"Erro de comunicação serial com o nobreak: {err}") from err
