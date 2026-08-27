# Changelog

All notable changes to OpenTryOn will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- **Planner is a super agent over the live registry.** `planner_agent` still has the same MCP arguments (Studio chat unchanged). After classify, it binds a **filtered** registry slice and calls `invoke_model` — the same runner MCP model tools use. Named models in the prompt (e.g. `wan-3.0`) pin that id. VTON / model-swap are recipes (defaults + outfit-preserving prompt rewrite), not LangChain `create_agent` loops. `tryon.tools` is frozen; do not add providers there.

### Fixed

- **Planner / Studio chat:** base64 photo uploads are materialized to 2048px temp files before `invoke_model` runs, so GPT-4o no longer 429s with `Request too large` / TPM on two phone images.

### Added

#### 🎨 Image — Muse Image (Meta Model API)
- **Muse Image** (`MuseImageAdapter` / CLI `--model muse-image`): first-party Meta Model API `muse-image-1.0`
  - Same `MODEL_API_KEY` (aliases `META_MODEL_API_KEY` / `MUSE_API_KEY`)
  - T2I, I2I / multi-ref compose, composition VTON; $0.01/image; agentic search on by default
  - **No open weights.** Muse Glimmer is a separate text VLM, not an image generator
  - MCP tools `generate_muse_image`, `edit_muse_image`, `vton_muse_image`
  - Docs: `docs/docs/api-reference/muse-image.md`
