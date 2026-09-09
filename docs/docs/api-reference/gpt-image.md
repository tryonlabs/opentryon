---
sidebar_position: 7
title: GPT-Image (OpenAI Image Generation)
description: Generate and edit images with OpenAI GPT-Image-1 / 1.5 and ChatGPT Images 2.5 (Flare and Sunburst).
keywords:
  - GPT-Image-1
  - GPT-Image-1.5
  - ChatGPT Images 2.5
  - gpt-image-2.5-flare
  - gpt-image-2.5-sunburst
  - OpenAI image generation
  - image generation
  - text to image
  - image editing
  - mask editing
  - OpenAI
  - GPT Image
---

# GPT-Image (OpenAI Image Generation)

OpenAI's GPT Image models provide high-quality image generation. Use **ChatGPT Images 2.5** (Flare / Sunburst) for new work. `--model gpt-image` stays on GPT-Image-1.5 so existing scripts do not silently jump versions.

## Models Available

- **ChatGPT Images 2.5 Flare** (`gpt-image-2.5-flare`): Fast everyday generation. CLI `--model gpt-image-2.5` (and `--model-version gpt-image-2.5` aliases to Flare).
- **ChatGPT Images 2.5 Sunburst** (`gpt-image-2.5-sunburst`): Precision edits. CLI `--model gpt-image-2.5-sunburst`.
- **GPT-Image-1.5**: Previous generation (CLI `--model gpt-image` default).
- **GPT-Image-1**: Original high-quality model (`--model gpt-image --model-version gpt-image-1`).

## Overview

The `tryon.api.openAI.image_adapter` module provides:

- **GPTImageAdapter**: OpenAI Images API (GPT-Image-1 / 1.5 and ChatGPT Images 2.5 Flare / Sunburst)
- Strong prompt understanding
- Consistent composition and visual accuracy
- Multiple image conditioning
- Transparent background support
- Adjustable quality and input fidelity

## Prerequisites

