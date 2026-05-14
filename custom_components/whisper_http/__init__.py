"""Init for Whisper HTTP STT integration."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.STT]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Whisper HTTP STT from a config entry."""
    _LOGGER.warning("async_setup_entry called for entry %s", entry.entry_id)
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data | entry.options
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Reload the STT entity when options are changed
    entry.async_on_unload(entry.add_update_listener(async_update_listener))
    return True


async def async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update — reload STT entity."""
    _LOGGER.warning("async_update_listener: reloading STT for entry %s", entry.entry_id)
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
