"""Config flow for Whisper HTTP STT integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    AVAILABLE_MODELS,
    CONF_HOST,
    CONF_LANGUAGE,
    CONF_MODEL,
    CONF_PORT,
    DEFAULT_HOST,
    DEFAULT_LANGUAGE,
    DEFAULT_MODEL,
    DEFAULT_PORT,
    DOMAIN,
    SUPPORTED_LANGUAGES,
)

_LOGGER = logging.getLogger(__name__)


class WhisperHTTPConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Whisper HTTP STT."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            _LOGGER.warning(
                "Config flow step_user: host=%s port=%s",
                user_input.get(CONF_HOST),
                user_input.get(CONF_PORT),
            )
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]
            await self.async_set_unique_id(f"{host}_{port}")
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=f"{host}:{port}",
                data={
                    CONF_HOST: host,
                    CONF_PORT: port,
                },
                options={
                    CONF_MODEL: DEFAULT_MODEL,
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
        _LOGGER.warning("async_get_options_flow called")
        return WhisperHTTPOptionsFlow()


class WhisperHTTPOptionsFlow(config_entries.OptionsFlow):
    """Handle options for Whisper HTTP STT."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Handle the options step."""
        _LOGGER.warning("async_step_init called")

        current_model = self.config_entry.options.get(CONF_MODEL, DEFAULT_MODEL)
        current_language = self.config_entry.options.get(CONF_LANGUAGE, DEFAULT_LANGUAGE)

        # Build model choices dict
        models_dict: dict[str, str] = {m: m for m in AVAILABLE_MODELS}
        if current_model not in AVAILABLE_MODELS:
            models_dict[current_model] = current_model

        schema = vol.Schema(
            {
                vol.Optional(CONF_MODEL, default=current_model): vol.In(models_dict),
                vol.Optional(CONF_LANGUAGE, default=current_language): vol.In(
                    SUPPORTED_LANGUAGES
                ),
            }
        )

        if user_input is not None:
            _LOGGER.warning("user_input=%s", user_input)
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(step_id="init", data_schema=schema)
