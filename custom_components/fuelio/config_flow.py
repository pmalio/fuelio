"""Config flow for Fuelio."""
from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries

from .const import (
    CONF_FILE_PATH,
    CONF_SCAN_INTERVAL,
    DEFAULT_FILE_PATH,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)
from .parser import parse_fuelio_csv


class FuelioConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            path = user_input[CONF_FILE_PATH]
            try:
                parsed = await self.hass.async_add_executor_job(parse_fuelio_csv, path)
            except Exception:
                errors["base"] = "cannot_read_file"
            else:
                await self.async_set_unique_id(path)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=parsed.get("vehicle_name") or "Fuelio",
                    data=user_input,
                )

        schema = vol.Schema({
            vol.Required(CONF_FILE_PATH, default=DEFAULT_FILE_PATH): str,
            vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
                vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL)
            ),
        })
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
