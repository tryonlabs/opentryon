# API Reference

Complete API reference for OpenTryOn modules. **Current package: v0.0.4.**

Models are also available through the unified **CLI**, **MCP server**, and (for upstream media HTTP) **OpenAPI / Postman** snapshots:

- [CLI](../getting-started/cli) · [MCP](../getting-started/mcp) · [OpenAPI & Postman](../getting-started/openapi-swagger)

## Preprocessing API

### `segment_garment`

Segment garments from images using U2Net model.

```python
from tryon.preprocessing import segment_garment

segment_garment(
    inputs_dir: str,
    outputs_dir: str,
    cls: str = "all"
)
```

**Parameters:**
- `inputs_dir` (str): Directory containing input garment images
- `outputs_dir` (str): Directory to save segmented masks
- `cls` (str): Garment class. Options: `"upper"`, `"lower"`, `"dress"`, `"all"`

**Returns:** None (saves masks to output directory)

---

### `extract_garment`

Extract garments from images and prepare for virtual try-on.

```python
from tryon.preprocessing import extract_garment

extract_garment(
    inputs_dir: str,
    outputs_dir: str,
    cls: str = "all",
    resize_to_width: Optional[int] = None
)
```

**Parameters:**
- `inputs_dir` (str): Directory containing input garment images
- `outputs_dir` (str): Directory to save extracted garments
- `cls` (str): Garment class
- `resize_to_width` (int, optional): Resize output width

**Returns:** None (saves extracted garments)

---

### `segment_human`

Segment human subjects from images.

```python
from tryon.preprocessing import segment_human

segment_human(
    image_path: str,
    output_dir: str
)
```

**Parameters:**
- `image_path` (str): Path to input human image
- `output_dir` (str): Directory to save segmented mask

**Returns:** None (saves mask as PNG)

---

### `extract_garment` (Single Image)

Extract garment from a single PIL Image object.

```python
from tryon.preprocessing.extract_garment_new import extract_garment
from PIL import Image

garments = extract_garment(
    image: Image.Image,
    cls: str = "all",
    resize_to_width: Optional[int] = None,
    net: Optional[torch.nn.Module] = None,
    device: Optional[torch.device] = None
)
```

**Parameters:**
- `image` (PIL.Image): Input image object
- `cls` (str): Garment class
- `resize_to_width` (int, optional): Resize output width
- `net` (torch.nn.Module, optional): Pre-loaded U2Net model
- `device` (torch.device, optional): Device to run inference on

**Returns:** Dict[str, PIL.Image] - Dictionary mapping garment class names to PIL Image objects

---

## TryOnDiffusion API

### `Diffusion`

Main diffusion model class.

```python
from tryondiffusion.diffusion import Diffusion

diffusion = Diffusion(
    device: torch.device,
    pose_embed_dim: int,
    time_steps: int = 256,
    beta_start: float = 1e-4,
    beta_end: float = 0.02,
    unet_dim: int = 64,
    noise_input_channel: int = 3,
    beta_ema: float = 0.995
)
```

**Methods:**

- `sample(use_ema: bool, conditional_inputs: tuple) -> torch.Tensor`
- `fit(args)` - Start training
- `prepare(args)` - Prepare data and optimizer

See [TryOnDiffusion Documentation](../tryondiffusion/overview.md) for details.

---

## Virtual Try-On API Adapters

### `SegmindVTONAdapter`

Adapter for Segmind Try-On Diffusion API for virtual try-on generation.

```python
from tryon.api import SegmindVTONAdapter

adapter = SegmindVTONAdapter(api_key="your_api_key")

images = adapter.generate_and_decode(
    model_image="person.jpg",
    cloth_image="garment.jpg",
    category="Upper body"
)
```

**Parameters:**
- `api_key` (str, optional): Segmind API key. Defaults to `SEGMIND_API_KEY` environment variable

**Methods:**
- `generate(model_image, cloth_image, category, ...)` - Generate virtual try-on images
- `generate_and_decode(model_image, cloth_image, category, ...)` - Generate and decode to PIL Images

See [Segmind API Documentation](segmind) for complete details.

