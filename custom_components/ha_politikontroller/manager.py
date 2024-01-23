"""Entity manager for generic Politikontroller events."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from politikontroller_py import Client
from politikontroller_py.models import PoliceControlResponse
from politikontroller_py.exceptions import AuthenticationError

from homeassistant.const import (
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_PASSWORD,
    CONF_RADIUS,
    CONF_USERNAME,
    UnitOfLength,
)
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.util import (
    dt as dt_util,
    location as loc_util,
)

from .const import (
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    SIGNAL_DELETE_ENTITY,
    SIGNAL_UPDATE_ENTITY,
    UPDATE_ERROR,
    UPDATE_OK,
    UPDATE_OK_NO_DATA,
)

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable
    from datetime import datetime

    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


class PolitikontrollerFeedManager:
    """Politikontroller Feed Manager."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: Client,
        generate_async_callback: Callable[[str], Awaitable[None]],
        update_async_callback: Callable[[str], Awaitable[None]],
        remove_async_callback: Callable[[str], Awaitable[None]],
        coordinates: tuple[float, float],
        filter_radius: float,
    ) -> None:
        """Initialise feed manager."""
        self.feed_entries: dict[str, PoliceControlResponse] = {}
        self._managed_external_ids = set()
        self._last_update = None
        self._last_update_successful = None
        self._hass = hass
        self._client = client
        self._coordinates = coordinates
        self._filter_radius = int(filter_radius)
        self._generate_async_callback = generate_async_callback
        self._update_async_callback = update_async_callback
        self._remove_async_callback = remove_async_callback

    async def update(self) -> None:
        """Update the feed and then update connected entities."""
        feed_entries = []
        error = None
        try:
            results = await self._client.get_controls_in_radius(
                lat=self._coordinates[0],
                lng=self._coordinates[1],
                radius=self._filter_radius,
            )
            _LOGGER.debug("Data retrieved %s", results)
            status = UPDATE_OK if len(results) > 0 else UPDATE_OK_NO_DATA
            feed_entries = await self._client.get_controls_from_lists(results)
        except Exception as err:  # noqa: BLE001
            status = UPDATE_ERROR
            error = str(err)

        # Record current time of update.
        self._last_update = dt_util.now()
        count_created = 0
        count_updated = 0
        count_removed = 0
        await self._store_feed_entries(status, feed_entries)
        if status == UPDATE_OK:
            # Record current time of update.
            self._last_update_successful = self._last_update
            # For entity management the external ids from the feed are used.
            feed_external_ids = set([str(entry.id) for entry in feed_entries])
            count_removed = await self._update_feed_remove_entries(feed_external_ids)
            count_updated = await self._update_feed_update_entries(feed_external_ids)
            count_created = await self._update_feed_create_entries(feed_external_ids)
        elif status == UPDATE_OK_NO_DATA:
            _LOGGER.debug("Update successful, but no data received")
            # Record current time of update.
            self._last_update_successful = self._last_update
        else:
            _LOGGER.warning("Update not successful, no data received. Error: %s", error)
            # Remove all entities.
            count_removed = await self._update_feed_remove_entries(set())
        # Send status update to subscriber.
        await self._status_update(count_created, count_updated, count_removed)

    async def _store_feed_entries(
        self,
        status: str,
        feed_entries: list[PoliceControlResponse] | None
    ) -> None:
        """Keep a copy of all feed entries for future lookups."""
        if feed_entries or status == UPDATE_OK_NO_DATA:
            if status == UPDATE_OK:
                self.feed_entries = {str(entry.id): entry for entry in feed_entries}
        else:
            self.feed_entries.clear()

    async def _update_feed_create_entries(self, feed_external_ids: set[str]) -> int:
        """Create entities after feed update."""
        create_external_ids = feed_external_ids.difference(self._managed_external_ids)
        count_created = len(create_external_ids)
        await self._generate_new_entities(create_external_ids)
        return count_created

    async def _update_feed_update_entries(self, feed_external_ids: set[str]) -> int:
        """Update entities after feed update."""
        update_external_ids = self._managed_external_ids.intersection(feed_external_ids)
        count_updated = len(update_external_ids)
        await self._update_entities(update_external_ids)
        return count_updated

    async def _update_feed_remove_entries(self, feed_external_ids: set[str]) -> int:
        """Remove entities after feed update."""
        remove_external_ids = self._managed_external_ids.difference(feed_external_ids)
        count_removed = len(remove_external_ids)
        await self._remove_entities(remove_external_ids)
        return count_removed

    async def _generate_new_entities(self, external_ids: set[str]) -> None:
        """Generate new entities for events using callback."""
        for external_id in external_ids:
            await self._generate_async_callback(external_id)
            _LOGGER.debug("New entity added %s", external_id)
            self._managed_external_ids.add(external_id)

    async def _update_entities(self, external_ids: set[str]) -> None:
        """Update entities using callback."""
        for external_id in external_ids:
            _LOGGER.debug("Existing entity found %s", external_id)
            await self._update_async_callback(external_id)

    async def _remove_entities(self, external_ids: set[str]) -> None:
        """Remove entities using callback."""
        for external_id in external_ids:
            _LOGGER.debug("Entity not current anymore %s", external_id)
            self._managed_external_ids.remove(external_id)
            await self._remove_async_callback(external_id)

    async def _status_update(
        self, count_created: int, count_updated: int, count_removed: int
    ) -> None:
        """Provide status update."""
        _LOGGER.debug("Update status: %d created, %d updated, %d removed", count_created, count_updated, count_removed)


