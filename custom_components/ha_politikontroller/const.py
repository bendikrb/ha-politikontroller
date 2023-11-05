"""Define constants for the Politikontroller events integration."""
from __future__ import annotations

from datetime import timedelta
from typing import Final

from homeassistant.const import Platform

DOMAIN: Final = "ha_politikontroller"

PLATFORMS: Final = [Platform.GEO_LOCATION]

ATTR_DESCRIPTION: Final = "description"
ATTR_DETAILS: Final = "details"
ATTR_DISTANCE: Final = "distance"
ATTR_EXTERNAL_ID: Final = "external_id"
ATTR_SOURCE: Final = "source"
ATTR_TYPE: Final = "type"
CONF_TYPE_FILTER: Final = "type_filter"
DEFAULT_RADIUS_IN_KM: Final = 20.0
DEFAULT_RADIUS_IN_M: Final = 20000.0
DEFAULT_UPDATE_INTERVAL: Final = timedelta(seconds=300)
ATTRIBUTION: Final = "politikontroller.no"

SIGNAL_DELETE_ENTITY: Final = "ha_politikontroller_delete_{}"
SIGNAL_UPDATE_ENTITY: Final = "ha_politikontroller_update_{}"

UPDATE_OK = "OK"
UPDATE_OK_NO_DATA = "OK_NO_DATA"
UPDATE_ERROR = "ERROR"