---

### `KlingAIVTONAdapter`

Adapter for Kling AI Kolors Virtual Try-On API with asynchronous processing.

```python
from tryon.api import KlingAIVTONAdapter

adapter = KlingAIVTONAdapter(api_key="your_api_key", secret_key="your_secret_key")

images = adapter.generate_and_decode(
    source_image="person.jpg",
    reference_image="garment.jpg",
    model="kolors-virtual-try-on-v1-5"
)
```

**Parameters:**
- `api_key` (str, optional): Kling AI API key. Defaults to `KLING_AI_API_KEY` environment variable
- `secret_key` (str, optional): Kling AI secret key. Defaults to `KLING_AI_SECRET_KEY` environment variable
- `base_url` (str, optional): Base URL for API. Defaults to `KLING_AI_BASE_URL` or Singapore endpoint

**Methods:**
- `generate(source_image, reference_image, model, ...)` - Generate virtual try-on images (returns URLs)
- `generate_and_decode(source_image, reference_image, model, ...)` - Generate and decode to PIL Images
- `query_task_status(task_id)` - Query task status
- `poll_task_until_complete(task_id, ...)` - Poll task until completion

See [Kling AI API Documentation](kling-ai) for complete details.

---

### `AmazonNovaCanvasVTONAdapter`

Adapter for Amazon Nova Canvas Virtual Try-On through AWS Bedrock.

```python
from tryon.api import AmazonNovaCanvasVTONAdapter

adapter = AmazonNovaCanvasVTONAdapter(region="us-east-1")

images = adapter.generate_and_decode(
    source_image="person.jpg",
    reference_image="garment.jpg",
    mask_type="GARMENT",
    garment_class="UPPER_BODY"
)
```

**Parameters:**
- `region` (str, optional): AWS region. Defaults to `AMAZON_NOVA_REGION` or `'us-east-1'`

**Methods:**
- `generate(source_image, reference_image, mask_type, garment_class, ...)` - Generate virtual try-on images
- `generate_and_decode(source_image, reference_image, mask_type, garment_class, ...)` - Generate and decode to PIL Images

See [Nova Canvas API Documentation](nova-canvas) for complete details.

---

### `PImageTryOnAdapter`

Adapter for Pruna AI's P-Image-Try-On API -- multi-garment virtual try-on
(up to 11 garment reference images in one call). Lives under
`tryon.api.vton` and shares `tryon.api.pruna.client.PrunaClient` with the
newer P-Image / P-Video adapters in `tryon.api.pruna`.

```python
from tryon.api.vton import PImageTryOnAdapter

adapter = PImageTryOnAdapter(api_key="your_api_key")

images = adapter.generate_and_decode(
    person_image="person.jpg",
    garment_images=["top.jpg", "bottoms.jpg"],
)
```

**Parameters:**
- `api_key` (str, optional): Pruna API key. Defaults to `PRUNA_API_KEY` environment variable

**Methods:**
- `generate(person_image, garment_images, ...)` - Generate a virtual try-on result (returns a URL)
- `generate_and_decode(person_image, garment_images, ...)` - Generate and decode to PIL Images

See [Pruna AI Documentation](pruna) for complete details (also covers `PImageAdapter`, `PImageIdeogramAdapter`, `PImageEditAdapter`, `PImageUpscaleAdapter`, `PVideoAdapter`, `PVideoReplaceAdapter`, `PVideoAvatarAdapter`, `PVideoAnimateAdapter`). Dedicated page: [P-Image-Ideogram](p-image-ideogram).

---

### `FashnVTONAdapter`

Adapter for FASHN AI virtual try-on (`tryon-max` and `tryon-v1.6`). Lives
under `tryon.api.vton` (use-case directory) rather than a dedicated
`tryon.api.fashn` package.

```python
from tryon.api.vton import FashnVTONAdapter

adapter = FashnVTONAdapter(api_key="your_api_key")

images = adapter.generate_and_decode(
    model_image="person.jpg",
    product_image="garment.jpg",
    model_name="tryon-max",
    resolution="2k",
)
```

