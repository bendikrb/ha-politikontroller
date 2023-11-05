"""Support for generic Politikontroller events."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.geo_location import GeolocationEvent
from homeassistant.const import UnitOfLength
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
import homeassistant.util.dt as dt_util

from .const import (
    ATTR_DESCRIPTION,
    ATTR_DETAILS,
    ATTR_EXTERNAL_ID,
    ATTR_TYPE,
    ATTRIBUTION,
    DOMAIN,
    SIGNAL_DELETE_ENTITY,
    SIGNAL_UPDATE_ENTITY,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from politikontroller_py.models import PoliceControl

    from homeassistant.config_entries import ConfigEntry
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from . import PolitikontrollerFeedEntityManager

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Politikontroller Events platform."""
    manager: PolitikontrollerFeedEntityManager = hass.data[DOMAIN][entry.entry_id]

    @callback
    def async_add_geolocation(
        feed_manager: PolitikontrollerFeedEntityManager,
        external_id: str,
    ) -> None:
        """Add geolocation entity from feed."""
        new_entity = PolitikontrollerEvent(feed_manager, external_id)
        _LOGGER.debug("Adding geolocation %s", new_entity)
        async_add_entities([new_entity], update_before_add=True)

    manager.listeners.append(
        async_dispatcher_connect(hass, manager.signal_new_entity, async_add_geolocation)
    )
    # Do not wait for update here so that the setup can be completed and because an
    # update will fetch data from the feed via HTTP and then process that data.
    entry.async_create_task(hass, manager.async_update())
    _LOGGER.debug("Geolocation setup done")


class PolitikontrollerEvent(GeolocationEvent):
    """Represents a Politikontroller event with GeoJSON data."""

    _attr_should_poll = False
    _attr_source = DOMAIN
    _attr_unit_of_measurement = UnitOfLength.KILOMETERS
    _attr_attribution = ATTRIBUTION
    _attr_type: str | None = None
    _attr_description: str | None = None
    _attr_confirmed: bool = False
    _attr_feed_entry: dict | None = None
    _attr_last_updated_ts: str | None = None

    def __init__(
        self,
        feed_manager: PolitikontrollerFeedEntityManager,
        external_id: str,
    ) -> None:
        """Initialize entity with data from feed entry."""
        self._feed_manager: PolitikontrollerFeedEntityManager = feed_manager
        self._external_id = external_id
        self._attr_unique_id = f"{feed_manager.entry_id}_{external_id}"
        self._remove_signal_delete: Callable[[], None] | None = None
        self._remove_signal_update: Callable[[], None] | None = None

    async def async_added_to_hass(self) -> None:
        """Call when entity is added to hass."""
        self._remove_signal_delete = async_dispatcher_connect(
            self.hass,
            SIGNAL_DELETE_ENTITY.format(self._external_id),
            self._delete_callback,
        )
        self._remove_signal_update = async_dispatcher_connect(
            self.hass,
            SIGNAL_UPDATE_ENTITY.format(self._external_id),
            self._update_callback,
        )

    @callback
    def _delete_callback(self) -> None:
        """Remove this entity."""
        self._remove_signal_delete()
        self._remove_signal_update()
        self.hass.async_create_task(self.async_remove(force_remove=True))

    @callback
    def _update_callback(self) -> None:
        """Call update method."""
        self.async_schedule_update_ha_state(force_refresh=True)

    async def async_update(self) -> None:
        """Update this entity from the data held in the feed manager."""
        _LOGGER.debug("Updating %s", self._external_id)
        feed_entry = self._feed_manager.get_entry(self._external_id)
        if feed_entry:
            self._update_from_feed(feed_entry)

    def _update_from_feed(self, feed_entry: PoliceControl) -> None:
        """Update the internal state from the provided feed entry."""
        self._attr_name = feed_entry.title
        self._attr_latitude = feed_entry.lat
        self._attr_longitude = feed_entry.lng
        self._attr_distance = self._feed_manager.get_distance(self._external_id)
        self._attr_type = feed_entry.type.value
        last_updated = feed_entry.last_seen or feed_entry.timestamp
        if last_updated:
            self._attr_last_updated_ts = dt_util.as_local(last_updated).isoformat(timespec="seconds")

        self._attr_extra_state_attributes = {
            ATTR_TYPE: feed_entry.type.name,
            ATTR_DESCRIPTION: feed_entry.description,
            ATTR_DETAILS: feed_entry.dict(),
        }

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the device state attributes."""
        if not self._external_id:
            return {}
        return {
            ATTR_EXTERNAL_ID: self._external_id,
            ATTR_TYPE: self._attr_type,
            ATTR_DESCRIPTION: self._attr_description,
        }
