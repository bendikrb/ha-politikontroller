"""The Politikontroller events component."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.const import Platform
from homeassistant.helpers.entity_registry import (
    async_entries_for_config_entry,
    async_get,
)

from .const import DOMAIN, PLATFORMS, URL_BASE
from .manager import PolitikontrollerFeedEntityManager
from .static import locate_dir

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up the Politikontroller events component as config entry."""
    feeds = hass.data.setdefault(DOMAIN, {})
    # Create feed entity manager for all platforms.
    entity_manager = PolitikontrollerFeedEntityManager(hass, config_entry)
    feeds[config_entry.entry_id] = entity_manager
    _LOGGER.debug("Feed entity manager added for %s", config_entry.entry_id)
    await remove_orphaned_entities(hass, config_entry.entry_id)
    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)
    await entity_manager.async_init()

    static_path = locate_dir()
    hass.http.register_static_path(
        f"{URL_BASE}/img",
        f"{static_path}/img",
    )
    return True


async def remove_orphaned_entities(hass: HomeAssistant, entry_id: str) -> None:
    """Remove orphaned geo_location entities.

    This is needed because when fetching data from the external feed this integration is
    determining which entities need to be added, updated or removed by comparing the
    current with the previous data. After a restart of Home Assistant the integration
    has no previous data to compare against, and thus all entities managed by this
    integration are removed after startup.
    """
    entity_registry = async_get(hass)
    orphaned_entries = async_entries_for_config_entry(entity_registry, entry_id)
    if orphaned_entries is not None:
        for entry in orphaned_entries:
            if entry.domain == Platform.GEO_LOCATION:
                _LOGGER.debug("Removing orphaned entry %s", entry.entity_id)
                entity_registry.async_remove(entry.entity_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload the Politikontroller events config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        entity_manager: PolitikontrollerFeedEntityManager = hass.data[DOMAIN].pop(entry.entry_id)
        await entity_manager.async_stop()
    return unload_ok