**Parameters:**
- `api_key` (str, optional): FASHN API key. Defaults to `FASHN_API_KEY`

**Methods:**
- `generate(model_image, product_image, model_name, ...)` - Run try-on (returns URLs / data URIs)
- `generate_and_decode(model_image, product_image, model_name, ...)` - Generate and decode to PIL Images

See [FASHN AI Virtual Try-On Documentation](fashn) for complete details.

---

## Image Generation API Adapters

### `NanoBananaAdapter`

Adapter for Gemini 2.5 Flash Image (Nano Banana) - fast and efficient image generation.

```python
from tryon.api.nano_banana import NanoBananaAdapter

adapter = NanoBananaAdapter(api_key="your_api_key")

images = adapter.generate_text_to_image(
    prompt="A nano banana dish in a fancy restaurant",
    aspect_ratio="16:9"
)
```

**Parameters:**
- `api_key` (str, optional): Google Gemini API key. Defaults to `GEMINI_API_KEY` environment variable

**Methods:**
- `generate_text_to_image(prompt, aspect_ratio, ...)` - Generate images from text
- `generate_image_edit(image, prompt, aspect_ratio, ...)` - Edit images with text prompts
- `generate_multi_image(images, prompt, aspect_ratio, ...)` - Compose multiple images
- `generate_batch(prompts, aspect_ratio, ...)` - Batch generation

See [Nano Banana API Documentation](nano-banana) for complete details.

---

### `NanoBananaProAdapter`

Adapter for Gemini 3 Pro Image Preview (Nano Banana Pro) - advanced image generation with 4K support.

```python
from tryon.api.nano_banana import NanoBananaProAdapter

adapter = NanoBananaProAdapter(api_key="your_api_key")

images = adapter.generate_text_to_image(
    prompt="A professional nano banana dish",
    resolution="4K",
    aspect_ratio="16:9",
    use_search_grounding=True
)
```

**Parameters:**
- `api_key` (str, optional): Google Gemini API key. Defaults to `GEMINI_API_KEY` environment variable

**Methods:**
- `generate_text_to_image(prompt, resolution, aspect_ratio, use_search_grounding, ...)` - Generate images from text
- `generate_image_edit(image, prompt, resolution, aspect_ratio, ...)` - Edit images with text prompts
- `generate_multi_image(images, prompt, resolution, aspect_ratio, ...)` - Compose multiple images
- `generate_batch(prompts, resolution, aspect_ratio, ...)` - Batch generation

See [Nano Banana API Documentation](nano-banana) for complete details.

---

### `NanoBanana2LiteAdapter`

Adapter for Gemini 3.1 Flash-Lite Image (Nano Banana 2 Lite) -- Google's
fastest and cheapest Gemini image tier (1K resolution only). Also exposes
`generate_virtual_tryon()`, a lightweight try-on convenience method built on
multi-image composition (not the highest-fidelity option -- see the note in
[Nano Banana API Documentation](nano-banana)).

```python
from tryon.api.nano_banana import NanoBanana2LiteAdapter

adapter = NanoBanana2LiteAdapter(api_key="your_api_key")

images = adapter.generate_text_to_image(
    prompt="A fashion model wearing a summer collection",
    aspect_ratio="16:9",
)

# Lightweight virtual try-on
images = adapter.generate_virtual_tryon(
    person="person.jpg",
    garment="jacket.jpg",
    garment_description="olive green bomber jacket",
)
```

**Parameters:**
- `api_key` (str, optional): Google Gemini API key. Defaults to `GEMINI_API_KEY` environment variable

**Methods:**
- `generate_text_to_image(prompt, aspect_ratio, ...)` - Generate images from text (1K only)
- `generate_image_edit(image, prompt, aspect_ratio, ...)` - Edit images with text prompts
- `generate_multi_image(images, prompt, aspect_ratio, ...)` - Compose multiple images
- `generate_virtual_tryon(person, garment, garment_description, ...)` - Lightweight virtual try-on
- `generate_batch(prompts, aspect_ratio, ...)` - Batch generation

See [Nano Banana API Documentation](nano-banana) for complete details.

