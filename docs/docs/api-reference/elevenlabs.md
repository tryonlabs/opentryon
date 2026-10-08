---
sidebar_position: 28
title: ElevenLabs Eleven v4 / v4 Turbo (Text-to-Speech)
description: OpenTryOn's first text-to-speech service -- ElevenLabs Eleven v4 and Eleven v4 Turbo via the opentryon ElevenLabsAdapter.
keywords:
  - ElevenLabs
  - Eleven v4
  - Eleven v4 Turbo
  - text-to-speech
  - TTS
  - voiceover
  - voice cloning
---

# ElevenLabs Eleven v4 / v4 Turbo (Text-to-Speech)

[Eleven v4](https://elevenlabs.io/docs/overview/models) and **Eleven v4
Turbo** are ElevenLabs' text-to-speech models, called via their first-party
REST API. This is OpenTryOn's **first `tts` service** -- previously there
was no speech modality in the registry at all.

Useful on its own (voiceover/narration for lookbook or product copy), or as
an input to [Pruna P-Video-Avatar](pruna.md) (which accepts a pre-generated
`--audio` file) for a talking-head clip with a specific branded/cloned
voice.

> A second TTS vendor is available: [Gemini 3.8 Flash TTS](gemini-3-8.md) (`gemini-3.8-flash-tts`, `gemini-3.8-flash-lite-tts`, `GEMINI_API_KEY`) with 30 prebuilt voices and two-speaker dialogue.

## Capabilities

| Capability | `eleven-v4` | `eleven-v4-turbo` |
|---|---|---|
| Character limit | 10,000 (~10 min of audio) | Not explicitly capped |
| Latency | Not optimized for real-time | ~100ms median inference |
| Languages | 90+ | 90+ |
| Style | Most emotionally rich / expressive | Adds **audio tags** for delivery control, e.g. `[whispers]`, `[laughs]` |
| Voice cloning | Yes (via `voice_id`) | Yes (via `voice_id`) |
| Output formats | mp3, wav, pcm, opus, µ-law, A-law at various sample rates/bitrates | Same |

Both models are billed per character; see
[elevenlabs.io/pricing/api](https://elevenlabs.io/pricing/api) for current
rates.

## Prerequisites

1. **ElevenLabs account** and API key: [elevenlabs.io/app/settings/api-keys](https://elevenlabs.io/app/settings/api-keys)
2. Set `ELEVENLABS_API_KEY` in your `.env` file
3. Optional base URL override via `ELEVENLABS_BASE_URL`

```bash
ELEVENLABS_API_KEY=your_elevenlabs_api_key
# ELEVENLABS_BASE_URL=https://api.elevenlabs.io  # default
```

## Voices

The adapter defaults `voice_id` to ElevenLabs' premade **"Rachel"** voice
(`21m00Tcm4TlvDq8ikWAM`) so you can try it without first looking one up.
Browse or clone voices at
[elevenlabs.io/app/voice-library](https://elevenlabs.io/app/voice-library),
or list your account's voices with `GET /v1/voices` (not wrapped by this
adapter -- use ElevenLabs' own SDK/dashboard for voice management; this
adapter is generation-only).

## Installation

No extra install -- the adapter only uses `requests`, already a core
`opentryon` dependency.

## Quick Start

```python
from tryon.api.elevenlabs import ElevenLabsAdapter

adapter = ElevenLabsAdapter()  # eleven_v4 by default

audio = adapter.generate_speech(
    "Welcome to the spring collection.",
    voice_id="21m00Tcm4TlvDq8ikWAM",  # optional; this is the default
)
open("voiceover.mp3", "wb").write(audio)
```

### Eleven v4 Turbo with audio tags

```python
turbo = ElevenLabsAdapter(model="eleven_v4_turbo")
audio = turbo.generate_speech("[whispers] New drop just landed.")
open("teaser.mp3", "wb").write(audio)
```

## CLI

```bash
opentryon tts --model eleven-v4 --text "Welcome to the spring collection."

opentryon tts --model eleven-v4-turbo \
  --text "[whispers] New drop just landed." \
  --voice-id 21m00Tcm4TlvDq8ikWAM --output-format wav_44100

opentryon tts --model eleven-v4 --text "Bonjour et bienvenue." --language-code fr
```

`opentryon` writes the result with an extension sniffed from the actual
audio bytes (`.mp3`/`.wav`/`.opus`; headerless formats like raw PCM or
µ-law fall back to `.raw`), not from the requested `--output-format`
string, so it's always correct even if a request is retried with a
different format.

| Flag | Notes |
|---|---|
| `--text` / `-t` | Required. Eleven v4: up to 10,000 characters |
| `--voice-id` | Default: premade "Rachel" (`21m00Tcm4TlvDq8ikWAM`) |
| `--output-format` | Codec/sample-rate/bitrate; default `mp3_44100_128` |
| `--language-code` | Optional ISO 639-1 code to force text normalization |
| `--stability` / `--similarity-boost` / `--style` / `--speed` | Voice settings (0-1 range, except `--speed`) |
| `--no-speaker-boost` | Disable enhanced speaker similarity |
| `--seed` | Optional deterministic-sampling seed |

## MCP

Same registry models appear as MCP tools (no extra wiring):

- `tts_eleven_v4` / `tts_eleven_v4_turbo` — ElevenLabs API (`ELEVENLABS_API_KEY`)

See [MCP Server](../getting-started/mcp.md) and
[`mcp-server/README.md`](https://github.com/tryonlabs/opentryon/blob/main/mcp-server/README.md).

Studio note: `tts` is a brand-new service category, so it does not yet have
a dedicated capability picker screen in TryOn Studio (those are currently
Image / VTON / Understand / Video / BG Remove). The MCP tools are live and
callable (e.g. via Studio's Agent chat) as soon as the MCP server restarts;
a dedicated Studio screen would be a separate `tryon-studio`-side change.

## API Reference

### `ElevenLabsAdapter`

```python
class ElevenLabsAdapter:
    def __init__(
        self,
        api_key: Optional[str] = None,   # ELEVENLABS_API_KEY
        model: str = "eleven_v4",        # or "eleven_v4_turbo"
        base_url: Optional[str] = None,  # ELEVENLABS_BASE_URL or the default
    )
```

### `generate_speech`

```python
def generate_speech(
    self,
    text: str,
    voice_id: str = "21m00Tcm4TlvDq8ikWAM",
    model: Optional[str] = None,
    output_format: str = "mp3_44100_128",
    language_code: Optional[str] = None,
    stability: float = 0.5,
    similarity_boost: float = 0.75,
    style: float = 0.0,
    speed: float = 1.0,
    use_speaker_boost: bool = True,
    seed: Optional[int] = None,
) -> bytes
```

Returns raw audio bytes (content type matches `output_format`). This is
what `opentryon tts --model eleven-v4` calls.

## References

- [ElevenLabs models overview](https://elevenlabs.io/docs/overview/models)
- [Create speech API reference](https://elevenlabs.io/docs/api-reference/text-to-speech/convert)
- [ElevenLabs API pricing](https://elevenlabs.io/pricing/api)
- [ElevenLabs voice library](https://elevenlabs.io/app/voice-library)
