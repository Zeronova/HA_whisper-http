"""STT platform for Whisper HTTP STT integration."""

from __future__ import annotations

import io
import logging
import wave
from typing import AsyncIterable

from aiohttp import FormData
from homeassistant.components.stt import (
    AudioBitRates,
    AudioChannels,
    AudioCodecs,
    AudioFormats,
    AudioSampleRates,
    SpeechMetadata,
    SpeechResult,
    SpeechResultState,
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
            "sw_version": "0.1.4",
        }

    @property
    def supported_languages(self) -> list[str]:
        """Return the list of supported languages."""
        return ["de", "en", "fr", "it", "es", "nl"]

    @staticmethod
    def _ensure_wav(audio_data: bytes) -> bytes:
        """Wrap raw PCM bytes in a WAV container if not already WAV.

        HA 2026.4+ may deliver raw PCM without a WAV header when the
        integration declares PCM codec support. Whisper's ffmpeg processing
        requires a valid WAV container.
        """
        if audio_data[:4] == b"RIFF":
            return audio_data  # Already has WAV header
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)  # 16 bit = 2 bytes
            wav.setframerate(16000)
            wav.writeframes(audio_data)
        wrapped = buf.getvalue()
        _LOGGER.debug(
            "Wrapped raw PCM (%d bytes) in WAV container (%d bytes)",
            len(audio_data),
            len(wrapped),
        )
        return wrapped

    async def async_process_audio_stream(
        self, metadata: SpeechMetadata, stream: AsyncIterable[bytes]
    ) -> SpeechResult:
        """Process an audio stream to text via the Whisper REST API.

        metadata: SpeechMetadata containing language, format, codec, bit_rate,
                  sample_rate, and channel.
        stream: async iterable yielding chunks of audio bytes (WAV PCM 16kHz 16bit).
        Returns a SpeechResult with the transcribed text on success.
        """
        audio_data = b""
        async for chunk in stream:
            audio_data += chunk

        if not audio_data:
            _LOGGER.error("Empty audio stream received")
            return SpeechResult(text=None, result=SpeechResultState.ERROR)

        _LOGGER.debug("Received %d bytes of audio for transcription", len(audio_data))

        # HA 2026.4+ may deliver raw PCM — ensure valid WAV container
        audio_data = self._ensure_wav(audio_data)

        model = self._config_entry.options.get(CONF_MODEL, self._model)
        lang = metadata.language or self._language

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
                    return SpeechResult(text=None, result=SpeechResultState.ERROR)

                result_json = await resp.json()
                text = result_json.get("text", "")
                _LOGGER.debug(
                    "Transcription result (%d chars): %s", len(text), text[:100]
                )
                return SpeechResult(text=text, result=SpeechResultState.SUCCESS)

        except Exception as err:
            _LOGGER.error("Error during transcription: %s", err)
            return SpeechResult(text=None, result=SpeechResultState.ERROR)
