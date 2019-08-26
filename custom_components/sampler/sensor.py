"""Samples another entity on a regular basis."""

from datetime import timedelta
import logging
import voluptuous as vol

from homeassistant.core import callback
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_ICON,
    ATTR_UNIT_OF_MEASUREMENT,
    CONF_ENTITY_ID,
    CONF_MODE,
    CONF_NAME,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import async_track_state_change, async_track_time_interval
from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)
ATTR_INTERVAL = "interval"
ATTR_MODE = "mode"
CONF_INTERVAL = "interval"
CONF_BOOST = "boost"            # Fire change at least every interval but also if underlying value changes
CONF_REGULATE = "regulate"      # Fire change exactly at interval
CONF_THROTTLE = "throttle"      # Fire change at most every interval, but less if underlying value hasn't changed
ICON = "mdi:chart-line-variant"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_ENTITY_ID): cv.entity_id,
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional(CONF_MODE, default=CONF_REGULATE): vol.In([CONF_THROTTLE, CONF_REGULATE, CONF_BOOST]),
        vol.Required(CONF_INTERVAL, default=60): cv.positive_int
    }
)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the template sensors."""
    name = config.get(CONF_NAME)
    entity_id = config.get(CONF_ENTITY_ID)
    mode = config.get(CONF_MODE)
    interval = config.get(CONF_INTERVAL)

    _LOGGER.debug("Adding sampler %s for %s, %s every %s seconds", name, entity_id, mode, interval)
    async_add_entities([Sampler(name, entity_id, mode, interval)])

class Sampler(Entity):
    """Representation of a Sampler Sensor, which provides control over how frequently we sample the state of another entity."""

    def __init__(self, name, entity_id, mode, interval):
        """Initialize the sensor."""
        self._name = name
        self._entity = entity_id
        self._mode = mode
        self._interval_secs = interval
        self._interval = timedelta(seconds=interval)
        self._unit_of_measurement = None
        self._state = None
        self._icon = None
        self._last_published = dt_util.utcnow()
        self._last_value = None

    async def async_added_to_hass(self):
        """Register callbacks."""

        @callback
        def sensor_state_listener(entity, old_state, new_state):
            """Handle device state changes."""
            _LOGGER.debug("%s received new state for %s: %s", self._name, self._entity, new_state.state)
            if new_state.state in [STATE_UNKNOWN, STATE_UNAVAILABLE]:
                return

            self._state = new_state.state

            if self._icon is None:
                self._icon = new_state.attributes.get(ATTR_ICON, ICON)

            if self._unit_of_measurement is None:
                self._unit_of_measurement = new_state.attributes.get(
                    ATTR_UNIT_OF_MEASUREMENT
                )

            self.async_handle_callbacks(False)

        def timer_callback(event_time):
            _LOGGER.debug("%s received timer callback.", self._name)
            self.async_handle_callbacks(True)

        _LOGGER.debug("Setting up sampler %s for %s every %s seconds", self._name, self._entity, self._interval_secs)
        async_track_state_change(self.hass, self._entity, sensor_state_listener)
        async_track_time_interval(self.hass, timer_callback, self._interval)

    def async_handle_callbacks(self, from_timer):
        """Handle callbacks either from timer or from value changing."""
        publish = False
        now = dt_util.utcnow()
        if self._mode == CONF_REGULATE:
            # Only publish on timer callback
            publish = from_timer
        elif self._mode == CONF_BOOST:
            # Publish both when the value changes and on timer callback
            publish = True
        else:
            # Throttle ony publishes if the value has changed, and we've not already published recently
            if now >= self._last_published + self._interval and self._state != self._last_value:
                publish = True
        
        if publish:
            _LOGGER.debug("%s publishing state.", self._name)
            self._last_published = now
            self._last_value = self._state
            self.async_schedule_update_ha_state()

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def icon(self):
        """Return the icon to use in the frontend, if any."""
        return self._icon

    @property
    def unit_of_measurement(self):
        """Return the unit_of_measurement of the device."""
        return self._unit_of_measurement

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def force_update(self) -> bool:
        """Return True if state updates should be forced.
        If True, a state change will be triggered anytime the state property is
        updated, not just when the value changes.
        """
        return True

    @property
    def device_state_attributes(self):
        """Return the state attributes of the sensor."""
        state_attr = {ATTR_ENTITY_ID: self._entity, ATTR_MODE: self._mode, ATTR_INTERVAL: self._interval_secs}
        return state_attr
