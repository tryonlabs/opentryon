# OpenTryOn API Adapters

The `tryon.api` module provides adapters for various virtual try-on and image generation APIs. These adapters offer a unified interface for interacting with different cloud-based AI services, making it easy to switch between providers or use multiple services in your applications.

## Table of Contents

- [Overview](#overview)
- [Virtual Try-On APIs](#virtual-try-on-apis)
  - [Amazon Nova Canvas](#amazon-nova-canvas)
  - [Kling AI](#kling-ai)
  - [Segmind](#segmind)
- [Image Generation APIs](#image-generation-apis)
  - [Nano Banana (Gemini 2.5 Flash Image)](#nano-banana-gemini-25-flash-image)
  - [Nano Banana Pro (Gemini 3 Pro Image Preview)](#nano-banana-pro-gemini-3-pro-image-preview)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [API Comparison](#api-comparison)
- [Common Patterns](#common-patterns)
- [Error Handling](#error-handling)
- [Best Practices](#best-practices)

## Overview

The API adapters in this module follow a consistent design pattern:

- **Unified Interface**: All adapters provide similar methods (`generate()`, `generate_and_decode()`) for consistency
- **Flexible Input**: Support for file paths, URLs, PIL Images, file-like objects, and base64 strings
- **Automatic Handling**: Automatic image format conversion and validation
- **Error Handling**: Comprehensive error messages and validation
- **Environment Variables**: Support for configuration via environment variables

## Virtual Try-On APIs

### Amazon Nova Canvas

Amazon Nova Canvas provides virtual try-on capabilities through AWS Bedrock, allowing you to combine a source image (person) with a reference image (garment) to create realistic try-on results.

**Features:**
- Automatic garment detection and masking
- Custom mask image support
- Multiple garment classes (Upper body, Lower body, Full body, Footwear)
- AWS region support (us-east-1, ap-northeast-1, eu-west-1)
- Maximum image size: 4.1M pixels (2048x2048)

**Reference:** [AWS Blog Post](https://aws.amazon.com/blogs/aws/amazon-nova-canvas-update-virtual-try-on-and-style-options-now-available/)

**Prerequisites:**
- AWS account with Bedrock access
- Nova Canvas model enabled in AWS Bedrock console
- AWS credentials configured (via `.env` or AWS CLI)

**Example:**
```python
from tryon.api import AmazonNovaCanvasVTONAdapter

# Initialize adapter
adapter = AmazonNovaCanvasVTONAdapter(region="us-east-1")

# Generate virtual try-on
images = adapter.generate_and_decode(
    source_image="person.jpg",
    reference_image="shirt.jpg",
    mask_type="GARMENT",  # Options: "GARMENT", "IMAGE"
    garment_class="UPPER_BODY"  # Options: "UPPER_BODY", "LOWER_BODY", "FULL_BODY", "FOOTWEAR"
)

# Save results
for idx, image in enumerate(images):
    image.save(f"result_{idx}.png")
```

**Environment Variables:**
```bash
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AMAZON_NOVA_REGION=us-east-1  # Optional
AMAZON_NOVA_MODEL_ID=amazon.nova-canvas-v1:0  # Optional
```

### Kling AI

Kling AI provides virtual try-on capabilities through their Kolors API, combining a human image with a cloth image to generate realistic try-on results with automatic asynchronous processing.

**Features:**
- Asynchronous task processing with automatic polling
- Multiple model versions (v1, v1-5)
- Maximum image size: 16M pixels (4096x4096)
- Webhook support for async results
- Regional endpoint support

**Reference:** [Kling AI API Documentation](https://app.klingai.com/global/dev/document-api/apiReference/model/functionalityTry)

**Prerequisites:**
- Kling AI account
- API key and secret key from Kling AI Developer Portal

**Example:**
```python
from tryon.api import KlingAIVTONAdapter

# Initialize adapter
adapter = KlingAIVTONAdapter()

# Generate virtual try-on (automatically polls until completion)
images = adapter.generate_and_decode(
    source_image="person.jpg",
    reference_image="shirt.jpg",
    model="kolors-virtual-try-on-v1-5"  # Optional
)

# Save results
images[0].save("result.png")
```

**Environment Variables:**
```bash
KLING_AI_API_KEY=your_api_key
KLING_AI_SECRET_KEY=your_secret_key
KLING_AI_BASE_URL=https://api-singapore.klingai.com  # Optional
```

**Model Versions:**
- `kolors-virtual-try-on-v1`: Original model version
- `kolors-virtual-try-on-v1-5`: Enhanced version (recommended)

### Segmind

Segmind provides virtual try-on capabilities through their Try-On Diffusion API, combining a model image (person) with a cloth image (garment) to create realistic try-on results.

**Features:**
- Fast synchronous processing
- Multiple garment categories (Upper body, Lower body, Dress)
- Customizable inference parameters (steps, guidance scale, seed)
- Simple API key authentication

**Reference:** [Segmind Try-On Diffusion API](https://www.segmind.com/models/try-on-diffusion/api)

**Prerequisites:**
- Segmind account
- API key from Segmind API Portal

**Example:**
```python
from tryon.api import SegmindVTONAdapter

# Initialize adapter
adapter = SegmindVTONAdapter()

# Generate virtual try-on
images = adapter.generate_and_decode(
    model_image="person.jpg",
    cloth_image="shirt.jpg",
    category="Upper body",  # Options: "Upper body", "Lower body", "Dress"
    num_inference_steps=35,  # Optional: 20-100, default: 25
    guidance_scale=2.5,  # Optional: 1-25, default: 2
    seed=42  # Optional: -1 to 999999999999999, default: -1
)

# Save results
images[0].save("result.png")
```

**Environment Variables:**
```bash
SEGMIND_API_KEY=your_api_key
```

**Garment Categories:**
- `"Upper body"`: Tops, shirts, jackets, hoodies (default)
- `"Lower body"`: Pants, skirts, shorts
- `"Dress"`: Dresses, jumpsuits

**Inference Parameters:**
- `num_inference_steps`: Number of denoising steps (20-100, default: 25)
- `guidance_scale`: Classifier-free guidance scale (1-25, default: 2)
- `seed`: Random seed for reproducibility (-1 for random, default: -1)

## Image Generation APIs

### Nano Banana (Gemini 2.5 Flash Image)

Nano Banana is Google's fast and efficient image generation model, optimized for high-volume, low-latency tasks. It generates images at 1024px resolution.

**Features:**
- Text-to-image generation
- Image editing (image + text to image)
- Multi-image composition and style transfer
- Batch generation support
- Multiple aspect ratios (10 options)
- Fast generation times

**Reference:** [Gemini Image Generation Documentation](https://ai.google.dev/gemini-api/docs/image-generation)

**Prerequisites:**
- Google Gemini API key
- `google-genai` Python package

**Example:**
```python
from tryon.api.nano_banana import NanoBananaAdapter

# Initialize adapter
adapter = NanoBananaAdapter()

# Text-to-image
images = adapter.generate_text_to_image(
    prompt="A nano banana dish in a fancy restaurant with a Gemini theme",
    aspect_ratio="16:9"  # Optional
)

# Image editing
images = adapter.generate_image_edit(
    image="cat.jpg",
    prompt="Add a nano-banana to the scene"
)

# Multi-image composition
images = adapter.generate_multi_image(
    images=["image1.jpg", "image2.jpg"],
    prompt="Combine these images with a Gemini theme"
)

# Batch generation
results = adapter.generate_batch([
    "Prompt 1",
    "Prompt 2",
    "Prompt 3"
])

# Save results
images[0].save("result.png")
```

**Environment Variables:**
```bash
GEMINI_API_KEY=your_api_key
```

**Supported Aspect Ratios:**
- `"1:1"` (1024x1024)
- `"2:3"` (832x1248)
- `"3:2"` (1248x832)
- `"3:4"` (864x1184)
- `"4:3"` (1184x864)
- `"4:5"` (896x1152)
- `"5:4"` (1152x896)
- `"9:16"` (768x1344)
- `"16:9"` (1344x768)
- `"21:9"` (1536x672)

### Nano Banana Pro (Gemini 3 Pro Image Preview)

Nano Banana Pro is Google's advanced image generation model designed for professional asset production. It features real-world grounding using Google Search, default "Thinking" process, and can generate images up to 4K resolution.

**Features:**
- Text-to-image generation with 1K/2K/4K resolution support
- Image editing (image + text to image)
- Multi-image composition and style transfer
- Batch generation support
- Search grounding (real-world grounding using Google Search)
- High-fidelity text rendering
- Up to 4K resolution output

**Reference:** [Gemini Image Generation Documentation](https://ai.google.dev/gemini-api/docs/image-generation)

**Prerequisites:**
- Google Gemini API key
- `google-genai` Python package

**Example:**
```python
from tryon.api.nano_banana import NanoBananaProAdapter

# Initialize adapter
adapter = NanoBananaProAdapter()

# Text-to-image with 4K resolution
images = adapter.generate_text_to_image(
    prompt="A professional nano banana dish in a fancy restaurant",
    resolution="4K",  # Options: "1K", "2K", "4K"
    aspect_ratio="16:9",
    use_search_grounding=True  # Optional: Use Google Search for real-world grounding
)

# Image editing with 2K resolution
images = adapter.generate_image_edit(
    image="cat.jpg",
    prompt="Add a nano-banana to the scene",
    resolution="2K"
)

# Multi-image composition
images = adapter.generate_multi_image(
    images=["image1.jpg", "image2.jpg"],
    prompt="Combine these images with a Gemini theme",
    resolution="2K"
)

# Batch generation
results = adapter.generate_batch(
    prompts=["Prompt 1", "Prompt 2", "Prompt 3"],
    resolution="2K"
)

# Save results
images[0].save("result.png")
```

**Environment Variables:**
```bash
GEMINI_API_KEY=your_api_key
```

**Supported Resolutions:**
- `"1K"`: Standard resolution (varies by aspect ratio)
- `"2K"`: High resolution (varies by aspect ratio)
- `"4K"`: Ultra-high resolution (varies by aspect ratio)

**Supported Aspect Ratios:** Same as Nano Banana (10 options), with resolution-specific dimensions.

## Installation

### Core Dependencies

```bash
pip install pillow requests
```

### Provider-Specific Dependencies

**Amazon Nova Canvas:**
```bash
pip install boto3
```

**Kling AI:**
```bash
pip install PyJWT
```

**Nano Banana / Nano Banana Pro:**
```bash
pip install google-genai
```

### All Dependencies

```bash
pip install boto3 PyJWT google-genai
```

## Quick Start

### 1. Set Up Environment Variables

Create a `.env` file in your project root:

```bash
# Amazon Nova Canvas
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AMAZON_NOVA_REGION=us-east-1

# Kling AI
KLING_AI_API_KEY=your_api_key
KLING_AI_SECRET_KEY=your_secret_key

# Segmind
SEGMIND_API_KEY=your_api_key

# Nano Banana / Nano Banana Pro
GEMINI_API_KEY=your_api_key
```

### 2. Basic Usage

```python
from dotenv import load_dotenv
load_dotenv()

from tryon.api import (
    AmazonNovaCanvasVTONAdapter,
    KlingAIVTONAdapter,
    SegmindVTONAdapter
)
from tryon.api.nano_banana import NanoBananaAdapter, NanoBananaProAdapter

# Virtual Try-On
adapter = SegmindVTONAdapter()
images = adapter.generate_and_decode(
    model_image="person.jpg",
    cloth_image="shirt.jpg",
    category="Upper body"
)
images[0].save("vton_result.png")

# Image Generation
image_adapter = NanoBananaAdapter()
images = image_adapter.generate_text_to_image(
    prompt="A nano banana dish in a fancy restaurant"
)
images[0].save("generated_image.png")
```

## API Comparison

| Feature | Amazon Nova Canvas | Kling AI | Segmind | Nano Banana | Nano Banana Pro |
|---------|-------------------|----------|---------|-------------|----------------|
| **Type** | Virtual Try-On | Virtual Try-On | Virtual Try-On | Image Generation | Image Generation |
| **Processing** | Synchronous | Asynchronous | Synchronous | Synchronous | Synchronous |
| **Max Resolution** | 2048x2048 | 4096x4096 | Varies | 1024px | 4K (4096px+) |
| **Mask Support** | Yes (GARMENT/IMAGE) | No | No | N/A | N/A |
| **Garment Classes** | Yes (4 types) | No | Yes (3 types) | N/A | N/A |
| **Batch Support** | No | No | No | Yes | Yes |
| **Image Editing** | No | No | No | Yes | Yes |
| **Multi-Image** | No | No | No | Yes | Yes |
| **Search Grounding** | No | No | No | No | Yes |
| **Cost Model** | AWS Bedrock | Token-based | Per request | Token-based | Token-based |
| **Latency** | Medium | Medium-High | Low | Low | Medium |

## Common Patterns

### Pattern 1: Try Multiple Providers

```python
from tryon.api import (
    AmazonNovaCanvasVTONAdapter,
    KlingAIVTONAdapter,
    SegmindVTONAdapter
)

def try_multiple_providers(person_img, garment_img):
    results = {}
    
    # Try Segmind (fastest)
    try:
        adapter = SegmindVTONAdapter()
        results['segmind'] = adapter.generate_and_decode(
            model_image=person_img,
            cloth_image=garment_img,
            category="Upper body"
        )
    except Exception as e:
        print(f"Segmind failed: {e}")
    
    # Try Kling AI (best quality)
    try:
        adapter = KlingAIVTONAdapter()
        results['kling'] = adapter.generate_and_decode(
            source_image=person_img,
            reference_image=garment_img
        )
    except Exception as e:
        print(f"Kling AI failed: {e}")
    
    return results
```

### Pattern 2: Image Preprocessing Pipeline

```python
from tryon.api import SegmindVTONAdapter
from PIL import Image

def preprocess_and_generate(person_path, garment_path):
    # Load and preprocess images
    person_img = Image.open(person_path)
    garment_img = Image.open(garment_path)
    
    # Resize if needed
    person_img = person_img.resize((512, 768))
    garment_img = garment_img.resize((512, 512))
    
    # Generate
    adapter = SegmindVTONAdapter()
    images = adapter.generate_and_decode(
        model_image=person_img,
        cloth_image=garment_img,
        category="Upper body"
    )
    
    return images
```

### Pattern 3: Batch Processing with Error Handling

```python
from tryon.api.nano_banana import NanoBananaAdapter

def batch_generate_with_retry(prompts, max_retries=3):
    adapter = NanoBananaAdapter()
    results = []
    
    for prompt in prompts:
        for attempt in range(max_retries):
            try:
                images = adapter.generate_text_to_image(prompt)
                results.append(images)
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"Failed after {max_retries} attempts: {e}")
                    results.append(None)
                else:
                    time.sleep(2 ** attempt)  # Exponential backoff
    
    return results
```

### Pattern 4: Iterative Image Refinement

```python
from tryon.api.nano_banana import NanoBananaProAdapter

def refine_image(initial_prompt, refinement_steps):
    adapter = NanoBananaProAdapter()
    current_image = None
    
    for step in refinement_steps:
        if current_image is None:
            # Initial generation
            images = adapter.generate_text_to_image(initial_prompt)
            current_image = images[0]
        else:
            # Refine existing image
            images = adapter.generate_image_edit(
                image=current_image,
                prompt=step
            )
            current_image = images[0]
    
    return current_image
```

## Error Handling

All adapters provide comprehensive error handling:

```python
from tryon.api import SegmindVTONAdapter

try:
    adapter = SegmindVTONAdapter()
    images = adapter.generate_and_decode(
        model_image="person.jpg",
        cloth_image="shirt.jpg"
    )
except ValueError as e:
    # Validation errors (missing API key, invalid parameters, etc.)
    print(f"Validation error: {e}")
except Exception as e:
    # API errors, network errors, etc.
    print(f"API error: {e}")
```

**Common Error Types:**
- `ValueError`: Invalid parameters, missing credentials, validation errors
- `ImportError`: Missing required dependencies
- `RuntimeError`: API errors, network errors, timeout errors

## Best Practices

### 1. Use Environment Variables

Always use environment variables for API keys and credentials:

```python
import os
from tryon.api import SegmindVTONAdapter

# Good: Use environment variable
adapter = SegmindVTONAdapter()  # Reads from SEGMIND_API_KEY

# Bad: Hardcode API key
adapter = SegmindVTONAdapter(api_key="hardcoded_key")
```

### 2. Validate Images Before Processing

```python
from PIL import Image
from tryon.api import AmazonNovaCanvasVTONAdapter

def validate_and_process(person_path, garment_path):
    # Validate images exist and are valid
    person_img = Image.open(person_path)
    garment_img = Image.open(garment_path)
    
    # Check dimensions
    adapter = AmazonNovaCanvasVTONAdapter()
    adapter.validate_image_size(person_img)
    adapter.validate_image_size(garment_img)
    
    # Process
    images = adapter.generate_and_decode(
        source_image=person_img,
        reference_image=garment_img
    )
    
    return images
```

### 3. Handle Asynchronous Processing

For Kling AI, be aware of asynchronous processing:

```python
from tryon.api import KlingAIVTONAdapter

adapter = KlingAIVTONAdapter()

# This automatically polls until completion (default: 5 minutes)
images = adapter.generate_and_decode(
    source_image="person.jpg",
    reference_image="shirt.jpg"
)

# For custom polling, use generate() and poll manually
task_id = adapter.generate(...)  # Returns task_id
# Custom polling logic...
```

### 4. Optimize for Cost

- Use Nano Banana (Flash) for high-volume, low-latency tasks
- Use Nano Banana Pro only when you need 4K resolution or search grounding
- Cache results when possible
- Batch requests when supported

### 5. Error Recovery

```python
from tryon.api import SegmindVTONAdapter
import time

def generate_with_retry(adapter, max_retries=3, backoff=2):
    for attempt in range(max_retries):
        try:
            return adapter.generate_and_decode(...)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(backoff ** attempt)
```

## Additional Resources

- [OpenTryOn Documentation](https://tryonlabs.github.io/opentryon/)
- [Amazon Nova Canvas Blog Post](https://aws.amazon.com/blogs/aws/amazon-nova-canvas-update-virtual-try-on-and-style-options-now-available/)
- [Kling AI API Documentation](https://app.klingai.com/global/dev/document-api/apiReference/model/functionalityTry)
- [Segmind Try-On Diffusion API](https://www.segmind.com/models/try-on-diffusion/api)
- [Gemini Image Generation Documentation](https://ai.google.dev/gemini-api/docs/image-generation)

## License

All material is made available under [Creative Commons BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/).

---

Made with ❤️ by [TryOn Labs](https://www.tryonlabs.ai)

