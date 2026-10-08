---
sidebar_position: 30
title: Gemini 3.8 Flash (Understanding + TTS)
description: Google Gemini 3.8 Flash multimodal understanding (image, video, audio, PDF) and Gemini 3.8 Flash / Flash-Lite text-to-speech via the opentryon GeminiUnderstandAdapter and GeminiTTSAdapter.
keywords:
  - Gemini 3.8 Flash
  - gemini-3.8-flash
  - Gemini TTS
  - gemini-3.8-flash-tts
  - text-to-speech
  - multimodal understanding
  - video understanding
  - PDF understanding
---

# Gemini 3.8 Flash (Understanding + TTS)

Two Google Gemini 3.8 models share one key (`GEMINI_API_KEY`, the same one used by Nano Banana, Veo and Gemini Omni):

| CLI model | Service | Model id | What it does |
|---|---|---|---|
| `gemini-3.8-flash` | `understand` | `gemini-3.8-flash` | Text, image, video, audio and PDF in → text out |
| `gemini-3.8-flash-tts` | `tts` | `gemini-3.8-flash-tts` | Most expressive speech, 130+ languages, two-speaker dialogue |
| `gemini-3.8-flash-lite-tts` | `tts` | `gemini-3.8-flash-lite-tts` | Faster, lower-cost speech, 100+ languages |

Google-only, cloud-only: there are no open weights.

```bash
export GEMINI_API_KEY="your_api_key"
```

## Understanding — `gemini-3.8-flash`

Google's most capable Flash model (stable since 2 Sep 2026): 1,048,576-token context, 65,536 max output tokens. Before this, the `understand` service had no Gemini model at all.

Fashion uses: attribute extraction from look photos, lookbook and runway video review, reading care labels and size charts from PDFs, voice-note briefs.

```bash
opentryon understand --model gemini-3.8-flash \
  --image look1.jpg look2.jpg --prompt "Compare the two outfits: garments, colours, fabrics."

opentryon understand --model gemini-3.8-flash \
  --video runway.mp4 --prompt "Summarise the collection and list each look's key pieces." \
  --thinking-level low

opentryon understand --model gemini-3.8-flash --pdf size_chart.pdf --prompt "Extract the size table as JSON."
```

| Flag | Notes |
|---|---|
| `--image`, `--video`, `--audio`, `--pdf` | One or more inputs each (path or URL); mix freely in one call |
| `--prompt`, `--system` | Question and optional system instruction |
| `--thinking-level` | `low`, `medium` or `high`. **`minimal` is not supported** and the API rejects it |
| `--max-tokens` | Output cap, at most 65,536 |

Inputs larger than about 18 MB go through the Files API automatically (the adapter waits until the upload is ACTIVE). YouTube links are passed straight to Gemini. `gs://` and Files API URIs are used as-is.

```python
from tryon.api.gemini import GeminiUnderstandAdapter

out = GeminiUnderstandAdapter().understand(
    image="look.jpg",
    prompt="List garments, colours and fabrics.",
    thinking_level="low",
)
print(out["text"], out["usage"])
```

Notes: `thinking_level="medium"` is sent as-is even if your installed `google-genai` predates it (the SDK's enum may not list it; the adapter silences that cosmetic warning). Planner pin: `gemini 3.8 flash` / `gemini-3.8-flash`; the `understand` default stays `kimi-k2.6`. MCP tool: `understand_gemini_3_8_flash`.

## Text-to-speech — `gemini-3.8-flash-tts` / `gemini-3.8-flash-lite-tts`

Text in, audio out. The adapter calls the Gemini **Interactions** endpoint (`POST /v1beta/interactions`) over plain REST, so it works regardless of your `google-genai` version (Google recommends ≥ 2.25.0 for the SDK).

- **30 prebuilt voices** — Zephyr, Puck, Charon, **Kore** (default), Fenrir, Leda, Orus, Aoede, Callirrhoe, Autonoe, Enceladus, Iapetus, Umbriel, Algieba, Despina, Erinome, Algenib, Rasalgethi, Laomedeia, Achernar, Alnilam, Schedar, Gacrux, Pulcherrima, Achird, Zubenelgenubi, Vindemiatrix, Sadachbia, Sadaltager, Sulafat — plus the extended voice library and custom `voice_...` / `voicekey_...` ids from Google's voice design / replication features.
- **Style, not stage directions.** The transcript is read **verbatim**. Put delivery direction (emotion, pace, accent) in `--style`; put momentary events inline as English tags such as `<sigh>`, `<laugh>`, `<short pause>`, `<long pause>`.
- **Output.** 24 kHz mono 16-bit **WAV** by default. `--audio-format audio/l16` (raw PCM), `audio/mulaw` or `audio/alaw` with `--sample-rate 24000|16000|8000` for telephony/IVR.
- **Two speakers** per request, prebuilt voices only. For more characters, or to mix custom voices, synthesize each turn separately.

```bash
opentryon tts --model gemini-3.8-flash-tts \
  --text "Welcome to the spring collection <short pause> linen is back." \
  --voice Puck --style "warm, upbeat, a little amused"

# Two-speaker dialogue
cat > turns.json <<'JSON'
[
  {"speaker": "Joe",  "text": "Which look is your favourite?", "style": "curious"},
  {"speaker": "Jane", "text": "The linen set, by far.",         "style": "relaxed"}
]
JSON
opentryon tts --model gemini-3.8-flash-lite-tts \
  --dialogue turns.json --speaker Joe=Puck Jane=Kore
```

```python
from tryon.api.gemini import GeminiTTSAdapter

adapter = GeminiTTSAdapter()  # gemini-3.8-flash-tts
open("hello.wav", "wb").write(adapter.generate_speech("Have a wonderful day!", voice="Kore", style="cheerful"))
open("dialogue.wav", "wb").write(adapter.generate_dialogue(
    [{"speaker": "Joe", "text": "Hi Jane!"}, {"speaker": "Jane", "text": "Hey Joe."}],
    speakers={"Joe": "Puck", "Jane": "Kore"},
))
```

Notes: MCP tools `tts_gemini_3_8_flash_tts` and `tts_gemini_3_8_flash_lite_tts`. Planner pins: `gemini tts`, `gemini 3.8 flash tts`, `gemini lite tts` (a bare TTS request still defaults to `eleven-v4`). Compare with [ElevenLabs Eleven v4](elevenlabs.md), which offers cloned voices and 90+ languages. Not yet wired: the `GET /v1beta/voices` listing and voice design / replication endpoints (use a `voice_...` id you created elsewhere).

References: [Gemini 3.8 Flash](https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash) · [Speech generation](https://ai.google.dev/gemini-api/docs/speech-generation) · [Thinking](https://ai.google.dev/gemini-api/docs/thinking)
