# BEN2 - Background Erase Network

BEN2 (Background Erase Network 2) is a state-of-the-art background removal model integrated into OpenTryOn. It provides high-quality background removal for fashion and product images, making it ideal for e-commerce, virtual try-on preprocessing, and product photography.

## Overview

BEN2 uses a transformer-based architecture with window attention mechanisms for precise foreground-background separation. The model automatically downloads weights from Hugging Face on first use.

### Key Features

- **High Precision**: State-of-the-art accuracy for background removal
- **Automatic Weight Download**: Weights automatically downloaded from [Hugging Face](https://huggingface.co/PramaLLC/BEN2)
- **Foreground Refinement**: Optional refinement for higher quality edges
- **Batch Processing**: Process multiple images efficiently
- **Flexible Input**: Accepts file paths, URLs, BytesIO, or PIL Images
- **GPU Acceleration**: CUDA support for faster processing

## Requirements

- **CUDA 11.8+** (recommended for GPU acceleration)
- **PyTorch 2.1+**
- Model weights are automatically cached after first download

## Installation

BEN2 is included with OpenTryOn. The model weights are automatically downloaded on first use:

```bash
pip install opentryon
```

## Quick Start

### Single Image

```python
from tryon.api.ben2 import BEN2BackgroundRemoverAdapter
from PIL import Image

# Initialize adapter (weights download automatically on first use)
adapter = BEN2BackgroundRemoverAdapter()

# Remove background from a single image
result = adapter.remove_background("model.jpg")

# Save the result (PNG with transparency)
result[0].save("model_no_bg.png")
```

### Batch Processing

```python
from tryon.api.ben2 import BEN2BackgroundRemoverAdapter

adapter = BEN2BackgroundRemoverAdapter()

# Process multiple images
images = ["model1.jpg", "model2.jpg", "model3.jpg"]
results = adapter.remove_background_batch(images)

# Save all results
for i, img in enumerate(results):
    img.save(f"output_{i+1}.png")
```

## Command Line Usage

BEN2 can be used directly from the command line:

```bash
# Single image background removal
python bg_remove.py --mode single --image model.jpg --output_dir outputs

# With foreground refinement for higher quality
python bg_remove.py --mode single --image model.jpg --refine

# Batch processing multiple images
python bg_remove.py --mode batch --images model_1.jpg model_2.jpg model_3.jpg

# Batch with refinement
python bg_remove.py --mode batch --images *.jpg --refine --output_dir results
```

### CLI Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--mode` | string | `single` | Processing mode: `single` or `batch` |
| `--image` | string | - | Path/URL for single image mode |
| `--images` | list | - | Multiple paths/URLs for batch mode |
| `--output_dir` | string | `ben2_outputs` | Output directory for results |
| `--refine` | flag | False | Enable foreground refinement |

## Python API

### `BEN2BackgroundRemoverAdapter`

The main adapter class for background removal.

#### Constructor

```python
BEN2BackgroundRemoverAdapter(
    weights_path: str = None,  # Custom weights path (optional)
    device: str = None         # Device: "cuda" or "cpu" (auto-detected)
)
```

#### Methods

##### `remove_background`

Remove background from a single image.

```python
def remove_background(
    self,
    image: Union[str, io.BytesIO, Image.Image],
    refine: bool = False
) -> List[Image.Image]
```

**Parameters:**
- `image`: Input image (file path, URL, BytesIO, or PIL Image)
- `refine`: Enable foreground refinement for higher quality edges

**Returns:**
- List containing a single PIL Image with transparent background

**Example:**

```python
adapter = BEN2BackgroundRemoverAdapter()

# From file path
result = adapter.remove_background("model.jpg")

# From URL
result = adapter.remove_background("https://example.com/model.jpg")

# From PIL Image
from PIL import Image
img = Image.open("model.jpg")
result = adapter.remove_background(img)

# With refinement
result = adapter.remove_background("model.jpg", refine=True)

# Save result
result[0].save("output.png")
```

##### `remove_background_batch`

Remove background from multiple images.

```python
def remove_background_batch(
    self,
    images: List[Union[str, io.BytesIO, Image.Image]],
    refine: bool = False
) -> List[Image.Image]
```

**Parameters:**
- `images`: List of input images (file paths, URLs, BytesIO, or PIL Images)
- `refine`: Enable foreground refinement for all images

**Returns:**
- List of PIL Images with transparent backgrounds

**Example:**

```python
adapter = BEN2BackgroundRemoverAdapter()

# Process multiple images
images = [
    "model1.jpg",
    "model2.jpg",
    "https://example.com/model3.jpg"
]

results = adapter.remove_background_batch(images, refine=True)

# Save all results
for i, img in enumerate(results):
    img.save(f"output_{i+1}.png")

print(f"Processed {len(results)} images")
```

##### `load_image`

Load and normalize image from various input formats.

```python
def load_image(
    self,
    input_data: Union[str, io.BytesIO, Image.Image]
) -> Image.Image
```

**Supported Inputs:**
- File paths (local files)
- URLs (http/https)
- BytesIO / file-like objects
- PIL Image objects

## Use Cases

### Virtual Try-On Preprocessing

Remove backgrounds from garment images before virtual try-on:

```python
from tryon.api.ben2 import BEN2BackgroundRemoverAdapter
from tryon.api import KlingAIVTONAdapter

# Step 1: Remove garment background
bg_adapter = BEN2BackgroundRemoverAdapter()
garment_clean = bg_adapter.remove_background("garment.jpg", refine=True)
garment_clean[0].save("garment_clean.png")

# Step 2: Use cleaned garment for virtual try-on
vton_adapter = KlingAIVTONAdapter()
result = vton_adapter.generate_and_decode(
    source_image="model.jpg",
    reference_image="garment_clean.png"
)
```

### E-Commerce Product Photos

Create professional product photos with transparent backgrounds:

```python
from tryon.api.ben2 import BEN2BackgroundRemoverAdapter
from pathlib import Path

adapter = BEN2BackgroundRemoverAdapter()

# Process all product images in a folder
input_dir = Path("raw_products")
output_dir = Path("processed_products")
output_dir.mkdir(exist_ok=True)

images = list(input_dir.glob("*.jpg"))
results = adapter.remove_background_batch([str(img) for img in images], refine=True)

for img_path, result in zip(images, results):
    output_path = output_dir / f"{img_path.stem}.png"
    result.save(output_path)
    print(f"Processed: {output_path}")
```

### Model Swap Preprocessing

Prepare images for model swapping:

```python
from tryon.api.ben2 import BEN2BackgroundRemoverAdapter

adapter = BEN2BackgroundRemoverAdapter()

# Remove background for cleaner model swap
person_clean = adapter.remove_background("person.jpg", refine=True)
person_clean[0].save("person_clean.png")
```

## Performance Tips

### GPU Acceleration

BEN2 automatically uses CUDA if available:

```python
import torch

# Check if CUDA is available
print(f"CUDA available: {torch.cuda.is_available()}")

# BEN2 will automatically use GPU if available
adapter = BEN2BackgroundRemoverAdapter()  # Auto-detects device

# Or explicitly set device
adapter = BEN2BackgroundRemoverAdapter(device="cuda")  # Force GPU
adapter = BEN2BackgroundRemoverAdapter(device="cpu")   # Force CPU
```

### Batch Processing

For multiple images, batch processing is more efficient:

```python
# Less efficient: processing one by one
for img in images:
    result = adapter.remove_background(img)
    # process result...

# More efficient: batch processing
results = adapter.remove_background_batch(images)
for result in results:
    # process results...
```

### Refinement Trade-offs

The `refine` parameter improves edge quality but increases processing time:

```python
# Fast processing (no refinement)
result = adapter.remove_background("image.jpg", refine=False)

# Higher quality (with refinement) - takes longer
result = adapter.remove_background("image.jpg", refine=True)
```

## Model Architecture

BEN2 uses a Swin Transformer-based architecture with:

- **Window Attention**: Efficient self-attention in local windows
- **Shifted Windows**: Cross-window connections for global context
- **Multi-scale Processing**: Captures both fine details and global structure
- **Foreground Refinement**: Optional post-processing for cleaner edges

The model weights are downloaded from [Hugging Face: PramaLLC/BEN2](https://huggingface.co/PramaLLC/BEN2).

## Troubleshooting

### Common Issues

#### CUDA Out of Memory

For large images on limited GPU memory:

```python
# Use CPU instead
adapter = BEN2BackgroundRemoverAdapter(device="cpu")

# Or resize images before processing
from PIL import Image

img = Image.open("large_image.jpg")
img.thumbnail((2048, 2048))  # Resize to max 2048px
result = adapter.remove_background(img)
```

#### Weights Download Issues

If automatic download fails:

```python
# Manually download weights
import huggingface_hub

huggingface_hub.hf_hub_download(
    repo_id="PramaLLC/BEN2",
    filename="BEN2_Base.pth",
    local_dir="tryon/api/ben2"
)

# Then use custom path
adapter = BEN2BackgroundRemoverAdapter(
    weights_path="tryon/api/ben2/BEN2_Base.pth"
)
```

#### Image Format Issues

BEN2 automatically converts images to RGB:

```python
# RGBA images are converted to RGB automatically
result = adapter.remove_background("image_with_alpha.png")

# Grayscale images are also converted
result = adapter.remove_background("grayscale.jpg")
```

## API Reference Summary

| Method | Description |
|--------|-------------|
| `remove_background(image, refine=False)` | Remove background from single image |
| `remove_background_batch(images, refine=False)` | Remove background from multiple images |
| `load_image(input_data)` | Load image from path, URL, or BytesIO |

## Related Documentation

- [Preprocessing Overview](/preprocessing/overview)
- [Garment Segmentation](/preprocessing/garment-segmentation)
- [Virtual Try-On API](/api-reference/overview)
- [Kling AI](/api-reference/kling-ai)

## References

- [BEN2 on Hugging Face](https://huggingface.co/PramaLLC/BEN2)
- [Swin Transformer Paper](https://arxiv.org/abs/2103.14030)

