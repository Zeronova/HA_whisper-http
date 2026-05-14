# HA_whisper-http

**Home Assistant custom integration** for local Whisper speech-to-text via HTTP API.

Uses an OpenAI-compatible Whisper REST API (e.g. faster-whisper) as the STT provider for Home Assistant Assist pipelines.

## Features

- Connects to any OpenAI-compatible Whisper API (`/v1/audio/transcriptions`)
- Configurable model and language
- Config flow + options flow (no YAML needed)
- Supports HA Assist voice pipelines

## Requirements

- A running Whisper HTTP server supporting the OpenAI API format
  (e.g. `ahmetoner/whisper-asr-webservice` or a custom faster-whisper REST API)
- Home Assistant 2026.4+ (may work with earlier versions, untested)

## Installation

### Via HACS (recommended)

1. Add this repository to HACS as a custom integration:
   - HACS → Integrations → ⋮ → Custom repositories
   - Repository: `https://github.com/Zeronova/HA_whisper-http`
   - Category: Integration
2. Download the integration
3. Restart Home Assistant

### Manual

Copy the `custom_components/whisper_http/` directory to your HA `custom_components/` directory and restart Home Assistant.

## Configuration

1. Go to Settings → Devices & Services → Add Integration
2. Search for "Whisper HTTP STT"
3. Enter your Whisper server host and port (default: `192.168.2.7:9000`)
4. Configure model and default language in Options

## Usage

After configuration, the STT entity `stt.whisper_http` appears and can be selected in Assist pipelines:

Settings → Voice Assistants → [Your Assistant] → Speech-to-text → Whisper HTTP STT
