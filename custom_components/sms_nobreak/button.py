"""Buttons for the SMS Nobreak (serial UPS) integration."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import serial

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import SmsNobreakApi, SmsNobreakCoordinator


@dataclass(frozen=True, kw_only=True)
class SmsButtonDescription(ButtonEntityDescription):
    press_fn: Callable[[SmsNobreakApi], None]


BUTTON_TYPES: tuple[SmsButtonDescription, ...] = (
    SmsButtonDescription(
        key="start_test_10s",
        translation_key="start_test_10s",
        press_fn=lambda api: api.start_test_10s(),
    ),
    SmsButtonDescription(
        key="start_test_5m",
        translation_key="start_test_5m",
        press_fn=lambda api: api.start_test_5m(),
    ),
    SmsButtonDescription(
        key="start_test_until_low",
        translation_key="start_test_until_low",
        press_fn=lambda api: api.start_test_until_low(),
    ),
    SmsButtonDescription(
        key="stop_test",
        translation_key="stop_test",
        press_fn=lambda api: api.stop_test(),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: SmsNobreakCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        SmsButton(coordinator, entry, description) for description in BUTTON_TYPES
    )


class SmsButton(ButtonEntity):
    entity_description: SmsButtonDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SmsNobreakCoordinator,
        entry: ConfigEntry,
        description: SmsButtonDescription,
    ) -> None:
        self._coordinator = coordinator
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="SMS",
        )

    async def async_press(self) -> None:
        try:
            await self.hass.async_add_executor_job(
                self.entity_description.press_fn, self._coordinator.api
            )
        except serial.SerialException as err:
            raise HomeAssistantError(
                f"Falha ao enviar o comando para o nobreak (porta serial): {err}"
            ) from err
        await self._coordinator.async_request_refresh()
