# Quick Start

Get started with OpenTryOn in minutes! This guide will walk you through your first virtual try-on pipeline.

## Prerequisites

- OpenTryOn installed (see [Installation Guide](installation.md))
- Environment variables configured
- Model checkpoints downloaded

## Basic Workflow

### Step 1: Load Environment Variables

```python
from dotenv import load_dotenv
load_dotenv()
```

### Step 2: Import Required Modules

```python
from tryon.preprocessing import (
    segment_garment,
    extract_garment,
    segment_human
)
```

### Step 3: Segment Garment

Segment garments from images using U2Net:

```python
segment_garment(
    inputs_dir="data/original_cloth",
    outputs_dir="data/garment_segmented",
    cls="upper"  # Options: "upper", "lower", "dress", "all"
)
```

### Step 4: Extract Garment

Extract and preprocess garments:

```python
extract_garment(
    inputs_dir="data/original_cloth",
    outputs_dir="data/cloth",
    cls="upper",
    resize_to_width=400
)
```

### Step 5: Segment Human

Isolate human subjects:

```python
segment_human(
    image_path="data/original_human/model.jpg",
    output_dir="data/human_segmented"
)
```

## Complete Example

Here's a complete example that processes a garment and human image:

```python
from dotenv import load_dotenv
load_dotenv()

from tryon.preprocessing import segment_garment, extract_garment, segment_human

# Process garment
print("Segmenting garment...")
segment_garment(
    inputs_dir="data/original_cloth",
    outputs_dir="data/garment_segmented",
    cls="upper"
)

print("Extracting garment...")
extract_garment(
    inputs_dir="data/original_cloth",
    outputs_dir="data/cloth",
    cls="upper",
    resize_to_width=400
)

# Process human
print("Segmenting human...")
segment_human(
    image_path="data/original_human/model.jpg",
    output_dir="data/human_segmented"
)

print("Processing complete!")
```

## Single Image Processing

For processing a single image object:

```python
from PIL import Image
from tryon.preprocessing.extract_garment_new import extract_garment

# Load image
image = Image.open("garment.jpg").convert("RGB")

# Extract garment
garments = extract_garment(
    image=image,
    cls="upper",
    resize_to_width=400
)

# Access extracted garment
if "upper" in garments:
    garments["upper"].save("extracted_upper.jpg")
```

## Using Command Line Interface

You can also use the CLI for batch processing:

```bash
# Segment garment
python main.py --dataset data --action segment_garment --cls upper

# Extract garment
python main.py --dataset data --action extract_garment --cls upper

# Segment human
python main.py --dataset data --action segment_human
```

## Running Demos

OpenTryOn includes interactive Gradio demos:

```bash
# Extract garment demo
python run_demo.py --name extract_garment

# Model swap demo
python run_demo.py --name model_swap

# Outfit generator demo
python run_demo.py --name outfit_generator
```

## Next Steps

- Learn more about [Preprocessing](preprocessing/overview.md)
- Explore [TryOnDiffusion](tryondiffusion/overview.md)
- Check out [Examples](../examples/basic-usage.md)