---

### `Flux2ProAdapter`

Adapter for FLUX.2 [PRO] - high-quality image generation with standard controls.

```python
from tryon.api import Flux2ProAdapter

adapter = Flux2ProAdapter(api_key="your_api_key")

images = adapter.generate_text_to_image(
    prompt="A professional fashion model wearing elegant evening wear",
    width=1024,
    height=1024,
    seed=42
)
```

**Parameters:**
- `api_key` (str, optional): BFL API key. Defaults to `BFL_API_KEY` environment variable

**Methods:**
- `generate_text_to_image(prompt, width, height, seed, safety_tolerance, output_format, ...)` - Generate images from text
- `generate_image_edit(prompt, input_image, width, height, seed, ...)` - Edit images with text prompts
- `generate_multi_image(prompt, images, width, height, seed, ...)` - Compose multiple images (up to 8)

See [FLUX.2 API Documentation](flux2) for complete details.

---

### `Flux2FlexAdapter`

Adapter for FLUX.2 [FLEX] - flexible image generation with advanced controls.

```python
from tryon.api import Flux2FlexAdapter

adapter = Flux2FlexAdapter(api_key="your_api_key")

images = adapter.generate_text_to_image(
    prompt="A stylish fashion model wearing elegant evening wear",
    width=1024,
    height=1024,
    guidance=7.5,  # Higher = more adherence to prompt (1.5-10)
    steps=50,  # More steps = higher quality
    prompt_upsampling=True,
    seed=42
)
```

**Parameters:**
- `api_key` (str, optional): BFL API key. Defaults to `BFL_API_KEY` environment variable

**Methods:**
- `generate_text_to_image(prompt, width, height, seed, guidance, steps, prompt_upsampling, ...)` - Generate images from text with advanced controls
- `generate_image_edit(prompt, input_image, width, height, seed, guidance, steps, ...)` - Edit images with advanced controls
- `generate_multi_image(prompt, images, width, height, seed, guidance, steps, ...)` - Compose multiple images with advanced controls

See [FLUX.2 API Documentation](flux2) for complete details.

---

## Video Generation API Adapters

Also available via the CLI/MCP registry:

| Adapter | CLI model | Docs |
|---|---|---|
| `SeedanceAdapter` | `seedance` | [Seedance & Seedream](seedance-seedream) |
| `LumaRay32Adapter` | `luma-ray-3.2` | [Luma Ray 3.2](luma-ray) |
| `KlingVideoAdapter` | `kling-v3` / `kling-v3-omni` / `kling-v2-5-turbo` | [Kling Video](kling-video) |
| `GrokImagineVideoAdapter` | `grok-imagine-video` | [Grok Imagine](grok-imagine) |
| `LTXVideoAdapter` | `ltx-2.5-api` | [LTX-2.5 API](ltx-2.5) |
| `HailuoVideoAdapter` | `hailuo-2.3` | [Hailuo](hailuo) |
| `MiniMaxH3Adapter` | `minimax-h3` | [MiniMax H3](minimax-h3) |
| `WanVideoAdapter` | `wan-api` / `wan-3.0` | [Wan](wan) |
| `RunwayVideoAdapter` | `runway-gen4.5` | [Runway Gen-4.5](runway-gen4.5) |
| `Cosmos3VideoAdapter` | `cosmos3` | [NVIDIA NIM](nvidia-nim) |
| `SoraVideoAdapter` / `VeoAdapter` / `LumaAIVideoAdapter` | `sora` / `veo` / `luma-video` | existing pages |

Local twins: `LTX25Adapter` (`ltx-2.5`), `MiniMaxH3LocalAdapter` (`minimax-h3-local`), `Wan22Adapter` (`wan-2.2`). Wan 3.0 is API-only.

Image counterparts: `SeedreamAdapter` (`seedream`), `IdeogramAdapter` (`ideogram`), `PImageIdeogramAdapter` (`p-image-ideogram`), `GrokImagineImageAdapter` (`grok-imagine-image`), `MuseImageAdapter` (`muse-image`). Muse Video has no API yet — see [Muse Video](muse-video).

