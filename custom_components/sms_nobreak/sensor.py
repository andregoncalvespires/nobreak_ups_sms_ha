"""Sensors for the SMS Nobreak (serial UPS) integration."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricPotential,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_CAPACITY_VA, CONF_POWER_FACTOR, DEFAULT_CAPACITY_VA, DEFAULT_POWER_FACTOR, DOMAIN
from .coordinator import SmsNobreakCoordinator
from .protocol import UpsStatus


@dataclass(frozen=True, kw_only=True)
class SmsSensorDescription(SensorEntityDescription):
    value_fn: Callable[[UpsStatus], float | None] = lambda status: None


SENSOR_TYPES: tuple[SmsSensorDescription, ...] = (
    SmsSensorDescription(
        key="last_input_vac",
        translation_key="last_input_vac",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda s: s.last_input_vac,
    ),
    SmsSensorDescription(
        key="input_vac",
        translation_key="input_vac",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda s: s.input_vac,
    ),
    SmsSensorDescription(
        key="output_vac",
        translation_key="output_vac",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda s: s.output_vac,
    ),
    SmsSensorDescription(
        key="output_power_percent",
        translation_key="output_power_percent",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda s: s.output_power_percent,
    ),
    SmsSensorDescription(
        key="output_hz",
        translation_key="output_hz",
        device_class=SensorDeviceClass.FREQUENCY,
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda s: s.output_hz,
    ),
    SmsSensorDescription(
        key="battery_level",
        translation_key="battery_level",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda s: s.battery_level,
    ),
    SmsSensorDescription(
        key="temperature_c",
        translation_key="temperature_c",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda s: s.temperature_c,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: SmsNobreakCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = [
        SmsSensor(coordinator, entry, description) for description in SENSOR_TYPES
    ]
    entities.append(SmsOutputPowerWattsSensor(coordinator, entry))
    async_add_entities(entities)


class SmsSensor(CoordinatorEntity[SmsNobreakCoordinator], SensorEntity):
    entity_description: SmsSensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SmsNobreakCoordinator,
        entry: ConfigEntry,
        description: SmsSensorDescription,
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
    def native_value(self) -> float | None:
        if self.coordinator.data is None:
            return None
        return self.entity_description.value_fn(self.coordinator.data)


class SmsOutputPowerWattsSensor(CoordinatorEntity[SmsNobreakCoordinator], SensorEntity):
    """Estimated output power in watts, derived from % load, capacity (VA) and power factor.

    Mirrors the original flow's `(load% / 100) * capacity_va * power_factor`
    calculation, with capacity_va and power_factor configurable per-device
    via the options flow instead of a hardcoded flow variable.
    """

    _attr_has_entity_name = True
    _attr_translation_key = "output_power_watts"
    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: SmsNobreakCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_output_power_watts"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="SMS",
        )

    @property
    def native_value(self) -> float | None:
        status = self.coordinator.data
        if status is None:
            return None
        capacity_va = self._entry.options.get(CONF_CAPACITY_VA, DEFAULT_CAPACITY_VA)
        power_factor = self._entry.options.get(CONF_POWER_FACTOR, DEFAULT_POWER_FACTOR)
        return round((status.output_power_percent / 100) * capacity_va * power_factor, 2)
