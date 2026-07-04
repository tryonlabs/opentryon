---
sidebar_position: 5
title: Adding a New Model Integration
description: Checklist of every code change required to add a new cloud API or open-weight local model to OpenTryOn, including the opentryon CLI.
keywords:
  - contributing
  - new model
  - adapter
  - checklist
  - opentryon CLI
---

# Adding a New Model Integration

This is the checklist we follow whenever a new model/provider (cloud API or
open-weight/local) is added to OpenTryOn. Use it as a PR checklist -- most
integrations touch every item below.

## 1. Decide where the adapter lives

| Kind | Location | Pattern |
|---|---|---|
| Cloud API (needs an API key) | `tryon/api/<provider>/` | `tryon/api/kimi/adapter.py` |
| Open-weight / local GPU model | `tryon/models/<model>/` | `tryon/models/kimi_vl/adapter.py` |

Single-file adapters (no extra helpers) can skip the subpackage and live
directly as `tryon/api/<provider>.py` (see `veo.py`, `segmind.py`). Prefer a
subpackage once you have more than one file (adapter + custom model code,
multiple adapter classes, etc.).

## 2. Write the adapter class

Follow the conventions already used across the repo so every adapter feels
the same to callers and to the CLI:

- **Constructor**: `__init__(self, api_key: Optional[str] = None, ...)`.
  Fall back to an environment variable when `api_key` isn't passed, and
  raise `ValueError` if it's missing after that. Raise `ImportError` (with
  a `pip install ...` hint) if an optional SDK/library isn't installed --
  see `tryon/api/openAI/image_adapter.py` for the pattern.
- **Flexible input types**: methods that take an image/video should accept
  a file path, URL, `PIL.Image.Image`, raw `bytes`, or `io.BytesIO` (see
  `_load_bytes`/`prepare_image` helpers in existing adapters). Don't force
  callers to pre-load images themselves.
- **Method naming**: match the existing vocabulary so the CLI/registry stay
  uniform --
  `generate_text_to_image` / `generate_image_edit` / `generate_multi_image`
  for image generation, `generate_and_decode` for try-on, `understand` /
  `understand_image` / `understand_video` for understanding models,
  `generate_text_to_video` / `generate_image_to_video` for video.
- **Return types**: prefer `List[Image.Image]` for image outputs (or raw
  `bytes`/`List[bytes]` if decoding needs to stay optional -- see
  `output_kind` below), raw `bytes` for video, and a `dict` (e.g.
  `{"text": ..., "reasoning": ..., "model": ..., "usage": ...}`) for
  understanding/captioning models.
- **Docstring header**: include a one-paragraph summary, a link to the
  provider's API docs, the exact model ids supported, and 1-2 runnable
  examples (module-level docstring, mirrored by every existing adapter).

## 3. Export it from the subpackage `__init__.py`

```python
# tryon/api/<provider>/__init__.py
from .adapter import YourAdapter

__all__ = ["YourAdapter"]
```

## 4. Register the import so `tryon.api` / `tryon.models` stay lazy-safe

- **Cloud adapters**: add an entry to `_LAZY_ATTRS` in `tryon/api/__init__.py`
  (PEP 562 lazy loading). **Never** add a plain top-level
  `from .provider import Adapter` there -- that would force every adapter's
  transitive dependencies (including heavy ones like `torch`/`timm` for
  BEN2) to import just because someone touched `tryon.api`.

  ```python
  _LAZY_ATTRS = {
      ...
      "YourAdapter": ".your_provider",
  }
  ```

- **Local models**: add a normal eager import to `tryon/models/__init__.py`
  (this package already assumes `torch`/`transformers` are installed via the
  `local` extra, so there's no lazy-loading concern here).

## 5. Add dependencies to `setup.py`

- Lightweight SDK/client library (e.g. a REST client, the OpenAI SDK) →
  `install_requires` (core install).
- Heavy ML dependency (torch, transformers, diffusers, a model-specific
  package) → `LOCAL_INFERENCE_DEPS`, which feeds the `local` / `training` /
  `all` extras. Keep `pip install opentryon` free of GPU dependencies.

## 6. Add environment variables

- Add the new variable(s) to `env.template` with a comment explaining where
  to get the key and which CLI models need it.
- Document the same variable in the README's environment/setup section and
  in the adapter's own docs page (see step 9).

## 7. Wire it into the `opentryon` CLI

Add a `ModelSpec` entry to the right service dict in `tryon/cli/registry.py`
(`vton`, `generate`, `edit`, `understand`, `video-generate`, `bg-remove`, or
a new service if it's a genuinely new category):

```python
"your-model": ModelSpec(
    id="your-model", label="Human-readable name",
    import_path="tryon.api.your_provider", class_name="YourAdapter",
    method="generate_text_to_image",  # or whatever public method to call
    output_kind="images",  # "images" | "image_bytes" | "video_bytes" | "text"
    env_hint="YOUR_API_KEY",       # omit for local models
    extra="local",                 # only for GPU/local models
    args=[
        Arg(("--prompt", "-p"), "prompt", required=True, help="Text prompt"),
        ...
    ],
),
```

Watch out for the one recurring gotcha: **`dest` collisions with the
service-level `--model` selector**. If the adapter itself takes a `model=`
kwarg (e.g. a provider-specific model version string), you cannot name the
CLI arg's `dest="model"` -- that's already used by the top-level `--model
<provider>` flag and argparse will silently let one clobber the other. Use
`call_name` to decouple them:

```python
Arg(("--model-version",), "model_version", call_name="model", default="...", choices=[...]),
```

## 8. Validate and test

- Run `python3 -c "from tryon.cli.registry import validate_registry; validate_registry()"`
  (or `tests/test_cli.py`) to catch reserved/duplicate flag or `dest`
  collisions before they ship.
- Add a dry-run check to `tests/test_cli.py` (`--dry-run` prints the
  resolved `Adapter(**init_kwargs).method(**call_kwargs)` call without
  hitting the network/GPU).
- If a cheap/free-tier API call is feasible, gate a real end-to-end test
  behind the relevant env var being set (see `check_flux_vto_real_call` /
  `check_kimi_k26_real_call` in `tests/test_cli.py`) so CI/local runs skip
  it gracefully when the key isn't configured.

## 9. Update documentation

- **README.md**: add the adapter to the relevant section (Virtual Try-On /
  Image Generation / Video Generation / Understanding / Background Removal),
  the CLI service/model table, and the environment variables list.
- **Docusaurus site** (`docs/docs/`):
  - New page under `api-reference/<name>.md` (cloud) or
    `local-models/<name>.md` (local), following the structure of
    `api-reference/flux2.md` / `local-models/flux2-turbo.md`.
  - Add the new page to `docs/sidebars.ts`.
  - Add a short mention to `api-reference/overview.md` or
    `local-models/overview.md`.
  - Update `docs/docs/intro.md`'s feature bullets/keywords if the model adds
    a new capability or domain.
- **CHANGELOG.md**: add an entry under "Added" for the release.

## 10. Sanity-check the full picture

```bash
python3 -c "from tryon.api import YourAdapter"     # lazy import still works
python3 -m tryon.cli.main <service> --model your-model --help
python3 -m tryon.cli.main <service> --model your-model ... --dry-run
python3 tests/test_cli.py
```

If all of the above pass and the docs are updated, the integration is done.
