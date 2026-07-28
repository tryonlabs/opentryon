# Changelog

All notable changes to OpenTryOn will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

#### 🎨 Demos
- **The aggregated Next.js/Tailwind web UI has moved out of this repo.** `demo/virtual-tryon`, `demo/fashion-prompt-builder`, and `demo/tryon-agent` (the combined dashboard prototype) are removed; that UI now lives in the standalone [`tryon-studio`](https://github.com/tryonlabs/tryon-studio) app, which talks to `opentryon` exclusively over the MCP server (see below) so the two repos stay independently releasable
- `demo/` now contains only the Gradio demos (`extract_garment`, `model_swap`, `outfit_generator`) -- this package's own demos are Gradio apps and Jupyter notebooks, not a hosted web frontend
- Added `notebooks/virtual_tryon_demo.ipynb`, a runnable, dependency-light walkthrough of `tryon.cli.runner.invoke_model()` for the `vton` service (dry-run by default, no API key required to execute)

### Added

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

[0.0.2]: https://github.com/tryonlabs/opentryon/releases/tag/v0.0.2
[0.0.1]: https://github.com/tryonlabs/opentryon/releases/tag/v0.0.1