### `GeminiOmniAdapter`

Adapter for Gemini Omni Flash (`gemini-omni-flash-preview`) -- multimodal
video generation and conversational editing via the Interactions API.

```python
from tryon.api.omni import GeminiOmniAdapter

adapter = GeminiOmniAdapter(api_key="your_api_key")

video = adapter.generate_text_to_video(
    prompt="A fashion model walking a runway",
    aspect_ratio="9:16",
)
```

**Parameters:**
- `api_key` (str, optional): Google Gemini API key. Defaults to `GEMINI_API_KEY`

**Methods:**
- `generate_text_to_video(prompt, aspect_ratio, previous_interaction_id, ...)` - Text-to-video (or edit turn)
- `generate_image_to_video(image, prompt, aspect_ratio, reference_images, ...)` - Image-to-video
- `edit_video(prompt, previous_interaction_id, ...)` - Conversational edit of a prior clip

See [Gemini Omni Flash Documentation](gemini-omni) for complete details.

---

## Multimodal Understanding API Adapters

### `KimiUnderstandAdapter`

Adapter for Moonshot AI's Kimi K2.6, K2.7 Code, and K3 models -- general-purpose,
natively multimodal image and video understanding (not limited to fashion).

```python
from tryon.api import KimiUnderstandAdapter

adapter = KimiUnderstandAdapter()  # kimi-k2.6 by default

result = adapter.understand_image(
    "garment.jpg",
    prompt="Describe this outfit: color, pattern, style, fit, and material."
)
print(result["text"])
```

**Parameters:**
- `api_key` (str, optional): Moonshot API key. Defaults to `MOONSHOT_API_KEY` environment variable
- `model` (str, optional): `"kimi-k2.6"` (default), `"kimi-k2.7-code"`, `"kimi-k2.7-code-highspeed"`, `"kimi-k3"`, or `"kimi-k2.5"`

**Methods:**
- `understand_image(image, prompt, ...)` - Understand one or more images
- `understand_video(video, prompt, ...)` - Understand video content
- `understand(image=None, video=None, prompt=...)` - Single entry point accepting either/both
- `chat(messages, tools=None, ...)` - Multi-turn/tool-calling escape hatch

See [Kimi API Documentation](kimi) for complete details, or the open-weight
[Kimi-VL local model](../local-models/kimi-vl.md) for GPU-only deployment.

---

### `QwenUnderstandAdapter`

Adapter for Alibaba DashScope **Qwen3.8-Max** — native multimodal flagship
(text + image + video → text) with thinking / `reasoning_effort`. OpenTryOn
exposes the **understand** path (plus `chat()` for multi-turn/tools).

```python
from tryon.api import QwenUnderstandAdapter

adapter = QwenUnderstandAdapter()  # qwen3.8-max by default

result = adapter.understand_image(
    "garment.jpg",
    prompt="Describe this outfit: color, pattern, style, fit, and material."
)
print(result["text"])
```

**Parameters:**
- `api_key` (str, optional): Defaults to `DASHSCOPE_API_KEY`
- `model` (str, optional): `"qwen3.8-max"` (default)
- `base_url` (str, optional): Defaults to `QWEN_BASE_URL` or the international DashScope compatible-mode URL

**Methods:**
- `understand_image(image, prompt, ...)` - Understand one or more images
- `understand_video(video, prompt, ...)` - Understand video content
- `understand(image=None, video=None, prompt=...)` - Single entry point accepting either/both
- `chat(messages, tools=None, ...)` - Multi-turn/tool-calling escape hatch

**Series capabilities (vendor):** ~1M context on Max, long video, coding/agent
strengths, structured output and built-in tools on DashScope. Local open
counterpart: `qwen3.8` (`Qwen/Qwen3.8-27B`).

See [Qwen3.8-Max API Documentation](qwen3.8) for complete details, or the
open-weight [Qwen3.8 local model](../local-models/qwen3.8.md) for GPU-only deployment.

---

### `NemotronOmniUnderstandAdapter` / `Cosmos3ReasonerAdapter` / `Cosmos3VideoAdapter`