class PolitikontrollerFeedEntityManager:
    """Feed Entity Manager for Politikontroller feeds."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the Politikontroller Feed Manager."""
        self._hass: HomeAssistant = hass
        self._client = Client()
        self._config = config_entry.data
        self.entry_id: str = config_entry.entry_id


        self._feed_manager = PolitikontrollerFeedManager(
            self._hass,
            self._client,
            self._generate_entity,
            self._update_entity,
            self._remove_entity,
            (
                self._config[CONF_LATITUDE],
                self._config[CONF_LONGITUDE],
            ),
            self._config[CONF_RADIUS],
        )

        self._track_time_remove_callback: Callable[[], None] | None = None
        self.listeners: list[Callable[[], None]] = []
        self.signal_new_entity: str = (
            f"{DOMAIN}_new_geolocation_{config_entry.entry_id}"
        )

    async def async_init(self) -> None:
        """Schedule initial and regular updates based on configured time interval."""

        async def update(event_time: datetime) -> None:
            """Update."""
            await self.async_update()

        # Trigger updates at regular intervals.
        self._track_time_remove_callback = async_track_time_interval(
            self._hass, update, DEFAULT_UPDATE_INTERVAL
        )

        # Authenticate
        try:
            await self._client.authenticate_user(
                username=self._config[CONF_USERNAME],
                password=self._config[CONF_PASSWORD],
            )
        except AuthenticationError as err:
            _LOGGER.exception("Error authenticating politikontroller account: %s", err)
            raise ConfigEntryAuthFailed from err

        _LOGGER.debug("Feed entity manager initialized")

    async def async_update(self) -> None:
        """Refresh data."""
        await self._feed_manager.update()
        _LOGGER.debug("Feed entity manager updated")

    async def async_stop(self) -> None:
        """Stop this feed entity manager from refreshing."""
        for unsub_dispatcher in self.listeners:
            unsub_dispatcher()
        self.listeners = []
        if self._track_time_remove_callback:
            self._track_time_remove_callback()
        _LOGGER.debug("Feed entity manager stopped")

    def get_entry(self, external_id: str) -> PoliceControlResponse | None:
        """Get feed entry by external id."""
        return self._feed_manager.feed_entries.get(external_id)

    def get_distance(self, external_id: str) -> float:
        """Get distance to feed entry."""
        entry = self.get_entry(external_id)
        return self._hass.config.units.length(
            loc_util.distance(self._hass.config.latitude, self._hass.config.longitude, entry.lat, entry.lng),
            UnitOfLength.METERS
        )

    async def _generate_entity(self, external_id: str) -> None:
        """Generate new entity."""
        async_dispatcher_send(
            self._hass,
            self.signal_new_entity,
            self,
            external_id,
        )

    async def _update_entity(self, external_id: str) -> None:
        """Update entity."""
        async_dispatcher_send(self._hass, SIGNAL_UPDATE_ENTITY.format(external_id))

    async def _remove_entity(self, external_id: str) -> None:
        """Remove entity."""
        async_dispatcher_send(self._hass, SIGNAL_DELETE_ENTITY.format(external_id))
