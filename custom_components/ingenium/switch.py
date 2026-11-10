import logging
from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from ingeniumpy import IngeniumAPI
from ingeniumpy.objects import IngActuator, IngComponent

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    """Set up switch devices."""
    api: IngeniumAPI = hass.data[DOMAIN][entry.entry_id]

    switches = api.get_switches()

    _LOGGER.info("INGENIUM SWITCH: Total switches found: %s", len(switches))

    entities = []
    for item in switches:
        if isinstance(item, tuple):
            obj, comp = item
        else:
            obj, comp = item, getattr(item, "component", None)

        entities.append(IngSwitch(obj, comp))

    async_add_entities(entities)


class IngSwitch(SwitchEntity):
    """Representation of an Ingenium Switch."""

    def __init__(self, obj: IngActuator, comp: IngComponent):
        """Initialize the switch."""
        self._obj = obj
        self._comp = comp

        self._attr_unique_id = f"{DOMAIN}.{comp.id}"
        self._attr_should_poll = False

        if hasattr(comp, "add_update_notify"):
            comp.add_update_notify(self.async_schedule_update_ha_state)

    @property
    def name(self) -> str:
        """Return the name of the device."""
        if self._comp and hasattr(self._comp, "label"):
            return self._comp.label
        return getattr(self._obj, "components_label", "Switch")

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._obj.available

    @property
    def is_on(self) -> bool:
        """Return True if switch is on."""
        try:
            return self._obj.get_switch_val(self._comp)
        except TypeError:
            return self._obj.get_switch_val()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        if not self.is_on:
            try:
                await self._obj.action_switch(self._comp)
            except TypeError:
                await self._obj.action_switch()
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        if self.is_on:
            try:
                await self._obj.action_switch(self._comp)
            except TypeError:
                await self._obj.action_switch()
        self.async_write_ha_state()

    @property
    def device_class(self) -> SwitchDeviceClass | None:
        """Return the device class."""
        if getattr(self._obj, "consumption", -1) != -1:
            return SwitchDeviceClass.OUTLET
        return SwitchDeviceClass.SWITCH

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the extra state attributes."""
        attrs = {}
        if getattr(self._obj, "consumption", -1) != -1 and getattr(self._obj, "voltage", -1) == -1:
            attrs["power"] = self._obj.consumption
        if getattr(self._obj, "voltage", -1) != -1 and getattr(self._obj, "current", -1) != -1:
            attrs["current"] = self._obj.current
        if getattr(self._obj, "voltage", -1) != -1:
            attrs["voltage"] = self._obj.voltage
        if getattr(self._obj, "active_power", -1) != -1:
            attrs["active_power"] = self._obj.active_power
        return attrs

    @property
    def device_info(self):
        """Return device information."""
        return self._obj.get_info()