NVIDIA NIM Path A (`NVIDIA_API_KEY`). Omni and Reasoner are OpenAI-compatible
chat understand models; Cosmos 3 Generator is T2V/I2V infer (`b64_video`).

```python
from tryon.api.nvidia import NemotronOmniUnderstandAdapter, Cosmos3VideoAdapter

print(NemotronOmniUnderstandAdapter().understand(image="garment.jpg")["text"])
mp4 = Cosmos3VideoAdapter().generate_text_to_video("runway walk at dusk")
```

See [NVIDIA NIM](nvidia-nim).

---

### `QwenImageAdapter`

Adapter for Alibaba DashScope **Qwen-Image 3.0** — text-to-image, image
editing (1–3 refs), and person+garment virtual try-on. Same
`DASHSCOPE_API_KEY` as `QwenUnderstandAdapter`.

```python
from tryon.api import QwenImageAdapter

adapter = QwenImageAdapter()  # qwen-image-3.0-pro by default
images = adapter.generate_text_to_image("editorial lookbook, linen trench")
tryon = adapter.generate_virtual_tryon("person.jpg", "garment.jpg")
```

**Parameters:**
- `api_key` (str, optional): Defaults to `DASHSCOPE_API_KEY`
- `model` (str, optional): `"qwen-image-3.0-pro"` (default), `"qwen-image-3.0"`, `"qwen-image-2.0-pro"`, `"qwen-image-2.0"`
- `base_url` (str, optional): Defaults to `QWEN_IMAGE_BASE_URL` or the international DashScope `/api/v1` host

**Methods:**
- `generate_text_to_image(prompt, size=None, n=1, ...)` — T2I
- `generate_image_edit(image, prompt, ...)` — I2I (one image or a list of 1–3)
- `generate_multi_image(images, prompt, ...)` — I2I composition
- `generate_virtual_tryon(person, garment, garment_description=None, ...)` — VTON wrapper

CLI: `opentryon generate|edit|vton --model qwen-image`. Pair with
`understand --model qwen3.8-max` to caption a garment first. Local twin:
`QwenImageLocalAdapter` / `--model qwen-image-local`
([local docs](../local-models/qwen-image.md)).

See [Qwen-Image API Documentation](qwen-image) for complete details.

---

## Background Removal API

### `BEN2BackgroundRemoverAdapter`

Adapter for BEN2 (Background Erase Network 2) - state-of-the-art background removal for fashion and product images.

```python
from tryon.api.ben2 import BEN2BackgroundRemoverAdapter

adapter = BEN2BackgroundRemoverAdapter()

# Single image background removal
result = adapter.remove_background("model.jpg", refine=True)
result[0].save("model_no_bg.png")

# Batch processing
results = adapter.remove_background_batch(
    ["model1.jpg", "model2.jpg", "model3.jpg"],
    refine=True
)
```

**Parameters:**
- `weights_path` (str, optional): Custom weights path. Auto-downloads from Hugging Face if not specified
- `device` (str, optional): Device to use ("cuda" or "cpu"). Auto-detected if not specified

**Methods:**
- `remove_background(image, refine=False)` - Remove background from single image
- `remove_background_batch(images, refine=False)` - Remove background from multiple images
- `load_image(input_data)` - Load image from path, URL, or BytesIO

**Features:**
- Automatic weight download from [Hugging Face](https://huggingface.co/PramaLLC/BEN2)
- GPU acceleration with CUDA support
- Foreground refinement for higher quality edges
- Batch processing for multiple images
- Supports file paths, URLs, BytesIO, and PIL Images

See [BEN2 API Documentation](ben2) for complete details.

---

## Utility Functions

### `convert_to_jpg`

Convert image to JPG format.

```python
from tryon.preprocessing import convert_to_jpg

convert_to_jpg(
    image_path: str,
    output_dir: str,
    size: Optional[tuple] = None
)
```

**Parameters:**
- `image_path` (str): Path to input image
- `output_dir` (str): Directory to save converted JPG
- `size` (tuple, optional): Desired output size (width, height)

For complete API documentation, see individual module documentation.

