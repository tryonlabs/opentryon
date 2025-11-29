---
sidebar_position: 5
title: FLUX.2 Image Generation
description: Generate high-quality images using FLUX.2 [PRO] and FLUX.2 [FLEX] models with text-to-image, image editing, and multi-image composition capabilities.
keywords:
  - FLUX.2
  - FLUX.2 PRO
  - FLUX.2 FLEX
  - image generation
  - text-to-image
  - image editing
  - BFL AI
  - image composition
---

# FLUX.2 Image Generation

FLUX.2 models provide high-quality image generation capabilities through the BFL AI API. This module includes adapters for both FLUX.2 [PRO] and FLUX.2 [FLEX] models, supporting text-to-image generation, image editing, and multi-image composition.

## Overview

- **FLUX.2 [PRO]**: High-quality image generation with standard controls
- **FLUX.2 [FLEX]**: Flexible generation with advanced controls (guidance scale, steps, prompt upsampling)

Both models support:
- Text-to-image generation
- Image editing (prompt + input image)
- Multi-image composition (up to 8 reference images)
- Custom width/height control
- Seed for reproducibility
- Safety tolerance control

## Prerequisites

1. **BFL AI Account**: Sign up at [BFL AI](https://docs.bfl.ai/)
2. **API Key**: Obtain your API key from the BFL AI dashboard
3. **Environment Variable**: Set `BFL_API_KEY` in your `.env` file

```bash
BFL_API_KEY=your_bfl_api_key
```

## Installation

The FLUX.2 adapters are included in the `tryon.api` module. No additional installation is required beyond the base dependencies.

## Quick Start

### FLUX.2 [PRO] - Text-to-Image

```python
from tryon.api import Flux2ProAdapter

# Initialize adapter
adapter = Flux2ProAdapter()

# Generate image from text prompt
images = adapter.generate_text_to_image(
    prompt="A professional fashion model wearing elegant evening wear on a runway",
    width=1024,
    height=1024,
    seed=42
)

# Save result
images[0].save("outputs/flux2_pro_result.png")
```

### FLUX.2 [FLEX] - Advanced Generation

```python
from tryon.api import Flux2FlexAdapter

# Initialize adapter
adapter = Flux2FlexAdapter()

# Generate with advanced controls
images = adapter.generate_text_to_image(
    prompt="A stylish fashion model wearing elegant evening wear",
    width=1024,
    height=1024,
    guidance=7.5,  # Higher guidance = more adherence to prompt
    steps=50,  # More steps = higher quality
    prompt_upsampling=True,
    seed=42
)

images[0].save("outputs/flux2_flex_result.png")
```

## API Reference

### Flux2ProAdapter

#### `__init__(api_key=None, base_url=None)`

Initialize the FLUX.2 [PRO] adapter.

**Parameters:**
- `api_key` (str, optional): BFL API key. Defaults to `BFL_API_KEY` environment variable.
- `base_url` (str, optional): Base URL for BFL API. Defaults to `https://api.bfl.ai`.

**Raises:**
- `ValueError`: If API key is not provided.

**Example:**
```python
# Using environment variable
adapter = Flux2ProAdapter()

# Using parameter
adapter = Flux2ProAdapter(api_key="your_api_key")
```

#### `generate_text_to_image(prompt, width=None, height=None, seed=None, safety_tolerance=2, output_format="png", **kwargs)`

Generate image from text prompt.

**Parameters:**
- `prompt` (str, required): Text description of the image to generate
- `width` (int, optional): Width of output image (minimum: 64)
- `height` (int, optional): Height of output image (minimum: 64)
- `seed` (int, optional): Seed for reproducibility
- `safety_tolerance` (int): Moderation tolerance (0-5). 0 = most strict, 5 = least strict. Default: 2
- `output_format` (str): Output format. Options: "jpeg", "png". Default: "png"
- `**kwargs`: Additional parameters (webhook_url, webhook_secret, etc.)

**Returns:**
- `List[Image.Image]`: List of PIL Image objects

**Example:**
```python
images = adapter.generate_text_to_image(
    prompt="A professional fashion model wearing elegant evening wear",
    width=1024,
    height=1024,
    seed=42
)
```

#### `generate_image_edit(prompt, input_image, width=None, height=None, seed=None, safety_tolerance=2, output_format="png", **kwargs)`

Generate edited image from prompt and input image.

**Parameters:**
- `prompt` (str, required): Text description of how to edit the image
- `input_image` (Union[str, io.BytesIO, Image.Image], required): Input image (file path, URL, PIL Image, file-like object, or base64)
- `width` (int, optional): Width of output image (minimum: 64)
- `height` (int, optional): Height of output image (minimum: 64)
- `seed` (int, optional): Seed for reproducibility
- `safety_tolerance` (int): Moderation tolerance (0-5). Default: 2
- `output_format` (str): Output format. Options: "jpeg", "png". Default: "png"
- `**kwargs`: Additional parameters

**Returns:**
- `List[Image.Image]`: List of PIL Image objects

**Example:**
```python
images = adapter.generate_image_edit(
    prompt="Change the outfit to casual streetwear style",
    input_image="model.jpg",
    width=1024,
    height=1024
)
```

#### `generate_multi_image(prompt, images, width=None, height=None, seed=None, safety_tolerance=2, output_format="png", **kwargs)`

Generate image from multiple input images (composition & style transfer).

**Parameters:**
- `prompt` (str, required): Text description of how to combine/transform the images
- `images` (List[Union[str, io.BytesIO, Image.Image]], required): List of input images (file paths, URLs, PIL Images, file-like objects, or base64). Maximum 8 images supported.
- `width` (int, optional): Width of output image (minimum: 64)
- `height` (int, optional): Height of output image (minimum: 64)
- `seed` (int, optional): Seed for reproducibility
- `safety_tolerance` (int): Moderation tolerance (0-5). Default: 2
- `output_format` (str): Output format. Options: "jpeg", "png". Default: "png"
- `**kwargs`: Additional parameters

**Returns:**
- `List[Image.Image]`: List of PIL Image objects

**Raises:**
- `ValueError`: If more than 8 images are provided.

**Example:**
```python
images = adapter.generate_multi_image(
    prompt="Create a fashion catalog layout combining these clothing styles",
    images=["outfit1.jpg", "outfit2.jpg", "accessories.jpg"],
    width=1024,
    height=1024
)
```

### Flux2FlexAdapter

#### `__init__(api_key=None, base_url=None)`

Initialize the FLUX.2 [FLEX] adapter.

**Parameters:**
- `api_key` (str, optional): BFL API key. Defaults to `BFL_API_KEY` environment variable.
- `base_url` (str, optional): Base URL for BFL API. Defaults to `https://api.bfl.ai`.

**Raises:**
- `ValueError`: If API key is not provided.

#### `generate_text_to_image(prompt, width=None, height=None, seed=None, guidance=3.5, steps=28, prompt_upsampling=True, safety_tolerance=2, output_format="png", **kwargs)`

Generate image from text prompt with advanced controls.

**Parameters:**
- `prompt` (str, required): Text description of the image to generate
- `width` (int, optional): Width of output image (minimum: 64)
- `height` (int, optional): Height of output image (minimum: 64)
- `seed` (int, optional): Seed for reproducibility
- `guidance` (float): Guidance scale (1.5-10). Higher values = more adherence to prompt. Default: 3.5
- `steps` (int): Number of generation steps. More steps = higher quality. Default: 28
- `prompt_upsampling` (bool): Whether to use prompt upsampling. Default: True
- `safety_tolerance` (int): Moderation tolerance (0-5). Default: 2
- `output_format` (str): Output format. Options: "jpeg", "png". Default: "png"
- `**kwargs`: Additional parameters (webhook_url, webhook_secret, input_image_blob_path, etc.)

**Returns:**
- `List[Image.Image]`: List of PIL Image objects

**Raises:**
- `ValueError`: If guidance is not between 1.5 and 10.

**Example:**
```python
images = adapter.generate_text_to_image(
    prompt="A professional fashion model wearing elegant evening wear",
    width=1024,
    height=1024,
    guidance=7.5,
    steps=50,
    prompt_upsampling=True,
    seed=42
)
```

#### `generate_image_edit(prompt, input_image, width=None, height=None, seed=None, guidance=3.5, steps=28, prompt_upsampling=True, safety_tolerance=2, output_format="png", **kwargs)`

Generate edited image from prompt and input image with advanced controls.

**Parameters:**
- `prompt` (str, required): Text description of how to edit the image
- `input_image` (Union[str, io.BytesIO, Image.Image], required): Input image
- `width` (int, optional): Width of output image (minimum: 64)
- `height` (int, optional): Height of output image (minimum: 64)
- `seed` (int, optional): Seed for reproducibility
- `guidance` (float): Guidance scale (1.5-10). Default: 3.5
- `steps` (int): Number of generation steps. Default: 28
- `prompt_upsampling` (bool): Whether to use prompt upsampling. Default: True
- `safety_tolerance` (int): Moderation tolerance (0-5). Default: 2
- `output_format` (str): Output format. Options: "jpeg", "png". Default: "png"
- `**kwargs`: Additional parameters

**Returns:**
- `List[Image.Image]`: List of PIL Image objects

#### `generate_multi_image(prompt, images, width=None, height=None, seed=None, guidance=3.5, steps=28, prompt_upsampling=True, safety_tolerance=2, output_format="png", **kwargs)`

Generate image from multiple input images with advanced controls.

**Parameters:**
- `prompt` (str, required): Text description of how to combine/transform the images
- `images` (List[Union[str, io.BytesIO, Image.Image]], required): List of input images (maximum 8)
- `width` (int, optional): Width of output image (minimum: 64)
- `height` (int, optional): Height of output image (minimum: 64)
- `seed` (int, optional): Seed for reproducibility
- `guidance` (float): Guidance scale (1.5-10). Default: 3.5
- `steps` (int): Number of generation steps. Default: 28
- `prompt_upsampling` (bool): Whether to use prompt upsampling. Default: True
- `safety_tolerance` (int): Moderation tolerance (0-5). Default: 2
- `output_format` (str): Output format. Options: "jpeg", "png". Default: "png"
- `**kwargs`: Additional parameters

**Returns:**
- `List[Image.Image]`: List of PIL Image objects

## Supported Input Formats

All image input parameters accept:
- **File paths** (str): Path to local image file
- **URLs** (str): HTTP/HTTPS URL to image
- **Base64 strings** (str): Base64-encoded image data
- **File-like objects** (io.BytesIO): BytesIO or similar object
- **PIL Images** (Image.Image): PIL Image object

## Async Processing

FLUX.2 API processes requests asynchronously. The adapters automatically:
1. Submit the request and receive a `task_id` and `polling_url`
2. Poll the task status endpoint until completion
3. Return PIL Image objects when the task succeeds
4. Raise errors if the task fails or times out (default timeout: 5 minutes)

## Examples

### Complete Workflow

```python
from tryon.api import Flux2ProAdapter, Flux2FlexAdapter

# FLUX.2 [PRO] - Simple text-to-image
pro_adapter = Flux2ProAdapter()
pro_images = pro_adapter.generate_text_to_image(
    prompt="A professional fashion model wearing elegant evening wear",
    width=1024,
    height=1024
)
pro_images[0].save("outputs/pro_result.png")

# FLUX.2 [FLEX] - Advanced generation
flex_adapter = Flux2FlexAdapter()
flex_images = flex_adapter.generate_text_to_image(
    prompt="A stylish fashion model wearing elegant evening wear",
    width=1024,
    height=1024,
    guidance=8.0,
    steps=50,
    prompt_upsampling=True
)
flex_images[0].save("outputs/flex_result.png")

# Multi-image composition
composition_images = pro_adapter.generate_multi_image(
    prompt="Combine these clothing items into a cohesive fashion outfit",
    images=["top.jpg", "pants.jpg", "jacket.jpg", "shoes.jpg"],
    width=1024,
    height=1024
)
composition_images[0].save("outputs/composition_result.png")
```

### Image Editing

```python
from tryon.api import Flux2FlexAdapter

adapter = Flux2FlexAdapter()

# Edit image with advanced controls
images = adapter.generate_image_edit(
    prompt="Transform the outfit to match a vintage 1920s fashion style",
    input_image="model.jpg",
    guidance=8.0,
    steps=50,
    prompt_upsampling=True,
    seed=42
)

images[0].save("outputs/edited_result.png")
```

## Error Handling

The adapters raise `ValueError` for:
- Missing API key
- Invalid parameters (e.g., guidance out of range)
- API errors (HTTP errors, task failures)
- Timeout errors (task takes too long)
- Invalid image formats

**Example:**
```python
try:
    images = adapter.generate_text_to_image(
        prompt="A fashion model",
        guidance=15  # Invalid: must be between 1.5 and 10
    )
except ValueError as e:
    print(f"Error: {e}")
```

## Best Practices

1. **Prompt Quality**: Write detailed, specific prompts for better results
2. **Guidance Scale**: Start with default (3.5) and adjust based on results
   - Lower (1.5-3): More creative, less strict to prompt
   - Higher (7-10): More strict adherence to prompt
3. **Steps**: More steps = higher quality but slower generation
   - Default (28): Good balance
   - High quality (50+): Slower but better results
4. **Seed**: Use seeds for reproducible results
5. **Safety Tolerance**: Adjust based on your content moderation needs
6. **Multi-Image**: Use up to 8 reference images for best composition results

## References

- [FLUX.2 [PRO] API Documentation](https://docs.bfl.ai/api-reference/models/generate-or-edit-an-image-with-flux2-[pro])
- [FLUX.2 [FLEX] API Documentation](https://docs.bfl.ai/api-reference/models/generate-or-edit-an-image-with-flux2-[flex])
- [FLUX.2 Overview](https://docs.bfl.ai/flux_2/flux2_overview)
- [FLUX.2 Text-to-Image Guide](https://docs.bfl.ai/flux_2/flux2_text_to_image)
- [FLUX.2 Image Editing Guide](https://docs.bfl.ai/flux_2/flux2_image_editing)

