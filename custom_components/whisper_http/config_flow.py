"""Config flow for Whisper HTTP STT integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_HOST,
    CONF_LANGUAGE,
    CONF_PORT,
    DEFAULT_HOST,
    DEFAULT_LANGUAGE,
    DEFAULT_PORT,
    DOMAIN,
    SUPPORTED_LANGUAGES,
)

_LOGGER = logging.getLogger(__name__)


class WhisperHTTPConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Whisper HTTP STT."""

    VERSION = 1

    async def _try_connect(self, host: str, port: int) -> bool:
        """Test if the Whisper server is reachable."""
        from homeassistant.helpers.aiohttp_client import async_get_clientsession

        session = async_get_clientsession(self.hass)
        url = f"http://{host}:{port}/v1/models"
        try:
            async with session.get(url, timeout=5) as resp:
                return resp.status == 200
        except Exception:
            return False

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]

            if not await self._try_connect(host, port):
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(f"{host}_{port}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"{host}:{port}",
                    data={
                        CONF_HOST: host,
                        CONF_PORT: port,
                    },
                    options={
                        CONF_LANGUAGE: DEFAULT_LANGUAGE,
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default=DEFAULT_HOST): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Create the options flow."""
        return WhisperHTTPOptionsFlow()


class WhisperHTTPOptionsFlow(config_entries.OptionsFlow):
    """Handle options for Whisper HTTP STT."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Handle the options step."""

        current_language = self.config_entry.options.get(CONF_LANGUAGE, DEFAULT_LANGUAGE)

        schema = vol.Schema(
            {
                vol.Optional(CONF_LANGUAGE, default=current_language): vol.In(
                    SUPPORTED_LANGUAGES
                ),
            }
        )

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(step_id="init", data_schema=schema)
