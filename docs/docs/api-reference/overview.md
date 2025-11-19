# API Reference

Complete API reference for OpenTryOn modules.

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

