import logging
from typing import Any

from homeassistant.components.cover import (
    ATTR_POSITION,
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from ingeniumpy import IngeniumAPI
from ingeniumpy.objects import IngActuator, IngComponent

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up Ingenium covers."""
    api: IngeniumAPI = hass.data[DOMAIN][entry.entry_id]

    covers = api.get_covers()
    _LOGGER.info("INGENIUM COVER: Total covers found: %s", len(covers))

    entities = []
    for item in covers:
        if isinstance(item, tuple):
            obj, comp = item
        else:
            obj, comp = item, getattr(item, "component", None)
        entities.append(IngCover(obj, comp))

    async_add_entities(entities)


class IngCover(CoverEntity):
    """Representation of an Ingenium Cover."""

    def __init__(self, obj: IngActuator, comp: IngComponent):
        """Initialize the cover."""
        self._obj = obj
        self._comp = comp

        self._attr_unique_id = f"{DOMAIN}.{comp.id}"
        self._attr_device_class = CoverDeviceClass.BLIND
        self._attr_supported_features = (
            CoverEntityFeature.OPEN
            | CoverEntityFeature.CLOSE
            | CoverEntityFeature.SET_POSITION
        )
        self._attr_should_poll = False

        if hasattr(comp, "add_update_notify"):
            comp.add_update_notify(self.async_schedule_update_ha_state)

    @property
    def name(self) -> str:
        """Name of the device."""
        if self._comp and hasattr(self._comp, "label"):
            return self._comp.label
        return getattr(self._obj, "components_label", "Cover")

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._obj.available

    @property
    def current_cover_position(self) -> int | None:
        """Return current position of cover. 0 is closed, 100 is fully open."""
        try:
            return self._obj.get_cover_val(self._comp)
        except TypeError:
            return self._obj.get_cover_val()

    @property
    def is_closed(self) -> bool | None:
        """Return True if cover is closed."""
        pos = self.current_cover_position
        if pos is None:
            return None
        return pos == 0

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        try:
            await self._obj.set_cover_val(self._comp, 100)
        except TypeError:
            await self._obj.set_cover_val(100)
        self.async_write_ha_state()

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the cover."""
        try:
            await self._obj.set_cover_val(self._comp, 0)
        except TypeError:
            await self._obj.set_cover_val(0)
        self.async_write_ha_state()

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Move the cover to a specific position."""
        pos = kwargs[ATTR_POSITION]
        try:
            await self._obj.set_cover_val(self._comp, pos)
        except TypeError:
            await self._obj.set_cover_val(pos)
        self.async_write_ha_state()

    @property
    def device_info(self):
        """Return device information."""
        return self._obj.get_info()
