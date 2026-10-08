---
sidebar_position: 28
title: Claude Haiku 5.5 Understanding
description: Image and text understanding with Anthropic's Claude Haiku 5.5 via the opentryon ClaudeUnderstandAdapter.
keywords:
  - Claude Haiku 5.5
  - claude-haiku-5-5
  - Anthropic
  - image understanding
  - classification
  - extraction
---

# Claude Haiku 5.5 Understanding

[Claude Haiku 5.5](https://platform.claude.com/docs/en/models/haiku-5-5/overview) (`claude-haiku-5-5`, released 7 Oct 2026) is Anthropic's fastest and cheapest tier, built for high-volume, latency-sensitive work such as classification, extraction and routing. OpenTryOn exposes it through the `understand` service with `ClaudeUnderstandAdapter` (first-party Messages API, `anthropic` SDK).

Good fits in fashion pipelines: tagging garment attributes, reading care labels and size tags, writing alt-text and product copy, and cheap QC passes over generated try-on images.

| Property | Value |
|---|---|
| Model id | `claude-haiku-5-5` |
| Input / output | Text and images in, text out (**no video**) |
| Context / max output | 1M tokens / 128K tokens |
| Price | From $0.10 / $0.50 per MTok (input / output), 50% off on Batch |
| Thinking | Adaptive, on by default; `effort` low / medium (default) / high / xhigh / max |

## Authentication

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

This is the same key the Studio chat planner already uses when `OPENTRYON_AGENT_LLM_PROVIDER=anthropic`.

## CLI

```bash
opentryon understand --model claude-haiku-5-5 \
  --image garment.jpg --prompt "List fabric, colour, fit and neckline as JSON."

# Cheapest/fastest: low effort, thinking off (thinking can only be disabled at high effort or below)
opentryon understand --model claude-haiku-5-5 --image label.jpg \
  --prompt "Transcribe the care label." --effort low --no-thinking

# Text-only also works
opentryon understand --model claude-haiku-5-5 --prompt "Write a 20-word product blurb for a linen shirt."
```

| Flag | Notes |
|---|---|
| `--image`, `-i` | Optional image (path or URL; URLs are passed through, files are base64-encoded) |
| `--prompt`, `-p` | Question or instruction |
| `--system` | Optional system prompt |
| `--effort` | `low`, `medium`, `high`, `xhigh`, `max` (API default `medium`) |
| `--no-thinking` | Sends `thinking: {"type": "disabled"}`; rejected at `xhigh` / `max` |
| `--max-tokens` | Output cap, **including thinking** (default 4096) |

`temperature`, `top_p` and `top_k` are deliberately not exposed: Haiku 5.5 returns HTTP 400 for any non-default value.

## Python

```python
from tryon.api.claude import ClaudeUnderstandAdapter

adapter = ClaudeUnderstandAdapter()  # reads ANTHROPIC_API_KEY
result = adapter.understand(
    image="garment.jpg",
    prompt="Describe the outfit in one sentence.",
    effort="low",
    thinking=False,
)
print(result["text"], result["usage"])
```

`understand_image(image, ...)` accepts a list of images for multi-image comparison.

## Notes

- MCP tool: `understand_claude_haiku_5_5` (generated from the registry).
- Planner: `claude haiku 5.5` / `haiku 5.5` / `claude-haiku-5-5` pin this model. The `understand` default stays `kimi-k2.6`.
- Haiku 5.5 uses the newer tokenizer (about 30% more tokens than Haiku 4.5 for the same text) — budget `--max-tokens` accordingly.
- Cloud-only: Anthropic publishes no open weights.

See also: [Kimi](kimi), [Qwen3.8](qwen3.8), [DeepSeek](deepseek), [GLM](glm).
