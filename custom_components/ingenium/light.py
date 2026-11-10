import logging
from typing import Any

from homeassistant.components.light import ColorMode, LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from ingeniumpy import IngeniumAPI
from ingeniumpy.objects import IngBusingRegulator, IngComponent

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
):
    """Set up Ingenium lights."""
    api: IngeniumAPI = hass.data[DOMAIN][entry.entry_id]

    lights = api.get_lights()
    _LOGGER.info("INGENIUM LIGHT: Total lights found: %s", len(lights))

    entities = []
    for item in lights:
        if isinstance(item, tuple):
            obj, comp = item
        else:
            obj, comp = item, getattr(item, "component", None)
        entities.append(IngRegulator(obj, comp))

    async_add_entities(entities)


class IngRegulator(LightEntity):
    """Ingenium dimmer/regulator."""

    def __init__(
        self,
        obj: IngBusingRegulator,
        comp: IngComponent,
    ):
        """Initialize the light."""
        self._obj = obj
        self._comp = comp

        self._attr_unique_id = f"{DOMAIN}.{comp.id}"
        self._attr_should_poll = False
        self._attr_supported_color_modes = {ColorMode.BRIGHTNESS}
        self._attr_color_mode = ColorMode.BRIGHTNESS

        if hasattr(comp, "add_update_notify"):
            comp.add_update_notify(self.async_schedule_update_ha_state)

    @property
    def _output(self) -> int:
        if self._comp and hasattr(self._comp, "output"):
            return self._comp.output
        comp = getattr(self._obj, "component", None)
        return getattr(comp, "output", 0) if comp else 0

    @property
    def name(self) -> str:
        """Return the name of the device."""
        if self._comp and hasattr(self._comp, "label"):
            return self._comp.label
        return getattr(self._obj, "components_label", "Light")

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._obj.available

    @property
    def brightness(self) -> int | None:
        """Return brightness (0-255)."""
        return self._obj.get_value(self._output)

    @property
    def is_on(self) -> bool:
        """Return True if light is on."""
        b = self.brightness
        return b is not None and b > 1

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the light."""
        value = kwargs.get("brightness", 255)
        await self._obj.set_value(self._output, value)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the light."""
        await self._obj.set_value(self._output, 0)
        self.async_write_ha_state()

    @property
    def device_info(self):
        """Return device information."""
        return self._obj.get_info()
