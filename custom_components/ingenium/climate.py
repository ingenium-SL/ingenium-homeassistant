import logging
from typing import Any

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant

from ingeniumpy import IngeniumAPI
from ingeniumpy.objects import IngComponent, IngThermostat

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up Ingenium climate devices."""
    api: IngeniumAPI = hass.data[DOMAIN][entry.entry_id]

    climates = api.get_climates()
    _LOGGER.info("INGENIUM CLIMATE: Total climates found: %s", len(climates))

    entities = []
    for item in climates:
        if isinstance(item, tuple):
            obj, comp = item
        else:
            obj, comp = item, getattr(item, "component", None)
        entities.append(IngClimate(obj, comp))

    async_add_entities(entities)


class IngClimate(ClimateEntity):
    """Representation of an Ingenium Climate entity."""

    def __init__(self, obj: IngThermostat, comp: IngComponent):
        """Initialize the climate entity."""
        self._obj = obj
        self._comp = comp

        self._attr_unique_id = f"{DOMAIN}.{comp.id}"
        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_precision = 0.2
        self._attr_max_temp = 51.0
        self._attr_min_temp = 0.0
        self._attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
        self._attr_hvac_modes = [
            HVACMode.OFF,
            HVACMode.HEAT,
            HVACMode.COOL,
            HVACMode.HEAT_COOL,
        ]
        self._attr_should_poll = False

        if hasattr(comp, "add_update_notify"):
            comp.add_update_notify(self.async_schedule_update_ha_state)

    @property
    def name(self) -> str:
        """Name of the device."""
        if self._comp and hasattr(self._comp, "label"):
            return self._comp.label
        return getattr(self._obj, "components_label", "Thermostat")

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._obj.available

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        return self._obj.temp

    @property
    def current_humidity(self) -> float | None:
        """Return the current humidity."""
        return getattr(self._obj, "humidity", None)

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature."""
        return self._obj.set_point

    @property
    def hvac_mode(self) -> HVACMode:
        """Return the current HVAC mode."""
        mode_idx = self._obj.get_mode()
        if 0 <= mode_idx < len(self._attr_hvac_modes):
            return self._attr_hvac_modes[mode_idx]
        return HVACMode.OFF

    @property
    def hvac_action(self) -> HVACAction:
        """Return the current HVAC action."""
        action_idx = self._obj.get_action()
        actions = [
            HVACAction.OFF,
            HVACAction.HEATING,
            HVACAction.COOLING,
        ]
        if 0 <= action_idx < len(actions):
            return actions[action_idx]
        return HVACAction.OFF

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target HVAC mode."""
        if hvac_mode in self._attr_hvac_modes:
            await self._obj.set_mode(self._attr_hvac_modes.index(hvac_mode))
        self.async_write_ha_state()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        if ATTR_TEMPERATURE in kwargs:
            await self._obj.set_temp(kwargs[ATTR_TEMPERATURE])
        self.async_write_ha_state()

    @property
    def device_info(self):
        """Return device information."""
        return self._obj.get_info()
