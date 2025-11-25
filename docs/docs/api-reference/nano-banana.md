---
sidebar_position: 6
title: Nano Banana (Gemini Image Generation)
description: Generate high-quality images using Google's Gemini image generation models (Nano Banana and Nano Banana Pro)
keywords:
  - nano banana
  - gemini image generation
  - image generation
  - text to image
  - image editing
  - google gemini
  - gemini 2.5 flash
  - gemini 3 pro
---

# Nano Banana (Gemini Image Generation)

Nano Banana provides adapters for Google's Gemini image generation models, enabling text-to-image generation, image editing, multi-image composition, and batch generation.

## Overview

The `tryon.api.nano_banana` module provides two adapters:

- **NanoBananaAdapter**: Gemini 2.5 Flash Image - Fast, efficient, 1024px resolution
- **NanoBananaProAdapter**: Gemini 3 Pro Image Preview - Advanced, up to 4K resolution, search grounding

## Prerequisites

1. **Google Gemini API Key**: 
   - Sign up at [Google AI Studio](https://aistudio.google.com/)
   - Get your API key from [API Keys page](https://aistudio.google.com/app/apikey)
   - Set `GEMINI_API_KEY` environment variable

2. **Install Dependencies**:
   ```bash
   pip install google-genai
   ```

## NanoBananaAdapter (Gemini 2.5 Flash Image)

Fast and efficient image generation optimized for high-volume, low-latency tasks.

### Initialization

```python
from tryon.api.nano_banana import NanoBananaAdapter

# Using environment variable
adapter = NanoBananaAdapter()

# Or specify API key directly
adapter = NanoBananaAdapter(api_key="your_api_key")
```

### Text-to-Image Generation

Generate images from text descriptions.

```python
images = adapter.generate_text_to_image(
    prompt="A stylish fashion model wearing a modern casual outfit in a studio setting",
    aspect_ratio="16:9"  # Optional
)

# Save results
for idx, image in enumerate(images):
    image.save(f"result_{idx}.png")
```

**Parameters:**
- `prompt` (str): Text description of the image to generate
- `aspect_ratio` (str, optional): Aspect ratio. Options: `"1:1"`, `"2:3"`, `"3:2"`, `"3:4"`, `"4:3"`, `"4:5"`, `"5:4"`, `"9:16"`, `"16:9"`, `"21:9"`

**Returns:** `List[Image.Image]` - List of PIL Image objects

### Image Editing

Edit images using text prompts to add, remove, or modify elements.

```python
images = adapter.generate_image_edit(
    image="person.jpg",
    prompt="Change the outfit to a formal business suit",
    aspect_ratio="16:9"  # Optional
)
```

**Parameters:**
- `image` (str/PIL.Image): Input image (file path, URL, PIL Image, or base64)
- `prompt` (str): Text description of edits to make
- `aspect_ratio` (str, optional): Aspect ratio for output

**Returns:** `List[Image.Image]` - List of edited PIL Image objects

### Multi-Image Composition

Combine multiple images with style transfer and composition.

```python
images = adapter.generate_multi_image(
    images=["outfit1.jpg", "outfit2.jpg"],
    prompt="Create a fashion catalog layout combining these clothing styles",
    aspect_ratio="16:9"  # Optional
)
```

**Parameters:**
- `images` (List[str/PIL.Image]): List of input images
- `prompt` (str): Text description of how to combine images
- `aspect_ratio` (str, optional): Aspect ratio for output

**Returns:** `List[Image.Image]` - List of composed PIL Image objects

### Batch Generation

Generate multiple images from multiple prompts.

```python
results = adapter.generate_batch(
    prompts=[
        "A fashion model showcasing summer collection",
        "Professional photography of formal wear",
        "Casual street style outfit on a model"
    ],
    aspect_ratio="16:9"  # Optional
)

# Save all results
for prompt_idx, images in enumerate(results):
    for img_idx, image in enumerate(images):
        image.save(f"batch_{prompt_idx}_{img_idx}.png")
```

**Parameters:**
- `prompts` (List[str]): List of text prompts
- `aspect_ratio` (str, optional): Aspect ratio for all images

**Returns:** `List[List[Image.Image]]` - List of lists, where each inner list contains images for that prompt

### Supported Aspect Ratios

| Aspect Ratio | Resolution | Tokens |
|-------------|------------|--------|
| 1:1 | 1024x1024 | 1290 |
| 2:3 | 832x1248 | 1290 |
| 3:2 | 1248x832 | 1290 |
| 3:4 | 864x1184 | 1290 |
| 4:3 | 1184x864 | 1290 |
| 4:5 | 896x1152 | 1290 |
| 5:4 | 1152x896 | 1290 |
| 9:16 | 768x1344 | 1290 |
| 16:9 | 1344x768 | 1290 |
| 21:9 | 1536x672 | 1290 |

## NanoBananaProAdapter (Gemini 3 Pro Image Preview)

Advanced image generation with 4K resolution support and search grounding.

### Initialization

```python
from tryon.api.nano_banana import NanoBananaProAdapter

# Using environment variable
adapter = NanoBananaProAdapter()

# Or specify API key directly
adapter = NanoBananaProAdapter(api_key="your_api_key")
```

### Text-to-Image Generation

Generate images with 1K, 2K, or 4K resolution.

```python
images = adapter.generate_text_to_image(
    prompt="Professional fashion photography of elegant evening wear on a runway",
    resolution="4K",  # Options: "1K", "2K", "4K"
    aspect_ratio="16:9",
    use_search_grounding=True  # Optional: Use Google Search for real-world grounding
)
```

**Parameters:**
- `prompt` (str): Text description of the image to generate
- `resolution` (str): Resolution level. Options: `"1K"`, `"2K"`, `"4K"`. Default: `"1K"`
- `aspect_ratio` (str, optional): Aspect ratio (same options as Nano Banana)
- `use_search_grounding` (bool, optional): Use Google Search for real-world grounding. Default: `False`

**Returns:** `List[Image.Image]` - List of PIL Image objects

### Image Editing

Edit images with high-resolution output.

```python
images = adapter.generate_image_edit(
    image="person.jpg",
    prompt="Change the outfit to a formal business suit",
    resolution="2K",  # Options: "1K", "2K", "4K"
    aspect_ratio="16:9"
)
```

**Parameters:**
- `image` (str/PIL.Image): Input image
- `prompt` (str): Text description of edits to make
- `resolution` (str): Resolution level. Options: `"1K"`, `"2K"`, `"4K"`. Default: `"1K"`
- `aspect_ratio` (str, optional): Aspect ratio for output

**Returns:** `List[Image.Image]` - List of edited PIL Image objects

### Multi-Image Composition

Compose multiple images with high-resolution output.

```python
images = adapter.generate_multi_image(
    images=["outfit1.jpg", "outfit2.jpg"],
    prompt="Create a fashion catalog layout combining these clothing styles",
    resolution="2K",
    aspect_ratio="16:9"
)
```

**Parameters:**
- `images` (List[str/PIL.Image]): List of input images
- `prompt` (str): Text description of how to combine images
- `resolution` (str): Resolution level. Options: `"1K"`, `"2K"`, `"4K"`. Default: `"1K"`
- `aspect_ratio` (str, optional): Aspect ratio for output

**Returns:** `List[Image.Image]` - List of composed PIL Image objects

### Batch Generation

Generate multiple images in batch with high resolution.

```python
results = adapter.generate_batch(
    prompts=[
        "A fashion model showcasing summer collection",
        "Professional photography of formal wear",
        "Casual street style outfit on a model"
    ],
    resolution="2K",
    aspect_ratio="16:9"
)
```

**Parameters:**
- `prompts` (List[str]): List of text prompts
- `resolution` (str): Resolution level for all images. Options: `"1K"`, `"2K"`, `"4K"`. Default: `"1K"`
- `aspect_ratio` (str, optional): Aspect ratio for all images

**Returns:** `List[List[Image.Image]]` - List of lists, where each inner list contains images for that prompt

### Supported Resolutions and Aspect Ratios

Nano Banana Pro supports the same 10 aspect ratios as Nano Banana, but with resolution-specific dimensions:

| Aspect Ratio | 1K Resolution | 2K Resolution | 4K Resolution |
|-------------|---------------|---------------|----------------|
| 1:1 | 1024x1024 | 2048x2048 | 4096x4096 |
| 16:9 | 1376x768 | 2752x1536 | 5504x3072 |
| 9:16 | 768x1376 | 1536x2752 | 3072x5504 |
| ... | ... | ... | ... |

See the [Gemini Image Generation Documentation](https://ai.google.dev/gemini-api/docs/image-generation) for complete resolution tables.

## Command Line Usage

Use the `image_gen.py` script for command-line image generation:

```bash
# Text-to-image with Nano Banana
python image_gen.py --provider nano-banana --prompt "A stylish fashion model wearing a modern casual outfit"

# Text-to-image with Nano Banana Pro (4K)
python image_gen.py --provider nano-banana-pro --prompt "Professional fashion photography of elegant evening wear" --resolution 4K

# Image editing
python image_gen.py --provider nano-banana --mode edit --image person.jpg --prompt "Change the outfit to a formal business suit"

# Multi-image composition
python image_gen.py --provider nano-banana --mode compose --images outfit1.jpg outfit2.jpg --prompt "Create a fashion catalog layout"

# Batch generation
python image_gen.py --provider nano-banana --batch prompts.txt --output-dir results/
```

## Input Format Support

Both adapters support multiple input formats:

- **File paths**: `"path/to/image.jpg"`
- **URLs**: `"https://example.com/image.jpg"`
- **PIL Images**: `Image.open("image.jpg")`
- **File-like objects**: `io.BytesIO(image_bytes)`
- **Base64 strings**: Base64-encoded image data

## Error Handling

```python
from tryon.api.nano_banana import NanoBananaAdapter

try:
    adapter = NanoBananaAdapter()
    images = adapter.generate_text_to_image("A fashion model showcasing seasonal clothing")
except ValueError as e:
    # Validation errors (missing API key, invalid parameters, etc.)
    print(f"Validation error: {e}")
except ImportError as e:
    # Missing dependencies
    print(f"Import error: {e}. Install google-genai: pip install google-genai")
except Exception as e:
    # API errors, network errors, etc.
    print(f"API error: {e}")
```

## Best Practices

1. **Use Nano Banana for**: High-volume, low-latency tasks, fast iteration
2. **Use Nano Banana Pro for**: Professional production, 4K resolution needs, search grounding
3. **Cache API Key**: Use environment variables instead of hardcoding
4. **Batch Processing**: Use `generate_batch()` for multiple prompts to optimize API calls
5. **Aspect Ratios**: Choose appropriate aspect ratios for your use case
6. **Error Handling**: Always wrap API calls in try-except blocks

## Examples

### Complete Workflow

```python
from tryon.api.nano_banana import NanoBananaAdapter, NanoBananaProAdapter

# Fast generation with Nano Banana
fast_adapter = NanoBananaAdapter()
images = fast_adapter.generate_text_to_image(
    prompt="A stylish fashion model wearing a modern casual outfit",
    aspect_ratio="16:9"
)
images[0].save("fast_result.png")

# High-quality generation with Nano Banana Pro
pro_adapter = NanoBananaProAdapter()
images = pro_adapter.generate_text_to_image(
    prompt="Professional fashion photography of elegant evening wear on a runway",
    resolution="4K",
    aspect_ratio="16:9",
    use_search_grounding=True
)
images[0].save("pro_result.png")
```

### Iterative Refinement

```python
from tryon.api.nano_banana import NanoBananaProAdapter

adapter = NanoBananaProAdapter()

# Initial generation
images = adapter.generate_text_to_image("A fashion model wearing casual street style")
current_image = images[0]

# Refine with editing
images = adapter.generate_image_edit(
    image=current_image,
    prompt="Change to formal evening wear with elegant accessories"
)
refined_image = images[0]
refined_image.save("refined.png")
```

## Reference

- [Gemini Image Generation Documentation](https://ai.google.dev/gemini-api/docs/image-generation)
- [Google AI Studio](https://aistudio.google.com/)
- [API Keys](https://aistudio.google.com/app/apikey)