1. **OpenAI Account**: 
   - Sign up at [OpenAI Platform](https://platform.openai.com/settings/organization/general)
   - Get your API key from [API Keys page](https://platform.openai.com/settings/organization/api-key)
   - Set `OPENAI_API_KEY` environment variable

2. **Install Dependencies**:
   ```bash
   pip install openai pillow
   ```

## Initialization

```python
from tryon.api.openAI.image_adapter import GPTImageAdapter

# Using GPT-Image-1.5 (constructor default — same as CLI --model gpt-image)
adapter = GPTImageAdapter()

# ChatGPT Images 2.5 Flare (everyday; gpt-image-2.5 aliases here)
adapter = GPTImageAdapter(model_version="gpt-image-2.5")

# ChatGPT Images 2.5 Sunburst (precision edits)
adapter = GPTImageAdapter(model_version="gpt-image-2.5-sunburst")

# Explicitly specify GPT-Image-1.5
adapter = GPTImageAdapter(model_version="gpt-image-1.5")

# Use GPT-Image-1 (previous version)
adapter = GPTImageAdapter(model_version="gpt-image-1")

# With explicit API key
adapter = GPTImageAdapter(api_key="your_api_key", model_version="gpt-image-2.5-flare")
```

**Parameters:**
- `api_key` (str, optional): OpenAI API key. Defaults to `OPENAI_API_KEY` environment variable
- `model_version` (str, optional): Images API id. `"gpt-image-1"`, `"gpt-image-1.5"` (constructor default), `"gpt-image-2.5-flare"` / `"gpt-image-2.5"` (Flare), `"gpt-image-2.5-sunburst"`, or dated snapshots `gpt-image-2.5-*-2026-09-08`.

## Text-to-Image Generation

Generate images from text descriptions with customizable size, quality, and background.

```python
images = adapter.generate_text_to_image(
    prompt="A female model in a traditional green saree",
    size="1024x1024",
    quality="high",
    background="opaque",
    n=1
)

# Save results
for idx, image_bytes in enumerate(images):
    with open(f"result_{idx}.png", "wb") as f:
        f.write(image_bytes)
```

**Parameters:**
- `prompt` (str): Text description of the image to generate
- `size` (str, optional): Image size. Options: `"1024x1024"`, `"1536x1024"`, `"1024x1536"`, `"auto"`. Default: `"1024x1024"`
- `quality` (str, optional): Quality level. GPT-Image-1 / 1.5: `"low"`, `"medium"`, `"high"`, `"auto"`. ChatGPT Images 2.5 also accepts `"xhigh"` and `"max"`. Default: `"auto"`
- `background` (str, optional): Background type. Options: `"transparent"`, `"opaque"`, `"auto"`. Default: `"opaque"`
- `n` (int, optional): Number of images to generate (1-10). Default: `1`

**Returns:** `List[bytes]` - List of image data as bytes

## Image Editing

Edit images using text prompts with multiple base images for conditioning.

```python
images = adapter.generate_image_edit(
    images="person.jpg",  # Can be a single path or list of paths
    prompt="Make the hat red and stylish",
    size="1024x1024",
    quality="high",
    input_fidelity="low",
    n=1
)

# Save results
for idx, image_bytes in enumerate(images):
    with open(f"edited_{idx}.png", "wb") as f:
        f.write(image_bytes)
```

**Parameters:**
- `images` (str/List[str]): Input image path(s) or base64-encoded image(s)
- `prompt` (str): Text description of edits to make
- `size` (str, optional): Output image size. Default: `"1024x1024"`
- `quality` (str, optional): Quality level. Default: `"high"`
- `input_fidelity` (str, optional): How closely to preserve input image. Options: `"low"`, `"high"`. Default: `"low"`
- `mask` (str, optional): Mask image path for selective editing
- `n` (int, optional): Number of images to generate. Default: `1`

**Returns:** `List[bytes]` - List of edited image data as bytes

## Mask-Based Editing

Edit specific regions of an image using a mask.

```python
images = adapter.generate_image_edit(
    images="scene.png",
    mask="mask.png",  # Black regions will be edited
    prompt="Replace the masked area with a swimming pool",
    size="1024x1024",
    quality="high"
)
```

**Mask Format:**
- Black pixels (0, 0, 0): Areas to be edited
- White pixels (255, 255, 255): Areas to preserve
- Supported formats: PNG with transparency or grayscale

## Multi-Image Conditioning

Use multiple images as input for more consistent results.

```python
images = adapter.generate_image_edit(
    images=["reference1.jpg", "reference2.jpg", "reference3.jpg"],
    prompt="Create a fashion image combining elements from all reference images",
    size="1536x1024",
    quality="high",
    input_fidelity="high"
)
```

**Benefits:**
- More consistent styling across edits
- Better preservation of specific visual elements
- Enhanced control over the output

## Command Line Usage

Same `OPENAI_API_KEY` as `--model gpt-image`. `--model gpt-image` stays on 1.5.

```bash
# ChatGPT Images 2.5 Flare (everyday)
opentryon generate --model gpt-image-2.5 \
  --prompt "editorial still of a linen trench" --quality high --dry-run

# ChatGPT Images 2.5 Sunburst (precision edits)
opentryon edit --model gpt-image-2.5-sunburst \
  --images person.jpg --prompt "Change the jacket to black leather"

# Previous generation (GPT-Image-1.5)
opentryon generate --model gpt-image \
  --prompt "A fashion model wearing elegant evening wear"
```

## Supported Sizes

| Size | Resolution | Aspect Ratio | Use Case |
|------|------------|--------------|----------|
| 1024x1024 | 1024×1024 | 1:1 (Square) | Profile images, social media posts |
| 1536x1024 | 1536×1024 | 3:2 (Landscape) | Banners, wide photos |
| 1024x1536 | 1024×1536 | 2:3 (Portrait) | Magazine covers, posters |
| auto | Variable | Variable | Automatic based on prompt |

## Quality Options

- **low**: Faster generation, lower cost, good for previews
- **medium**: Balanced quality and speed
- **high**: High quality
- **xhigh** / **max**: ChatGPT Images 2.5 only (highest fidelity / cost)
- **auto**: Automatic quality selection

## Background Options

- **opaque**: Solid background (default)
- **transparent**: PNG with transparency (useful for product images)
- **auto**: Automatic background selection

## Input Fidelity Options

Controls how closely the output preserves the input image details:

- **low**: More creative freedom, larger changes allowed
- **high**: Better preservation of input image structure and details

## Input Format Support

The adapter supports multiple input formats:

- **File paths**: `"path/to/image.jpg"`
- **URLs**: `"https://example.com/image.jpg"`
- **Base64 strings**: Base64-encoded image data
- **Lists**: Multiple images for multi-image conditioning

## Error Handling

```python
from tryon.api.openAI.image_adapter import GPTImageAdapter

try:
    adapter = GPTImageAdapter()
    images = adapter.generate_text_to_image("A fashion model showcasing seasonal clothing")
except ValueError as e:
    # Validation errors (missing API key, invalid parameters, etc.)
    print(f"Validation error: {e}")
except ImportError as e:
    # Missing dependencies
    print(f"Import error: {e}. Install openai: pip install openai")
except Exception as e:
    # API errors, network errors, etc.
    print(f"API error: {e}")
```

## Best Practices

1. **Prompt Writing**: 
   - Be specific and detailed in your prompts
   - Mention style, mood, and composition
   - Include relevant fashion terminology

2. **Quality Selection**:
   - Use `high` quality for final production images
   - Use `medium` for iteration and testing
   - Use `low` for rapid prototyping

3. **Input Fidelity**:
   - Use `high` when you want to preserve the input image structure
   - Use `low` when you want more creative freedom

4. **Transparent Backgrounds**:
   - Set `background="transparent"` for product images
   - Useful for e-commerce and catalog applications

5. **Batch Generation**:
   - Generate multiple variants with `n > 1`
   - Review and select the best result

6. **Multi-Image Conditioning**:
   - Use 2-3 reference images for best results
   - Ensure images are related in style/content

## Examples

### Complete Workflow

```python
from tryon.api.openAI.image_adapter import GPTImageAdapter
import os

adapter = GPTImageAdapter()

# Text-to-image generation
images = adapter.generate_text_to_image(
    prompt="A person wearing a leather jacket with sunglasses",
    size="1024x1024",
    quality="high",
    n=1
)

# Save text-to-image result
os.makedirs("outputs", exist_ok=True)
with open("outputs/text_to_image.png", "wb") as f:
    f.write(images[0])

# Image editing
edited_images = adapter.generate_image_edit(
    images="data/image.png",
    prompt="Make the hat red and stylish",
    size="1024x1024",
    quality="high",
    n=1
)

# Save edited result
with open("outputs/edited_image.png", "wb") as f:
    f.write(edited_images[0])

print(f"Saved {len(images) + len(edited_images)} images.")
```

### Fashion Catalog Generation

```python
from tryon.api.openAI.image_adapter import GPTImageAdapter

adapter = GPTImageAdapter()

# Generate multiple fashion images
prompts = [
    "A model wearing a summer dress in a garden setting",
    "A model in formal business attire in an office",
    "A model in casual streetwear in an urban environment"
]

for idx, prompt in enumerate(prompts):
    images = adapter.generate_text_to_image(
        prompt=prompt,
        size="1536x1024",
        quality="high",
        background="transparent"
    )
    
    with open(f"catalog_{idx}.png", "wb") as f:
        f.write(images[0])
```

### Iterative Refinement

```python
from tryon.api.openAI.image_adapter import GPTImageAdapter

adapter = GPTImageAdapter()

# Initial generation
images = adapter.generate_text_to_image(
    "A fashion model wearing casual street style",
    size="1024x1024",
    quality="high"
)

# Save initial result
with open("initial.png", "wb") as f:
    f.write(images[0])

# Refine with editing
refined_images = adapter.generate_image_edit(
    images="initial.png",
    prompt="Change to formal evening wear with elegant accessories",
    size="1024x1024",
    quality="high",
    input_fidelity="high"
)

# Save refined result
with open("refined.png", "wb") as f:
    f.write(refined_images[0])
```

### Product Image with Transparent Background

```python
from tryon.api.openAI.image_adapter import GPTImageAdapter

adapter = GPTImageAdapter()

# Generate product image with transparent background
images = adapter.generate_text_to_image(
    prompt="A stylish leather handbag with gold hardware, studio lighting",
    size="1024x1024",
    quality="high",
    background="transparent"
)

# Save as PNG with transparency
with open("product.png", "wb") as f:
    f.write(images[0])
```

## API Limits and Quotas

- **Rate Limits**: Varies by OpenAI plan
- **Image Size Limits**: Maximum 1536x1024 or 1024x1536
- **Generation Count**: 1-10 images per request
- **Input Images**: Up to 10 images for multi-image conditioning

Check [OpenAI's pricing page](https://openai.com/pricing) for current rates and limits.

## Model Comparison

### ChatGPT Images 2.5 vs GPT-Image-1.5

| Feature | Flare (`gpt-image-2.5`) | Sunburst | GPT-Image-1.5 (`gpt-image`) |
|---------|-------------------------|----------|-----------------------------|
| Role | Everyday generation | Precision edits | Previous generation |
| Quality extras | `xhigh`, `max` | `xhigh`, `max` | `low`–`high` / `auto` |
| Same API | Images API + `OPENAI_API_KEY` | same | same |

### GPT-Image-1 vs GPT-Image-1.5

| Feature | GPT-Image-1 | GPT-Image-1.5 |
|---------|-------------|---------------|
| Quality | High | Enhanced |
| Prompt Understanding | Strong | Superior |
| Consistency | Good | Excellent |
| Detail Preservation | Good | Better |
| Speed | Fast | Fast |
| Recommended | ✓ | ✓✓ (Latest) |

### Comparison with Other Models

| Feature | GPT-Image-1.5 | GPT-Image-1 | FLUX.2 | Nano Banana |
|---------|---------------|-------------|--------|-------------|
| Max Resolution | 1536×1024 | 1536×1024 | Custom | 4096×4096 |
| Transparent BG | ✅ | ✅ | ❌ | ❌ |
| Multi-Image Input | ✅ | ✅ | ✅ | ✅ |
| Input Fidelity Control | ✅ | ✅ | ✅ | ❌ |
| Mask Editing | ✅ | ✅ | ❌ | ❌ |
| Speed | Fast | Fast | Fast | Very Fast |
| Quality | Very High | High | Very High | High |

## Reference

- [OpenAI Image Generation Documentation](https://platform.openai.com/docs/guides/image-generation)
- [ChatGPT Images 2.5 announcement](https://openai.com/index/introducing-chatgpt-images-2-5/)
- [GPT Image 2.5 Flare](https://developers.openai.com/api/docs/models/gpt-image-2.5-flare)
- [GPT Image 2.5 Sunburst](https://developers.openai.com/api/docs/models/gpt-image-2.5-sunburst)
- [GPT-Image-1.5 Model Card](https://platform.openai.com/docs/models/gpt-image-1.5)
- [OpenAI Platform](https://platform.openai.com/)
- [API Keys](https://platform.openai.com/settings/organization/api-key)
- [OpenAI Pricing](https://openai.com/pricing)


