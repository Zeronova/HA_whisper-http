"""STT platform for Whisper HTTP STT integration."""

from __future__ import annotations

import logging
from typing import AsyncIterable

from aiohttp import FormData
from homeassistant.components.stt import (
    AudioBitRates,
    AudioChannels,
    AudioCodecs,
    AudioFormats,
    AudioSampleRates,
    SpeechToTextEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_HOST,
    CONF_LANGUAGE,
    CONF_MODEL,
    CONF_PORT,
    DEFAULT_LANGUAGE,
    DEFAULT_MODEL,
    DOMAIN,
    ENDPOINT_TRANSCRIBE,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Whisper HTTP STT entities."""
    _LOGGER.warning("STT async_setup_entry called")
    async_add_entities([WhisperHTTPSTTEntity(config_entry)])


class WhisperHTTPSTTEntity(SpeechToTextEntity):
    """Whisper HTTP STT entity."""

    _attr_name = "Whisper HTTP STT"
    _attr_has_entity_name = True

    # Whisper works best with 16kHz 16bit mono PCM WAV

    @property
    def supported_formats(self) -> list[AudioFormats]:
        """Return list of supported audio formats."""
        return [AudioFormats.WAV]

    @property
    def supported_codecs(self) -> list[AudioCodecs]:
        """Return list of supported audio codecs."""
        return [AudioCodecs.PCM]

    @property
    def supported_bit_rates(self) -> list[AudioBitRates]:
        """Return list of supported audio bit rates."""
        return [AudioBitRates.BITRATE_16]

    @property
    def supported_sample_rates(self) -> list[AudioSampleRates]:
        """Return list of supported audio sample rates."""
        return [AudioSampleRates.SAMPLERATE_16000]

    @property
    def supported_channels(self) -> list[AudioChannels]:
        """Return list of supported audio channels."""
        return [AudioChannels.CHANNEL_MONO]

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize the Whisper HTTP STT entity."""
        super().__init__()
        _LOGGER.warning("WhisperHTTPSTTEntity.__init__")
        self._config_entry = config_entry
        self._host = config_entry.data[CONF_HOST]
        self._port = config_entry.data[CONF_PORT]
        self._base_url = f"http://{self._host}:{self._port}"
        model = config_entry.options.get(CONF_MODEL) or config_entry.data.get(CONF_MODEL, DEFAULT_MODEL)
        language = config_entry.options.get(CONF_LANGUAGE) or config_entry.data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE)
        self._model = model
        self._language = language
        self._attr_unique_id = f"{self._host}_{self._port}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._attr_unique_id)},
            "name": f"Whisper HTTP STT ({self._host}:{self._port})",
            "manufacturer": "OpenAI Whisper",
            "model": "faster-whisper",
            "sw_version": "0.1.1",
        }

    @property
    def supported_languages(self) -> list[str]:
        """Return the list of supported languages."""
        return list(self._attr_supported_languages)

    async def async_process_audio_stream(
        self, source: AsyncIterable[bytes], language: str | None = None
    ) -> str:
        """Process an audio stream to text via the Whisper REST API.

        source: async iterable yielding chunks of audio bytes (WAV PCM 16kHz 16bit).
        language: optional language hint (e.g. "de", "en").
        Returns the transcribed text (empty string on error).
        """
        audio_data = b""
        async for chunk in source:
            audio_data += chunk

        if not audio_data:
            _LOGGER.error("Empty audio stream received")
            return ""

        _LOGGER.debug("Received %d bytes of audio for transcription", len(audio_data))

        model = self._config_entry.options.get(CONF_MODEL, self._model)
        lang = language or self._language

        url = f"{self._base_url}{ENDPOINT_TRANSCRIBE}"

        session = async_get_clientsession(self.hass)

        try:
            # Build multipart form data for OpenAI-compatible API
            form = FormData()
            form.add_field(
                "file",
                audio_data,
                filename="audio.wav",
                content_type="audio/wav",
            )
            form.add_field("model", model)
            form.add_field("language", lang)
            form.add_field("response_format", "json")

            _LOGGER.debug(
                "Sending request to %s (model=%s, lang=%s, bytes=%d)",
                url, model, lang, len(audio_data),
            )

            async with session.post(url, data=form) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    _LOGGER.error(
                        "Whisper HTTP returned %s: %s", resp.status, error_text
                    )
                    return ""

                result_json = await resp.json()
                text = result_json.get("text", "")
                _LOGGER.debug(
                    "Transcription result (%d chars): %s", len(text), text[:100]
                )
                return text

        except Exception as err:
            _LOGGER.error("Error during transcription: %s", err)
            return ""
