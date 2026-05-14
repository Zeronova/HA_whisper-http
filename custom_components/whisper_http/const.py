"""Constants for the Whisper HTTP STT integration."""

DOMAIN = "whisper_http"

CONF_HOST = "host"
CONF_PORT = "port"
CONF_MODEL = "model"
CONF_LANGUAGE = "language"

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 9000
DEFAULT_LANGUAGE = "de"

ENDPOINT_MODELS = "/v1/models"
ENDPOINT_TRANSCRIBE = "/v1/audio/transcriptions"

SUPPORTED_LANGUAGES = {
    "de": "Deutsch",
    "en": "English",
    "fr": "Français",
    "it": "Italiano",
    "es": "Español",
    "nl": "Nederlands",
}
