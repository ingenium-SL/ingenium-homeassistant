import logging
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONCENTRATION_PARTS_PER_MILLION,
    PERCENTAGE,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.restore_state import RestoreEntity

from ingeniumpy import IngeniumAPI
from ingeniumpy.objects import (
    IngAirSensor,
    IngComponent,
    IngMeterBus,
    IngSif,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up Ingenium sensor devices."""
    api: IngeniumAPI = hass.data[DOMAIN][entry.entry_id]

    entities = []

    # Meterbuses
    for item in api.get_meterbuses():
        if len(item) == 3:
            o, c, i = item
        else:
            o, i = item
            c = getattr(o, "component", None)
        entities.append(MeterBusSensor(o, c, i))

    # SIFs
    for item in api.get_sifs():
        if len(item) == 3:
            o, c, i = item
        else:
            o, i = item
            c = getattr(o, "component", None)
        entities.append(SifSensor(o, c, i))

    # Air sensors (CO2 and VOCs)
    for item in api.get_air_sensors():
        if len(item) == 3:
            o, c, i = item
        else:
            o, i = item
            c = getattr(o, "component", None)
        # Register CO2 (0) and VOCs (1)
        if i in (0, 1):
            entities.append(AirSensor(o, c, i))

    _LOGGER.info("INGENIUM SENSOR: Total sensors found: %s", len(entities))
    async_add_entities(entities)


class MeterBusSensor(RestoreEntity, SensorEntity):
    """Representation of an Ingenium MeterBus sensor."""

    def __init__(self, obj: IngMeterBus, comp: IngComponent, channel: int):
        """Initialize the sensor."""
        self._obj = obj
        self._comp = comp
        self._channel = channel

        comp_id = comp.id if comp else getattr(getattr(obj, "component", None), "id", f"mb_{obj.address}")
        comp_label = comp.label if comp else getattr(obj, "components_label", "MeterBus")

        self._attr_unique_id = f"{DOMAIN}.{comp_id}_C{channel}"
        self._attr_name = f"{comp_label} C{channel}"
        self._attr_native_unit_of_measurement = UnitOfPower.WATT
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_should_poll = False

        if comp and hasattr(comp, "add_update_notify"):
            comp.add_update_notify(self.async_schedule_update_ha_state)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._obj.get_available(self._channel)

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if hasattr(self._obj, "get_cons"):
            return self._obj.get_cons(self._channel)
        return self._obj.get_value(self._channel)

    @property
    def device_info(self):
        """Return device information."""
        return self._obj.get_info()


class SifSensor(RestoreEntity, SensorEntity):
    """Representation of an Ingenium SIF multi-sensor."""

    def __init__(self, obj: IngSif, comp: IngComponent, mode: int):
        """Initialize the sensor."""
        self._obj = obj
        self._comp = comp
        self._mode = mode

        modes_names = ["T", "S", "P", "L", "H"]
        suffix = modes_names[mode] if 0 <= mode < len(modes_names) else str(mode)

        comp_id = comp.id if comp else getattr(getattr(obj, "component", None), "id", f"sif_{obj.address}")
        comp_label = comp.label if comp else getattr(obj, "components_label", "SIF")

        self._attr_unique_id = f"{DOMAIN}.{comp_id}_{suffix}"
        self._attr_name = f"{comp_label} {suffix}"
        self._attr_should_poll = False

        units = [
            UnitOfTemperature.CELSIUS,
            None,
            "Detected",
            "lx",
            PERCENTAGE,
        ]
        self._attr_native_unit_of_measurement = units[mode] if 0 <= mode < len(units) else None

        classes = [
            SensorDeviceClass.TEMPERATURE,
            None,
            None,
            SensorDeviceClass.ILLUMINANCE,
            SensorDeviceClass.HUMIDITY,
        ]
        self._attr_device_class = classes[mode] if 0 <= mode < len(classes) else None

        if comp and hasattr(comp, "add_update_notify"):
            comp.add_update_notify(self.async_schedule_update_ha_state)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._obj.get_available(self._mode)

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        return self._obj.get_value(self._mode)

    @property
    def device_info(self):
        """Return device information."""
        return self._obj.get_info()


class AirSensor(RestoreEntity, SensorEntity):
    """Representation of an Ingenium Air Quality sensor."""

    def __init__(self, obj: IngAirSensor, comp: IngComponent, mode: int):
        """Initialize the sensor."""
        self._obj = obj
        self._comp = comp
        self._mode = mode

        name_suffix = "CO2" if mode == 0 else "VOCs"
        suffix = "co2" if mode == 0 else "vocs"

        comp_id = comp.id if comp else getattr(getattr(obj, "component", None), "id", f"air_{obj.address}")
        comp_label = comp.label if comp else getattr(obj, "components_label", "Air Quality")

        self._attr_unique_id = f"{DOMAIN}.{comp_id}_{suffix}"
        self._attr_name = f"{comp_label} {name_suffix}"
        self._attr_native_unit_of_measurement = CONCENTRATION_PARTS_PER_MILLION
        self._attr_device_class = (
            SensorDeviceClass.CO2 if mode == 0 else SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS_PARTS
        )
        self._attr_should_poll = False

        if comp and hasattr(comp, "add_update_notify"):
            comp.add_update_notify(self.async_schedule_update_ha_state)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._obj.get_available(self._mode)

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        return self._obj.get_value(self._mode)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        return {
            "threshold": self._obj.get_threshold(self._mode),
        }

    @property
    def device_info(self):
        """Return device information."""
        return self._obj.get_info()
