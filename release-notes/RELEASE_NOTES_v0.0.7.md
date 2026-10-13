# OpenTryOn v0.0.7 Release Notes

## FASHN catalogue endpoints, fashion-specific models, and a new `classify` service

**Release Date**: 13 October 2026

OpenTryOn v0.0.7 adds **16 registry models** on top of v0.0.6 and one new service category, `classify`. Same CLI / MCP / registry surface — **148 models**, **153 MCP tools** (148 models + 5 discovery / key / planner), up from 132 models / 137 tools. Ten services: `vton`, `generate`, `edit`, `understand`, `video-generate`, `bg-remove`, `tts`, `decide`, `embed`, `classify`.

This release is about **fashion-specific** work: catalogue photography endpoints, fashion retrieval and tagging models, garment extraction, a commercially clean local try-on, and a gate for garments before try-on.

## What's New

### FASHN catalogue endpoints (hosted, same `FASHN_API_KEY` as try-on)

| CLI model | Service | What it does |
|---|---|---|
| `fashn-product-to-model` | `edit` | Product photo → a person wearing it (optional pose/background/face references) |
| `fashn-model-swap` | `edit` | Change the model's identity, keep the outfit and pose |
| `fashn-face-to-model` | `edit` | Headshot → try-on-ready upper-body avatar |
| `fashn-reframe` | `edit` | Expand or crop to a target aspect ratio |
| `fashn-edit` | `edit` | Prompt edit with optional mask / context image |
| `fashn-model-create` | `generate` | Fashion model photo from a prompt |
| `fashn-image-to-video` | `video-generate` | Animate a still, 5 or 10 s |
| `fashn-bg-remove` | `bg-remove` | Transparent-background cut-out |

Product-to-model generates a *new* person and does not replace try-on (`fashn-tryon-max`). Integrated from FASHN's published docs without live calls — confirm credit costs on your account.

### Fashion models (local, open weights)

| Model | Service | What it does | Licence |
|---|---|---|---|
| `marqo-fashionsiglip`, `moda-fashion-distilled` (image-only), `moda-pro-lite`, `zooclaw-fashionsiglip2` | `embed` | Fashion catalogue search by text or by photo | Apache-2.0 / MIT |
| `fashion-florence` | `understand` | Garment photo → JSON `{category, primary_color, material, style_tags}` | MIT |
| `qie-2511-extract-outfit` | `edit` | Worn outfit photo → flat studio mockup (garment extraction) | Apache-2.0 LoRA on Qwen-Image-Edit-2511 |
| `klein-4b-tryon` | `vton` | Try-on LoRA on FLUX.2-klein-4B; person (clothing-agnostic) + top + bottom | Apache-2.0 base **and** LoRA |

### New `classify` service

| Model | What it does |
|---|---|
| `tryon-safety-classifier` | Genlook's SigLIP2 classifier: from all photos of one product, what a try-on would show (`level` ok/revealing/lingerie/adult, `blocked`, `subject`, `swimwear`, `ravewear`). Re-implements the model's inference instead of running its repo code; weights pinned to tag `v1.0`. Apache-2.0 |

`classify` is named-model-only in the planner (no chat intent, no default change).

## Breaking changes

- **Removed 16 deprecated root-level wrapper scripts** — `bg_remove.py`, `caption_images.py`, `gpt_image.py`, `image_gen.py`, `luma_image.py`, `run_ootd.py`, `sora_video.py`, `veo_video.py`, `video_gen.py`, `vton.py`, `fashion_agent.py`, `model_swap_agent.py`, `vton_agent.py`, `luma_video_test.py`, `test_gpt_image.py`, `test_luma.py`. They only printed a deprecation warning and forwarded to copies under `examples/legacy/`, `examples/agents/` and `tests/legacy/`. Anyone running `python vton.py` (etc.) from a checkout now gets file-not-found: use the `opentryon` CLI (for example `opentryon vton --model ...`) or run the copies under `examples/` and `tests/legacy/` directly. `main.py`, `run_demo.py` and `api_server.py` are real scripts and stay. The installed `opentryon` package never shipped these root scripts, so `pip` users are unaffected.
- No changes to existing model ids, flags or defaults, and no new required dependencies (`install_requires` is unchanged from v0.0.6).

## Install / Upgrade

```bash
pip install -U opentryon
# optional local/GPU models (Leffa, CatVTON, Qwen-Image, klein try-on, Fashion Florence, …):
pip install -U "opentryon[local]"
```

Several of the new local models need libraries beyond the shared `[local]` pins — install them in a separate environment:

| Model | Extra install |
|---|---|
| `marqo-fashionsiglip`, `moda-*` | `pip install open_clip_torch` |
| `tryon-safety-classifier` | `pip install open_clip_torch safetensors huggingface_hub` |
| `qie-2511-extract-outfit` | `pip install -U peft diffusers transformers accelerate` |
| `klein-4b-tryon` | `pip install git+https://github.com/huggingface/diffusers.git peft accelerate` (`Flux2KleinPipeline` is not in a stable diffusers release yet) |
| `fashion-florence` | none beyond `[local]`; loads with `trust_remote_code` against the transformers 4.4x line it pins |

From source:

```bash
git checkout v0.0.7
pip install -e .
```

## Quick examples

```bash
opentryon edit --model fashn-product-to-model --image jacket.jpg --prompt "studio background" --resolution 2k
opentryon edit --model fashn-model-swap --model-image look.jpg --prompt "woman with red hair"
opentryon video-generate --model fashn-image-to-video --image look.jpg --duration 5 --resolution 720p
opentryon embed --model marqo-fashionsiglip --image catalogue/*.jpg --query "black leather ankle boots"
opentryon understand --model fashion-florence --image dress.jpg
opentryon edit --model qie-2511-extract-outfit --image model_wearing_look.jpg
opentryon vton --model klein-4b-tryon --person-image person_agnostic.png --top-image shirt.png --bottom-image jeans.png
opentryon classify --model tryon-safety-classifier --image front.jpg back.jpg
```

## Docs

- Site: https://tryonlabs.github.io/opentryon/
- Changelog: [CHANGELOG.md](../CHANGELOG.md)
- CLI: [Unified CLI](https://tryonlabs.github.io/opentryon/getting-started/cli)
- Backlog (includes the 13 Oct 2026 fashion-domain survey): [Integrate next](https://tryonlabs.github.io/opentryon/community/integrate-next)

## Notes

- Restart MCP after upgrade so Studio and other clients see the new tools. TryOn Studio has no capability screens yet for `decide`, `embed` or `classify`; the tools work from any MCP client and the Agent chat (named model).
- The new local models were integrated without a GPU or real weights: they are tested against stubbed pipelines, tokenizers and safetensors files, not end-to-end runs. Vendor-reported benchmark numbers in the docs are not reproduced here. Run a quick sanity check on your own data before relying on them.
- `klein-4b-tryon` is a v1 community LoRA (273 training tuples, no published metrics) and does no clothing segmentation: the person image must be clothing-agnostic, or pass `--mask-image`.
- The safety classifier is one layer of moderation: it classifies products (not people), was trained mostly on western e-commerce photos, and the right threshold depends on your audience.
- **148 models** across services → **153 MCP tools**.

## Links

- PyPI: https://pypi.org/project/opentryon/0.0.7/
- Tag: https://github.com/tryonlabs/opentryon/releases/tag/v0.0.7
- Previous: [v0.0.6](RELEASE_NOTES_v0.0.6.md)
