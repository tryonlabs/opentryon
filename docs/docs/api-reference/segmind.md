# Segmind Virtual Try-On API

The `SegmindVTONAdapter` provides an interface to Segmind's Try-On Diffusion API for generating realistic virtual try-on images.

## Overview

Segmind's Try-On Diffusion API combines a model image (person) with a cloth image (garment/product) to create realistic virtual try-on results. The adapter handles authentication, image preparation, and response decoding automatically.

**API Endpoint:** `https://api.segmind.com/v1/try-on-diffusion`

**Reference:** [Segmind API Documentation](https://www.segmind.com/models/try-on-diffusion/api)

## Installation

No additional installation required. The adapter uses the `requests` library which is included with OpenTryOn.

## Authentication

Segmind requires an API key for authentication. You can provide it in two ways:

1. **Environment Variable** (Recommended):
   ```bash
   export SEGMIND_API_KEY="your_api_key"
   ```

2. **Constructor Parameter**:
   ```python
   adapter = SegmindVTONAdapter(api_key="your_api_key")
   ```

## Quick Start

```python
from dotenv import load_dotenv
load_dotenv()

from tryon.api import SegmindVTONAdapter

# Initialize adapter (uses SEGMIND_API_KEY from environment)
adapter = SegmindVTONAdapter()

# Generate virtual try-on images
images = adapter.generate_and_decode(
    model_image="data/person.jpg",
    cloth_image="data/shirt.jpg",
    category="Upper body"
)

# Save results
for idx, image in enumerate(images):
    image.save(f"outputs/result_{idx}.png")
```

## API Reference

### Class: `SegmindVTONAdapter`

Adapter class for Segmind Try-On Diffusion API.

#### Constructor

```python
SegmindVTONAdapter(api_key: Optional[str] = None)
```

**Parameters:**
- `api_key` (str, optional): Segmind API key. Defaults to `SEGMIND_API_KEY` environment variable. If not provided, raises `ValueError`.

**Raises:**
- `ValueError`: If API key is not provided via parameter or environment variable.

**Example:**
```python
# Using environment variable
import os
os.environ['SEGMIND_API_KEY'] = 'your_api_key'
adapter = SegmindVTONAdapter()

# Using parameter
adapter = SegmindVTONAdapter(api_key="your_api_key")
```

#### Methods

##### `generate(model_image, cloth_image, category="Upper body", num_inference_steps=None, guidance_scale=None, seed=None, base64=True, **kwargs)`

Generate virtual try-on image(s) using Segmind API.

**Parameters:**
- `model_image` (str or io.BytesIO): Model/person image in one of these formats:
  - File path (str): Path to local image file
  - URL (str): HTTP/HTTPS URL to image
  - File-like object (io.BytesIO): BytesIO or similar
  - Base64 string (str): Base64-encoded image
- `cloth_image` (str or io.BytesIO): Cloth/garment image in same formats as `model_image`
- `category` (str): Garment category. Options: `"Upper body"`, `"Lower body"`, `"Dress"`. Default: `"Upper body"`
- `num_inference_steps` (int, optional): Number of denoising steps. Default: `25`. Range: 20-100
- `guidance_scale` (float, optional): Scale for classifier-free guidance. Default: `2`. Range: 1-25
- `seed` (int, optional): Seed for image generation. Default: `-1`. Range: -1 to 999999999999999
- `base64` (bool): Whether to return base64-encoded image. Default: `True`
- `**kwargs`: Additional parameters for Segmind API

**Returns:**
- `Union[str, bytes]`: Generated image data:
  - If `base64=True`: Base64-encoded string
  - If `base64=False`: Raw image bytes

**Raises:**
- `ValueError`: If required parameters are missing, API returns an error, or response format is unexpected

**Example:**
```python
# Using file paths
image_data = adapter.generate(
    model_image="person.jpg",
    cloth_image="hoodie.jpg",
    category="Upper body"
)

# Using URLs
image_data = adapter.generate(
    model_image="https://example.com/person.jpg",
    cloth_image="https://example.com/garment.jpg",
    category="Lower body"
)

# With custom parameters
image_data = adapter.generate(
    model_image="person.jpg",
    cloth_image="dress.jpg",
    category="Dress",
    num_inference_steps=35,
    guidance_scale=2.5,
    seed=42
)
```

##### `generate_and_decode(model_image, cloth_image, category="Upper body", num_inference_steps=None, guidance_scale=None, seed=None, **kwargs)`

Generate virtual try-on images and decode them to PIL Image objects.

**Parameters:**
- `model_image` (str or io.BytesIO): Model/person image (same formats as `generate()`)
- `cloth_image` (str or io.BytesIO): Cloth/garment image (same formats as `generate()`)
- `category` (str): Garment category. Options: `"Upper body"`, `"Lower body"`, `"Dress"`. Default: `"Upper body"`
- `num_inference_steps` (int, optional): Number of denoising steps. Default: `25`
- `guidance_scale` (float, optional): Guidance scale. Default: `2`
- `seed` (int, optional): Seed for generation. Default: `-1`
- `**kwargs`: Additional parameters

**Returns:**
- `List[PIL.Image.Image]`: List of PIL Image objects

**Raises:**
- `ValueError`: If API returns an error or response format is unexpected

**Example:**
```python
images = adapter.generate_and_decode(
    model_image="data/person.jpg",
    cloth_image="data/garment.jpg",
    category="Upper body",
    num_inference_steps=35,
    guidance_scale=2.5,
    seed=42
)

# Save all results
for idx, image in enumerate(images):
    image.save(f"outputs/vton_result_{idx}.png")
```

##### `create_virtual_try_on_payload(model_image, cloth_image, category="Upper body", num_inference_steps=None, guidance_scale=None, seed=None, base64=False, **kwargs)`

Create the payload for virtual try-on request based on Segmind API format.

**Parameters:**
- `model_image` (str): Model/person image (URL or base64)
- `cloth_image` (str): Cloth/garment image (URL or base64)
- `category` (str): Garment category. Default: `"Upper body"`
- `num_inference_steps` (int, optional): Number of denoising steps
- `guidance_scale` (float, optional): Guidance scale
- `seed` (int, optional): Seed for generation
- `base64` (bool): Whether to return base64 output. Default: `False`
- `**kwargs`: Additional parameters

**Returns:**
- `dict`: API request payload dictionary

**Note:** This is a low-level method. Use `generate()` or `generate_and_decode()` for most use cases.

## Garment Categories

Segmind supports three garment categories:

- **`"Upper body"`**: Tops, shirts, jackets, hoodies (default)
- **`"Lower body"`**: Pants, skirts, shorts
- **`"Dress"`**: Dresses, full-body garments

## Inference Parameters

### `num_inference_steps`

Number of denoising steps during generation. More steps generally produce higher quality results but take longer.

- **Default:** `25`
- **Range:** 20-100
- **Recommended:** 25-35 for good quality/speed balance

### `guidance_scale`

Scale for classifier-free guidance. Higher values make the model follow the input more closely.

- **Default:** `2`
- **Range:** 1-25
- **Recommended:** 2-3 for natural results

### `seed`

Seed for random number generation. Use the same seed to reproduce results.

- **Default:** `-1` (random)
- **Range:** -1 to 999999999999999
- **Use case:** Set a specific seed for reproducible results

## Image Input Formats

The adapter supports multiple input formats:

### File Paths

```python
images = adapter.generate_and_decode(
    model_image="data/person.jpg",
    cloth_image="data/garment.jpg"
)
```

### URLs

```python
images = adapter.generate_and_decode(
    model_image="https://example.com/person.jpg",
    cloth_image="https://example.com/garment.jpg"
)
```

### File-like Objects

```python
from io import BytesIO

with open("person.jpg", "rb") as f:
    person_bytes = BytesIO(f.read())

with open("garment.jpg", "rb") as f:
    garment_bytes = BytesIO(f.read())

images = adapter.generate_and_decode(
    model_image=person_bytes,
    cloth_image=garment_bytes
)
```

### Base64 Strings

```python
import base64

with open("person.jpg", "rb") as f:
    person_b64 = base64.b64encode(f.read()).decode()

with open("garment.jpg", "rb") as f:
    garment_b64 = base64.b64encode(f.read()).decode()

images = adapter.generate_and_decode(
    model_image=person_b64,
    cloth_image=garment_b64
)
```

## Complete Example

```python
from dotenv import load_dotenv
load_dotenv()

from tryon.api import SegmindVTONAdapter
from PIL import Image

# Initialize adapter
adapter = SegmindVTONAdapter()

# Generate virtual try-on
images = adapter.generate_and_decode(
    model_image="data/person.jpg",
    cloth_image="data/shirt.jpg",
    category="Upper body",
    num_inference_steps=35,
    guidance_scale=2.5,
    seed=42
)

# Process results
for idx, image in enumerate(images):
    # Save image
    image.save(f"outputs/vton_result_{idx}.png")
    
    # Display image (if in Jupyter)
    # display(image)
    
    # Get image info
    print(f"Image {idx}: {image.size} ({image.mode})")
```

## Error Handling

The adapter raises `ValueError` for common errors:

```python
try:
    images = adapter.generate_and_decode(
        model_image="person.jpg",
        cloth_image="garment.jpg"
    )
except ValueError as e:
    print(f"Error: {e}")
    # Handle error...
```

Common errors:
- Missing API key
- Invalid image format
- API request failure
- Invalid parameters

## Best Practices

### Use Environment Variables

Store your API key securely using environment variables:

```bash
# .env file
SEGMIND_API_KEY=your_api_key_here
```

```python
from dotenv import load_dotenv
load_dotenv()

adapter = SegmindVTONAdapter()  # Uses environment variable
```

### Image Preprocessing

For best results:
- Use high-resolution images (at least 512x512)
- Ensure person image shows full body or relevant body part
- Use clear, well-lit images
- Remove background if possible

### Parameter Tuning

- Start with default parameters (`num_inference_steps=25`, `guidance_scale=2`)
- Increase `num_inference_steps` for higher quality (slower)
- Adjust `guidance_scale` based on desired adherence to input
- Use `seed` for reproducible results during development

## Troubleshooting

### API Key Issues

If you get an authentication error:

1. Verify your API key is correct
2. Check environment variable is set: `echo $SEGMIND_API_KEY`
3. Ensure API key has sufficient credits/quota

### Image Format Issues

If images fail to process:

1. Verify image files exist and are readable
2. Check image format is supported (JPG, PNG)
3. Ensure URLs are accessible (if using URLs)
4. Try converting images to RGB format

### Rate Limiting

If you encounter rate limiting:

1. Reduce request frequency
2. Implement retry logic with exponential backoff
3. Check your API plan limits
4. Contact Segmind support for higher limits

## See Also

- [Virtual Try-On Examples](../examples/virtual-tryon) - Usage examples
- [API Reference Overview](overview) - Complete API reference
- [Segmind Documentation](https://www.segmind.com/models/try-on-diffusion/api) - Official API docs

