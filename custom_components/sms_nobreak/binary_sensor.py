"""Binary sensors for the SMS Nobreak (serial UPS) integration."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SmsNobreakCoordinator
from .protocol import UpsStatus


@dataclass(frozen=True, kw_only=True)
class SmsBinarySensorDescription(BinarySensorEntityDescription):
    value_fn: Callable[[UpsStatus], bool | None] = lambda status: None


BINARY_SENSOR_TYPES: tuple[SmsBinarySensorDescription, ...] = (
    SmsBinarySensorDescription(
        key="battery_in_use",
        translation_key="battery_in_use",
        device_class=BinarySensorDeviceClass.BATTERY,
        value_fn=lambda s: s.battery_in_use,
    ),
    SmsBinarySensorDescription(
        key="battery_low",
        translation_key="battery_low",
        device_class=BinarySensorDeviceClass.BATTERY,
        value_fn=lambda s: s.battery_low,
    ),
    SmsBinarySensorDescription(
        key="bypass",
        translation_key="bypass",
        value_fn=lambda s: s.bypass,
    ),
    SmsBinarySensorDescription(
        key="boost",
        translation_key="boost",
        value_fn=lambda s: s.boost,
    ),
    SmsBinarySensorDescription(
        key="ups_ok",
        translation_key="ups_ok",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda s: not s.ups_ok,
    ),
    SmsBinarySensorDescription(
        key="test_active",
        translation_key="test_active",
        value_fn=lambda s: s.test_active,
    ),
    SmsBinarySensorDescription(
        key="shutdown_active",
        translation_key="shutdown_active",
        value_fn=lambda s: s.shutdown_active,
    ),
    SmsBinarySensorDescription(
        key="beep_on",
        translation_key="beep_on",
        value_fn=lambda s: s.beep_on,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: SmsNobreakCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        SmsBinarySensor(coordinator, entry, description) for description in BINARY_SENSOR_TYPES
    )


class SmsBinarySensor(CoordinatorEntity[SmsNobreakCoordinator], BinarySensorEntity):
    entity_description: SmsBinarySensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SmsNobreakCoordinator,
        entry: ConfigEntry,
        description: SmsBinarySensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="SMS",
        )

    @property
    def is_on(self) -> bool | None:
        if self.coordinator.data is None:
            return None
        return self.entity_description.value_fn(self.coordinator.data)
