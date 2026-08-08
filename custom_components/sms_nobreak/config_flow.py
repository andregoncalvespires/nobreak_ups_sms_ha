"""Config flow for the SMS Nobreak (serial UPS) integration.

Discovers available serial/USB devices so the user can pick one from a
dropdown instead of typing a device path, with a manual-entry fallback
for setups where the port isn't detected (e.g. a device added after
Home Assistant started, or a non-USB serial port).
"""
from __future__ import annotations

import glob
import logging
import os
from typing import Any

import serial
import serial.tools.list_ports
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    CMD_STATUS,
    CONF_BAUDRATE,
    CONF_CAPACITY_VA,
    CONF_POWER_FACTOR,
    CONF_SCAN_INTERVAL,
    CONF_SERIAL_PORT,
    DEFAULT_BAUDRATE,
    DEFAULT_CAPACITY_VA,
    DEFAULT_POWER_FACTOR,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MANUAL_ENTRY_VALUE,
    STATUS_FRAME_LENGTH,
)
from .protocol import build_command, parse_status

_LOGGER = logging.getLogger(__name__)


def _by_id_for(device_path: str) -> str | None:
    """Return the stable /dev/serial/by-id/... path for a device, if one exists.

    Using the by-id symlink (like the original flow did) means the
    configured port keeps working even if the USB device enumerates as
    a different /dev/ttyUSBx after a reboot or a hub replug.
    """
    for link in glob.glob("/dev/serial/by-id/*"):
        try:
            if os.path.realpath(link) == os.path.realpath(device_path):
                return link
        except OSError:
            continue
    return None


def _discover_ports() -> dict[str, str]:
    """Return {value: label} for every serial port currently detected."""
    ports: dict[str, str] = {}
    for info in serial.tools.list_ports.comports():
        stable_path = _by_id_for(info.device)
        value = stable_path or info.device
        label_bits = [info.device]
        if info.manufacturer:
            label_bits.append(info.manufacturer)
        if info.description and info.description not in ("n/a", info.device):
            label_bits.append(info.description)
        ports[value] = " – ".join(label_bits)
    return ports


def _test_connection(port: str, baudrate: int) -> bool:
    """Open the port and confirm a valid status frame comes back."""
    with serial.Serial(port, baudrate, timeout=3) as conn:
        conn.reset_input_buffer()
        conn.write(build_command(CMD_STATUS))
        raw = conn.read(STATUS_FRAME_LENGTH)
    return parse_status(raw) is not None


def _connection_schema(discovered: dict[str, str] | None = None) -> vol.Schema:
    fields: dict[Any, Any] = {}
    if discovered is not None:
        options = [SelectOptionDict(value=v, label=l) for v, l in discovered.items()]
        options.append(
            SelectOptionDict(value=MANUAL_ENTRY_VALUE, label="Digitar caminho manualmente…")
        )
        fields[vol.Required(CONF_SERIAL_PORT)] = SelectSelector(
            SelectSelectorConfig(options=options, mode=SelectSelectorMode.DROPDOWN)
        )
    else:
        fields[vol.Required(CONF_SERIAL_PORT)] = str

    fields.update(
        {
            vol.Required(CONF_BAUDRATE, default=DEFAULT_BAUDRATE): int,
            vol.Required(CONF_CAPACITY_VA, default=DEFAULT_CAPACITY_VA): int,
            vol.Required(CONF_POWER_FACTOR, default=DEFAULT_POWER_FACTOR): vol.Coerce(float),
            vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int,
        }
    )
    return vol.Schema(fields)


class SmsNobreakConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for the SMS Nobreak integration."""

    VERSION = 1

    def __init__(self) -> None:
        self._discovered_ports: dict[str, str] = {}
        self._last_error: str | None = None

    async def _try_create_entry(self, user_input: dict[str, Any]) -> FlowResult | None:
        """Validate the connection and create the entry. Returns None on error
        (caller re-shows the form) with self._last_error set."""
        port = user_input[CONF_SERIAL_PORT]
        baudrate = user_input[CONF_BAUDRATE]
        try:
            ok = await self.hass.async_add_executor_job(_test_connection, port, baudrate)
        except serial.SerialException:
            self._last_error = "cannot_connect"
            return None
        if not ok:
            self._last_error = "invalid_response"
            return None

        await self.async_set_unique_id(port)
        self._abort_if_unique_id_configured()
        return self.async_create_entry(
            title=f"Nobreak ({port})",
            data={CONF_SERIAL_PORT: port, CONF_BAUDRATE: baudrate},
            options={
                CONF_CAPACITY_VA: user_input[CONF_CAPACITY_VA],
                CONF_POWER_FACTOR: user_input[CONF_POWER_FACTOR],
                CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL],
            },
        )

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}

        if not self._discovered_ports:
            self._discovered_ports = await self.hass.async_add_executor_job(_discover_ports)

        if user_input is not None:
            if user_input[CONF_SERIAL_PORT] == MANUAL_ENTRY_VALUE:
                return await self.async_step_manual_port()

            self._last_error = None
            result = await self._try_create_entry(user_input)
            if result is not None:
                return result
            errors["base"] = self._last_error

        return self.async_show_form(
            step_id="user",
            data_schema=_connection_schema(self._discovered_ports),
            errors=errors,
            description_placeholders={"count": str(len(self._discovered_ports))},
        )

    async def async_step_manual_port(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            self._last_error = None
            result = await self._try_create_entry(user_input)
            if result is not None:
                return result
            errors["base"] = self._last_error

        return self.async_show_form(
            step_id="manual_port", data_schema=_connection_schema(None), errors=errors
        )

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> "SmsNobreakOptionsFlow":
        return SmsNobreakOptionsFlow(config_entry)


class SmsNobreakOptionsFlow(config_entries.OptionsFlow):
    """Lets the user tweak capacity/power factor/poll interval after setup."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        opts = self.config_entry.options
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_CAPACITY_VA, default=opts.get(CONF_CAPACITY_VA, DEFAULT_CAPACITY_VA)
                ): int,
                vol.Required(
                    CONF_POWER_FACTOR,
                    default=opts.get(CONF_POWER_FACTOR, DEFAULT_POWER_FACTOR),
                ): vol.Coerce(float),
                vol.Required(
                    CONF_SCAN_INTERVAL,
                    default=opts.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                ): int,
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
