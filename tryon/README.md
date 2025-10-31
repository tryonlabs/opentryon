# Try-On Preprocessing Module

The `tryon` module provides comprehensive preprocessing utilities for virtual try-on applications, including garment segmentation, human parsing, and image captioning capabilities.

## 📋 Table of Contents

- [Setup](#setup)
- [Environment Variables](#environment-variables)
- [Core Functions](#core-functions)
  - [Garment Segmentation](#garment-segmentation)
  - [Garment Extraction](#garment-extraction)
  - [Human Segmentation](#human-segmentation)
  - [Image Captioning](#image-captioning)
  - [Utility Functions](#utility-functions)
- [Module Structure](#module-structure)
- [Models](#models)
- [Examples](#examples)

## 🚀 Setup

Before using the tryon module, ensure you have installed all dependencies:

```bash
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in your project's root directory with the following variables:

```env
U2NET_CLOTH_SEGM_CHECKPOINT_PATH=path/to/cloth_segm.pth
U2NET_SEGM_CHECKPOINT_PATH=path/to/u2net.pth
```

**Note**: Download the U2Net checkpoint files:
- Cloth segmentation model: Download from [huggingface-cloth-segmentation](https://github.com/wildoctopus/huggingface-cloth-segmentation)
- Human segmentation model: Download U2Net or U2NetP weights

Load environment variables before running scripts:

```python
from dotenv import load_dotenv
load_dotenv()
```

## 🔧 Core Functions

### Garment Segmentation

Segment garments from images using U2Net model. Supports segmentation of upper garments, lower garments, dresses, or all garment types.

#### Function: `segment_garment`

```python
from tryon.preprocessing import segment_garment

segment_garment(
    inputs_dir="path/to/input/images",
    outputs_dir="path/to/output/segments",
    cls="upper"  # Options: "upper", "lower", "dress", "all"
)
```

**Parameters:**
- `inputs_dir` (str): Directory containing input garment images
- `outputs_dir` (str): Directory to save segmented masks
- `cls` (str): Garment class to segment. Options:
  - `"upper"`: Upper body garments (tops, shirts, jackets)
  - `"lower"`: Lower body garments (pants, skirts)
  - `"dress"`: Full-body dresses
  - `"all"`: Automatically detect and segment all garment types present

**Output:**
- Saves segmentation masks as JPG files with format: `{image_name}_{class_id}.jpg`
- Class IDs: 1=upper, 2=lower, 3=dress

### Garment Extraction

Extract garments from images and prepare them for virtual try-on processing. This function segments garments and extracts them onto a standardized canvas.

#### Function: `extract_garment` (Batch Processing)

```python
from tryon.preprocessing import extract_garment

extract_garment(
    inputs_dir="path/to/input/images",
    outputs_dir="path/to/output/garments",
    cls="upper",  # Options: "upper", "lower", "dress", "all"
    resize_to_width=400  # Optional: resize output width (maintains aspect ratio)
)
```

**Parameters:**
- `inputs_dir` (str): Directory containing input garment images
- `outputs_dir` (str): Directory to save extracted garments
- `cls` (str): Garment class to extract (same options as `segment_garment`)
- `resize_to_width` (int, optional): Resize output images to specified width while maintaining aspect ratio

**Output:**
- Extracted garments centered on a 1024x768 canvas (or resized if specified)
- Images saved as JPG files

#### Function: `extract_garment` (Single Image)

For processing a single image object:

```python
from tryon.preprocessing.extract_garment_new import extract_garment
from PIL import Image

image = Image.open("path/to/image.jpg")
garments = extract_garment(
    image=image,
    cls="upper",
    resize_to_width=400
)

# Returns a dictionary: {"upper": PIL.Image, "lower": PIL.Image, ...}
```

**Parameters:**
- `image` (PIL.Image): Input image object
- `cls` (str): Garment class to extract
- `resize_to_width` (int, optional): Resize output width
- `net` (torch.nn.Module, optional): Pre-loaded U2Net model (for efficiency)
- `device` (torch.device, optional): Device to run inference on

**Returns:**
- Dictionary mapping garment class names to PIL Image objects

### Human Segmentation

Segment human subjects from images using U2Net model. Useful for isolating human figures in virtual try-on pipelines.

#### Function: `segment_human`

```python
from tryon.preprocessing import segment_human

segment_human(
    image_path="path/to/human/image.jpg",
    output_dir="path/to/output/directory"
)
```

**Parameters:**
- `image_path` (str): Path to input human image
- `output_dir` (str): Directory to save segmented human mask

**Output:**
- Saves segmented human mask as PNG file with transparent background
- Mask highlights human subject with gray background (231, 231, 231, 231) for removed areas

### Image Captioning

Generate detailed captions from fashion images using LLaVA-NeXT and Phi-3.5-mini models. Useful for extracting outfit details and generating descriptions.

#### Function: `caption_image`

```python
from tryon.preprocessing.captioning import caption_image
from PIL import Image

image = Image.open("path/to/fashion/image.jpg")
question = "Extract the outfit details as JSON with color, pattern, fit, style, material, type, etc."

json_data, caption = caption_image(
    image=image,
    question=question,
    json_only=False
)

print("JSON:", json_data)
print("Caption:", caption)
```

**Parameters:**
- `image` (PIL.Image): Input fashion image
- `question` (str): Question/prompt for the vision-language model
- `model` (optional): Pre-loaded LLaVA model (for efficiency)
- `processor` (optional): Pre-loaded processor (for efficiency)
- `json_only` (bool): If True, only return JSON data without generating caption

**Returns:**
- `json_data` (dict): Structured JSON data extracted from image
- `generated_caption` (str, optional): Natural language caption if `json_only=False`

**Helper Functions:**

```python
from tryon.preprocessing.captioning import (
    create_llava_next_pipeline,
    create_phi35mini_pipeline,
    convert_outfit_json_to_caption
)

# Create model pipelines
model, processor = create_llava_next_pipeline()
pipe = create_phi35mini_pipeline()

# Convert JSON to caption
json_data = {...}  # Your JSON data
caption = convert_outfit_json_to_caption(json_data, pipe=pipe)
```

### Utility Functions

#### Image Format Conversion

```python
from tryon.preprocessing import convert_to_jpg

convert_to_jpg(
    image_path="path/to/image.png",
    output_dir="path/to/output",
    size=(1024, 768)  # Optional: (width, height)
)
```

**Parameters:**
- `image_path` (str): Path to input image
- `output_dir` (str): Directory to save converted JPG
- `size` (tuple, optional): Desired output size (width, height)

## 📁 Module Structure

```
tryon/
├── __init__.py              # Module initialization
├── preprocessing/           # Preprocessing utilities
│   ├── __init__.py          # Exports: segment_garment, extract_garment, segment_human, convert_to_jpg
│   ├── preprocess_garment.py # Batch garment segmentation and extraction
│   ├── extract_garment_new.py # Single image garment extraction
│   ├── preprocess_human.py   # Human segmentation
│   ├── utils.py             # Image processing utilities
│   ├── captioning/          # Image captioning module
│   │   ├── generate_caption.py # LLaVA-based caption generation
│   ├── u2net/               # U2Net model implementations
│   │   ├── u2net_cloth_segm.py # Cloth segmentation model
│   │   ├── u2net_human_segm.py # Human segmentation model
│   │   ├── load_u2net.py     # Model loading utilities
│   │   └── data_loader.py    # Data loading utilities
│   └── sam2/                 # SAM2 segmentation support (future)
└── models/                  # Model implementations
    └── ootdiffusion/        # OOTDiffusion model setup
        └── setup.sh          # Setup script for OOTDiffusion
```

## 🤖 Models

### U2Net Models

The module uses U2Net architecture for segmentation tasks:

- **Cloth Segmentation**: 4-class segmentation (background, upper, lower, dress)
- **Human Segmentation**: Binary segmentation (background, human)

**Model Requirements:**
- PyTorch
- CUDA support (recommended)
- Model checkpoints (download separately)

### Image Captioning Models

- **LLaVA-NeXT**: Vision-language model for image understanding
  - Model: `llava-hf/llava-v1.6-mistral-7b-hf`
  - Used for extracting structured JSON data from images
- **Phi-3.5-mini**: Text generation model for caption creation
  - Model: `microsoft/Phi-3.5-mini-instruct`
  - Used for converting JSON to natural language captions

## 💡 Examples

### Complete Garment Processing Pipeline

```python
from dotenv import load_dotenv
load_dotenv()

from tryon.preprocessing import segment_garment, extract_garment, segment_human

# 1. Segment garments
segment_garment(
    inputs_dir="data/original_cloth",
    outputs_dir="data/garment_segmented",
    cls="all"
)

# 2. Extract garments
extract_garment(
    inputs_dir="data/original_cloth",
    outputs_dir="data/cloth",
    cls="all",
    resize_to_width=400
)

# 3. Segment human
segment_human(
    image_path="data/original_human/model.jpg",
    output_dir="data/human_segmented"
)
```

### Single Image Processing

```python
from PIL import Image
from tryon.preprocessing.extract_garment_new import extract_garment

# Load image
image = Image.open("garment.jpg").convert("RGB")

# Extract garment
garments = extract_garment(image, cls="upper", resize_to_width=400)

# Access extracted garment
if "upper" in garments:
    garments["upper"].save("extracted_upper.jpg")
```

### Image Captioning Workflow

```python
from PIL import Image
from tryon.preprocessing.captioning import caption_image

# Load fashion image
image = Image.open("outfit.jpg")

# Generate caption with JSON extraction
question = """
Extract outfit details as JSON with the following structure:
{
  "color": "...",
  "pattern": "...",
  "fit": "...",
  "style": "...",
  "material": "...",
  "type": "..."
}
"""

json_data, caption = caption_image(
    image=image,
    question=question,
    json_only=False
)

print("Extracted Details:", json_data)
print("Generated Caption:", caption)
```

### Batch Processing with Progress Tracking

```python
from tryon.preprocessing import extract_garment
from pathlib import Path

# Process multiple garment classes
for cls in ["upper", "lower"]:
    extract_garment(
        inputs_dir=f"data/clothes/{cls}",
        outputs_dir=f"data/processed/{cls}",
        cls=cls,
        resize_to_width=400
    )
```

## 📝 Notes

- **GPU Acceleration**: The module automatically uses CUDA if available, otherwise falls back to CPU
- **Image Formats**: Supports common image formats (JPG, PNG, etc.)
- **Memory Management**: Models are loaded per-process; reuse model instances when processing multiple images for efficiency
- **Batch Processing**: The batch processing functions (`segment_garment`, `extract_garment`) include progress bars for long-running operations

## 🔗 Related Resources

- [U2Net Paper](https://arxiv.org/abs/2005.09007)
- [LLaVA-NeXT](https://github.com/llava-hf/llava-next)
- [OOTDiffusion](https://github.com/tryonlabs/OOTDiffusion)