- **Muse Video is not integrable yet.** Consumer preview only ([announcement](https://ai.meta.com/blog/introducing-muse-image-muse-video-msl/)); Meta Model API has video *understanding* (Muse Spark), not video *generation*. No `--model muse-video`. Docs: `docs/docs/api-reference/muse-video.md`

#### 🎬 Video — MiniMax H3 (API + local)
- **MiniMax H3** (`MiniMaxH3Adapter` / CLI `--model minimax-h3`): first-party V2 `POST /v2/video_generation`
  - Same `MINIMAX_API_KEY` as Hailuo 2.3; **does not** reuse the Hailuo 2.3 V1 adapter
  - T2V, first/last-frame I2V, optional reference-to-video in Python; 4–15s, 768P/2K, native stereo audio
  - MCP tool `video_generate_minimax_h3`
  - Docs: `docs/docs/api-reference/minimax-h3.md`
- **MiniMax H3 local Diffusers** (`MiniMaxH3LocalAdapter` / CLI `--model minimax-h3-local`): open-weight dual-path
  - `MiniMaxAI/MiniMax-H3` via `ModularPipeline` (`t2va` / `fl2va`); 768p H3-Base (2K regenerate is not open-sourced)
  - CUDA + Diffusers from main; ComponentsManager CPU offload by default
  - Community License excludes US/EU/UK/South Korea for local weights; hosted API is globally available
  - MCP tool `video_generate_minimax_h3_local`
  - Docs: `docs/docs/local-models/minimax-h3.md`

#### 🤖 Planner — catalog-grounded help
- **`help` intent** on `planner_agent`: greetings and “what can you do?” are answered from the live `tryon.cli.registry` catalog (not a vector RAG store). `out_of_scope` no longer returns “no fashion-related inputs”.

#### 🎬 Video — Wan 3.0 hosted API
- **Alibaba Wan 3.0** (`WanVideoAdapter` / CLI `--model wan-3.0`): first-party DashScope `wan3.0-video` (preview)
  - Same `DASHSCOPE_API_KEY` / `WAN_API_BASE_URL` as `--model wan-api`
  - T2V, first-frame I2V, first-last frame, document (`--file`) and webpage (`--link`); up to 30s, 480P/720P/1080P
  - **No official open weights.** Local Wan remains `--model wan-2.2` (Diffusers TI2V-5B)
  - MCP tool `video_generate_wan_3_0`
  - Docs: `docs/docs/api-reference/wan.md`

#### 🎨 Image — Qwen-Image generate / edit / VTON
- **Qwen-Image 3.0** (`QwenImageAdapter` / CLI `--model qwen-image`): DashScope first-party T2I, I2I (1–3 refs), and person+garment virtual try-on
  - Same `DASHSCOPE_API_KEY` as Qwen3.8-Max understand and Wan video
  - Default `qwen-image-3.0-pro`; `--model-version` also accepts `qwen-image-3.0` / `qwen-image-2.0-pro` / `qwen-image-2.0`
  - Thinking + prompt rewrite on by default (`--no-thinking`, `--no-prompt-extend`)
  - MCP tools `generate_qwen_image`, `edit_qwen_image`, `vton_qwen_image`
  - Docs: `docs/docs/api-reference/qwen-image.md` — compose with `understand --model qwen3.8-max` for caption → generate / try-on
- **Qwen-Image local Diffusers** (`QwenImageLocalAdapter` / CLI `--model qwen-image-local`): open-weight dual-path
  - **T2I** default `Qwen/Qwen-Image-2512` (`QwenImagePipeline`)
  - **Edit / VTON** default `Qwen/Qwen-Image-Edit-2511` (`QwenImageEditPlusPipeline`, 1–3 refs)
  - CPU offload on by default; CUDA required; MCP `generate_qwen_image_local`, `edit_qwen_image_local`, `vton_qwen_image_local`
  - Docs: `docs/docs/local-models/qwen-image.md`

## [0.0.4] - 17 August 2026

### Added

#### 🎬 Video — new APIs + local paths
- **LTX-2.5 official API** (`tryon.api.ltx.LTXVideoAdapter`, CLI `--model ltx-2.5-api`): async V2 T2V/I2V with synced audio (`ltx-2-5-fast` / `ltx-2-5-pro`)
- **LTX-2.5 local Diffusers** (`tryon.models.ltx25.LTX25Adapter`, CLI `--model ltx-2.5`): open-weight distilled T2V/I2V on CUDA (requires Diffusers from main + HF gated access)
- **MiniMax Hailuo 2.3** (`tryon.api.minimax.HailuoVideoAdapter`, CLI `--model hailuo-2.3`): official API T2V/I2V (API-only; no open weights)
- **Alibaba Wan dual-path**: API `WanVideoAdapter` (`wan-api`) + local Diffusers `Wan22Adapter` (`wan-2.2`, default TI2V-5B)
- **Runway Gen-4.5** (`tryon.api.runway.RunwayVideoAdapter`, CLI `--model runway-gen4.5`): official API T2V/I2V (API-only; no open weights)

#### 🧠 Understanding — Qwen3.8 dual-path
- **Qwen3.8 dual-path (understand)**: Alibaba’s native multimodal flagship family for text + image + video → text
  - **API** `QwenUnderstandAdapter` / CLI `--model qwen3.8-max` (DashScope OpenAI-compatible; `DASHSCOPE_API_KEY`)
  - **Local** `Qwen38Adapter` / CLI `--model qwen3.8` (default HF `Qwen/Qwen3.8-27B`; optional `QWEN38_MODEL_ID`)
  - Capabilities exposed via OpenTryOn: image & video understanding, thinking mode (`enable_thinking` / `--no-thinking`), reasoning depth (`reasoning_effort`: `xhigh` | `medium` | `low`)
  - Docs: `docs/docs/api-reference/qwen3.8.md`, `docs/docs/local-models/qwen3.8.md`; MCP tools `understand_qwen3_8_max`, `understand_qwen3_8`

#### 📘 Docs / agent DX
- **Model integration guidelines** for agents: `docs/docs/advanced/model-integration-guidelines.md` (Path A first-party API vs Path B local/HF/Ollama/LM Studio/Unsloth)
- Expanded CLI, MCP, env.template, and local-models docs for the new providers

## [0.0.3] - 2 August 2026

### Added

#### 🎬 Video / 🎨 Image — new provider models
- **ByteDance Seedance 2.5** (`tryon.api.byteplus.SeedanceAdapter`): ModelArk async video (`opentryon video-generate --model seedance`). Variants: Seedance 2.5 + Seedance 2.0 Standard/Fast/Mini
- **ByteDance Seedream 5.0 Pro** (`SeedreamAdapter`): ModelArk image generate + edit/multi-ref (`opentryon generate|edit --model seedream`)
- **Luma Ray 3.2** (`tryon.api.lumaAI.LumaRay32Adapter`): Agents API T2V/I2V with HDR (`opentryon video-generate --model luma-ray-3.2`)
- **Kling 3.0 / 3.0 Omni / 2.5 Turbo** (`tryon.api.kling_video.KlingVideoAdapter`): official Open Platform video endpoints (`kling-v3`, `kling-v3-omni`, `kling-v2-5-turbo`)
- **xAI Grok Imagine Video 1.5** + **Image Quality** (`tryon.api.xai`)
- **Ideogram 4.0** (`tryon.api.ideogram.IdeogramAdapter`) with TURBO/DEFAULT/QUALITY rendering speeds
- **Pruna** (`tryon.api.pruna`): shared `PrunaClient` plus `p-image`, `p-image-edit`, `p-image-upscale`, `p-video`, `p-video-replace`, `p-video-avatar`, `p-video-animate` (try-on remains `vton --model p-image-tryon` and reuses the shared client)
- Postman collection (`postman/opentryon-media.postman_collection.json`) and OpenAPI snapshot (`openapi/opentryon-media.openapi.yaml`) for the new media models
- Docs pages under `docs/docs/api-reference/` for Seedance/Seedream, Kling Video, Luma Ray 3.2, Grok Imagine, Ideogram, expanded Pruna

### Changed

#### 🎨 Demos
- **The aggregated Next.js/Tailwind web UI has moved out of this repo.** `demo/virtual-tryon`, `demo/fashion-prompt-builder`, and `demo/tryon-agent` (the combined dashboard prototype) are removed; that UI now lives in the standalone [`tryon-studio`](https://github.com/tryonlabs/tryon-studio) app, which talks to `opentryon` exclusively over the MCP server (see below) so the two repos stay independently releasable
- `demo/` now contains only the Gradio demos (`extract_garment`, `model_swap`, `outfit_generator`) -- this package's own demos are Gradio apps and Jupyter notebooks, not a hosted web frontend
- Added `notebooks/virtual_tryon_demo.ipynb`, a runnable, dependency-light walkthrough of `tryon.cli.runner.invoke_model()` for the `vton` service (dry-run by default, no API key required to execute)

### Added (earlier in 0.0.3 cycle)

#### 🔌 MCP Server
- **Rebuilt `mcp-server/` on [FastMCP](https://gofastmcp.com) 3.x** (up from the low-level `mcp` SDK), replacing ~15 hand-written tool wrappers with 27 tools generated dynamically from `tryon.cli.registry` -- every model reachable via the `opentryon` CLI (Kimi, FLUX VTO/2, GPT Image, Sora, Veo, Nano Banana, BEN2, etc.) is now automatically exposed as an MCP tool, and new registry entries need zero MCP-server changes to show up
- New `tryon.cli.runner.invoke_model()`: a kwargs-based, non-argv equivalent of the CLI's `run_service()`, shared by both the CLI and the MCP server so they can never drift apart; always returns a structured `{"success": ...}` dict instead of raising
- Two discovery tools, `list_opentryon_tools` and `opentryon_status`, report live per-model configuration/readiness straight from the registry and the loaded `.env`
- Every generated tool supports `dry_run` (preview the resolved adapter call, no API/GPU cost) and `output_dir`, matching the CLI's `--dry-run`/`--output-dir` flags
- `mcp-server/test_server.py`: offline test suite covering tool/registry parity, schema generation (required fields, `choices` -> enum), dry-run calls across all six services, and `alt_method_on_image` switching (veo/sora/luma-video)
- `invoke_model()` / `run_service()` results for `images`/`image_bytes` outputs now include an `images_base64` list alongside `output_paths`, so remote MCP clients (e.g. a web frontend calling the server over the `http` transport) can render results directly without needing filesystem access to the server's `output_dir`

#### 🖥️ Unified CLI
- **`opentryon` command-line interface**: Installable console script exposing every adapter through `opentryon <service> --model <model> [params...]` (services: `vton`, `generate`, `edit`, `understand`, `video-generate`, `bg-remove`)
- Data-driven model registry (`tryon/cli/registry.py`) with two-stage argument parsing, `--dry-run`, and automatic `local`-extra detection
- `pip install opentryon[local]` extra to keep the core install lightweight while still supporting GPU-only models

#### 🧠 Multimodal Understanding
- **Kimi K2.6 & K2.7 Code (Moonshot AI)**: General-purpose text, image, and video understanding via the hosted API (`tryon.api.kimi.KimiUnderstandAdapter`), plus an open-weight local counterpart (`tryon.models.kimi_vl.KimiVLAdapter`, based on `moonshotai/Kimi-VL-A3B-Thinking-2506`)
  - Available in the CLI as `opentryon understand --model kimi-k2.6 / kimi-k2.7-code / kimi-vl`
  - Extends OpenTryOn's understanding capabilities beyond the fashion domain (documents, UI screenshots, general photography, etc.)

#### 👗 Virtual Try-On / 🎨 Image Generation
- **Pruna P-Image-Try-On** (`tryon.api.vton.PImageTryOnAdapter`): multi-garment virtual try-on -- fits up to 11 garment reference images onto a person photo in a single call. Available as `opentryon vton --model p-image-tryon` and the `vton_p_image_tryon` MCP tool. Lives under `tryon/api/vton/` (a use-case directory) rather than a new `tryon/api/pruna/` package -- see the updated "Decide where the adapter lives" section of `docs/docs/advanced/new-model-checklist.md` for the rationale (avoids one top-level vendor directory per new single-purpose provider)
- **Nano Banana 2 Lite** (`tryon.api.nano_banana.NanoBanana2LiteAdapter`, `gemini-3.1-flash-lite-image`): Google's fastest/cheapest Gemini image tier (1K resolution only). Registered under `generate` and `edit` (`opentryon generate|edit --model nano-banana-2-lite`), and under `vton` (`opentryon vton --model nano-banana-2-lite`) via a new `generate_virtual_tryon()` convenience method that composes a garment onto a person via multi-image composition -- a fast/cheap option, not the highest-fidelity one
- **FASHN AI Virtual Try-On** (`tryon.api.vton.FashnVTONAdapter`): fashion-focused try-on via FASHN's universal `/v1/run` API. Registered as `opentryon vton --model fashn-tryon-max` (recommended high-fidelity, up to 4K, prompt-based styling) and `opentryon vton --model fashn-tryon-v1.6` (fast/cheap real-time e-commerce). Also lives under `tryon/api/vton/`

#### 🎬 Video Generation
- **Gemini Omni Flash** (`tryon.api.omni.GeminiOmniAdapter`, `gemini-omni-flash-preview`): multimodal video generation and conversational editing via the Interactions API. Available as `opentryon video-generate --model gemini-omni` (text-to-video; pass `--image` for image-to-video; pass `--previous-interaction-id` for multi-turn edits). Uses the same `GEMINI_API_KEY` as Nano Banana / Veo

### Fixed
- Lazy (PEP 562) attribute loading for `tryon.api` so importing one adapter no longer transitively imports every adapter's dependencies (e.g. `torch`/`timm` for BEN2)
- Missing comma in `setup.py` `install_requires` that merged two dependency strings into one invalid requirement
- Missing `openai` dependency for GPT-Image/Sora adapters
- `tryon.api.nano_banana` adapters (`NanoBananaAdapter`, `NanoBananaProAdapter`, `NanoBanana2Adapter`) were decoding Gemini image responses with `part.as_image()`, which returns a `google.genai.types.Image` (a pydantic model), not a `PIL.Image.Image`, on `google-genai>=2.x` -- broke `.size`/`.mode` access and anything expecting a real PIL Image downstream (CLI/MCP output saving, notebooks, etc.). Now decodes `part.inline_data.data` directly via `PIL.Image.open()`

## [0.0.2] - 27 December 2025

### Added

#### 🎨 Image Generation
- **OpenAI GPT-Image Integration**: Added support for OpenAI's GPT-Image models
  - GPT-Image-1: High-quality image generation and editing
  - GPT-Image-1.5: Enhanced version with improved quality, better prompt understanding, and improved consistency
  - Support for text-to-image, image-to-image editing, multi-image composition, and mask-based editing
  - Background control, quality settings, and multiple output images
  - Full documentation and examples

#### 🎬 Video Generation
- **OpenAI Sora Video Generation**: Added support for OpenAI's Sora video models
  - Sora 2: Fast, high-quality video generation
  - Sora 2 Pro: Enhanced quality with superior temporal consistency
  - Text-to-video and image-to-video generation
  - Support for 4, 8, and 12-second videos with multiple resolutions (720p to Full HD)
  - Synchronous (blocking) and asynchronous (callback-based) wait modes
  - Progress tracking and status monitoring
  - Comprehensive documentation

- **Google Veo 3 Video Generation**: Added support for Google's Veo 3 video generation model
  - Generate high-quality, cinematic videos from text or images
  - Realistic motion and temporal consistency
  - Fine-grained control over style and camera dynamics
  - Full API integration with detailed documentation

#### 🤖 AI Agents
- **Virtual Try-On Agent (VTOnAgent)**: New LangChain-based AI agent for intelligent virtual try-on operations
  - Intelligent agent that can analyze prompts and automatically select appropriate models
  - Support for multiple virtual try-on providers (Kling AI, Segmind, Nova Canvas)
  - Tool-based architecture for flexible model selection
  - Comprehensive documentation and usage examples

- **Model Swap Agent (ModelSwapAgent)**: New AI agent for replacing models while preserving outfits
  - Automatically swaps models in images while maintaining outfit consistency
  - Support for multiple image generation models (Nano Banana, Nano Banana Pro, FLUX 2 Pro, FLUX 2 Flex)
  - Intelligent prompt engineering for model swapping
  - Full documentation with examples

#### 📚 Documentation & Infrastructure
- Added comprehensive documentation for all new features
- Created issue and PR templates for better contribution workflow
- Added security policy (SECURITY.md)
- Enhanced documentation with detailed API references
- Added quickstart guides for new features

### Changed
- Updated README.md with information about new features
- Enhanced project structure to accommodate new modules
- Improved code organization with new API adapters and agents

### Fixed
- Fixed broken link in fashion-prompt-builder documentation

## [0.0.1] - 16 December 2025

### Added
- Initial release of OpenTryOn
- Virtual Try-On support (Amazon Nova Canvas, Kling AI, Segmind)
- Image Generation (Nano Banana, FLUX.2, Luma AI)
- Video Generation (Luma AI Dream Machine)
- Datasets module (Fashion-MNIST, VITON-HD)
- Garment preprocessing and segmentation
- Pose estimation
- Interactive demos
- Complete documentation

[0.0.4]: https://github.com/tryonlabs/opentryon/releases/tag/v0.0.4
[0.0.3]: https://github.com/tryonlabs/opentryon/releases/tag/v0.0.3
[0.0.2]: https://github.com/tryonlabs/opentryon/releases/tag/v0.0.2
[0.0.1]: https://github.com/tryonlabs/opentryon/releases/tag/v0.0.1

