"""Fuelio integration."""
from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_FILE_PATH, CONF_SCAN_INTERVAL, DOMAIN, PLATFORMS
from .parser import parse_fuelio_csv

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    file_path = entry.data[CONF_FILE_PATH]
    scan_interval = int(entry.data.get(CONF_SCAN_INTERVAL, 5))

    async def async_update_data():
        try:
            return await hass.async_add_executor_job(parse_fuelio_csv, file_path)
        except Exception as err:
            raise UpdateFailed(f"Nie można odczytać eksportu Fuelio: {err}") from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="Fuelio",
        update_method=async_update_data,
        update_interval=timedelta(minutes=scan_interval),
    )
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
