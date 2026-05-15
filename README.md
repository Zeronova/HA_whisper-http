# Whisper HTTP STT für Home Assistant

Home Assistant STT-Plattform für lokale Spracherkennung via [Whisper Server](https://github.com/hwdsl2/whisper-server) (OpenAI-kompatible API).

## Installation

### Via HACS (empfohlen)

1. HACS → Custom Repositories → `https://github.com/zeronova/HA_whisper-http` (Typ: Integration)
2. HACS → Integrationen → "Whisper HTTP" installieren
3. HA neu starten

### Manuell

1. Ordner `whisper_http` nach `custom_components/whisper_http` kopieren
2. HA neu starten

## Konfiguration

1. **Integration hinzufügen:** Einstellungen → Geräte & Dienste → Integration hinzufügen → "Whisper HTTP"
2. **Host und Port** des Whisper-Servers angeben
3. **Assistent einrichten:** Einstellungen → Sprachassistenten → Assist → Sprache-zu-Text → "Whisper HTTP" auswählen
