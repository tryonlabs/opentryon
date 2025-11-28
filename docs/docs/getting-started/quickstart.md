# Quick Start

Get started with OpenTryOn in minutes! This guide will walk you through the key features: **API integrations**, **datasets**, and **preprocessing**.

## Prerequisites

- OpenTryOn installed (see [Installation Guide](installation.md))
- Environment variables configured (see [Configuration Guide](configuration.md))
- API keys for cloud services (optional, for API integrations)

## What You Can Do

OpenTryOn provides three main capabilities:

1. **🔌 API Integrations**: Use cloud-based virtual try-on and image generation APIs
2. **📊 Datasets**: Load and work with fashion datasets (Fashion-MNIST, VITON-HD, Subjects200K)
3. **🛠️ Preprocessing**: Process garments, models, and images for virtual try-on

## Quick Examples

### 1. API Integrations (Virtual Try-On)

Use cloud-based APIs for virtual try-on without local model setup:

```python
from dotenv import load_dotenv
load_dotenv()

from tryon.api import SegmindVTONAdapter, KlingAIVTONAdapter, AmazonNovaCanvasVTONAdapter

# Segmind Try-On Diffusion
adapter = SegmindVTONAdapter()
images = adapter.generate_and_decode(
    model_image="person.jpg",
    cloth_image="shirt.jpg",
    category="Upper body"
)
images[0].save("result.png")

# Kling AI Virtual Try-On
kling_adapter = KlingAIVTONAdapter()
images = kling_adapter.generate_and_decode(
    source_image="person.jpg",
    reference_image="garment.jpg"
)

# Amazon Nova Canvas (AWS Bedrock)
nova_adapter = AmazonNovaCanvasVTONAdapter(region="us-east-1")
images = nova_adapter.generate_and_decode(
    source_image="person.jpg",
    reference_image="garment.jpg",
    mask_type="GARMENT",
    garment_class="UPPER_BODY"
)
```

### 2. Image Generation APIs

Generate images using Google's Nano Banana models:

```python
from tryon.api.nano_banana import NanoBananaAdapter, NanoBananaProAdapter

# Nano Banana (Fast)
adapter = NanoBananaAdapter()
images = adapter.generate_text_to_image(
    prompt="A stylish fashion model wearing elegant evening wear",
    aspect_ratio="16:9"
)

# Nano Banana Pro (4K)
pro_adapter = NanoBananaProAdapter()
images = pro_adapter.generate_text_to_image(
    prompt="Professional fashion photography",
    resolution="4K",
    aspect_ratio="16:9"
)
```

### 3. Datasets

Load and work with fashion datasets:

```python
from tryon.datasets import FashionMNIST, VITONHD, Subjects200K

# Fashion-MNIST (small dataset)
fashion = FashionMNIST(download=True)
(train_images, train_labels), (test_images, test_labels) = fashion.load(normalize=True)

# VITON-HD (large dataset with DataLoader)
from torchvision import transforms
viton = VITONHD(data_dir="./datasets/viton_hd")
transform = transforms.Compose([
    transforms.Resize((512, 384)),
    transforms.ToTensor(),
])
dataloader = viton.get_dataloader(split='train', batch_size=8, transform=transform)

# Subjects200K (from HuggingFace)
subjects = Subjects200K()
hf_dataset = subjects.get_hf_dataset()
dataloader = subjects.get_dataloader(
    batch_size=16,
    collection='collection_2',
    filter_high_quality=True
)
```

### 4. Preprocessing

Process garments, models, and images for virtual try-on:

```python
from tryon.preprocessing import segment_garment, extract_garment, segment_human

# Segment garment
segment_garment(
    inputs_dir="data/original_cloth",
    outputs_dir="data/garment_segmented",
    cls="upper"  # Options: "upper", "lower", "dress", "all"
)

# Extract garment
extract_garment(
    inputs_dir="data/original_cloth",
    outputs_dir="data/cloth",
    cls="upper",
    resize_to_width=400
)

# Segment human
segment_human(
    image_path="data/original_human/model.jpg",
    output_dir="data/human_segmented"
)
```

## Complete Workflow Example

Here's a complete example combining preprocessing, datasets, and APIs:

```python
from dotenv import load_dotenv
load_dotenv()

from tryon.datasets import VITONHD
from tryon.preprocessing import segment_garment, extract_garment
from tryon.api import SegmindVTONAdapter
from torchvision import transforms

# 1. Load dataset
dataset = VITONHD(data_dir="./datasets/viton_hd")
sample = dataset.get_sample(0, split='test')
person_img = sample['person']
clothing_img = sample['clothing']

# 2. Preprocess images
person_img.save("temp_person.jpg")
clothing_img.save("temp_clothing.jpg")

# 3. Use API for virtual try-on
adapter = SegmindVTONAdapter()
result_images = adapter.generate_and_decode(
    model_image="temp_person.jpg",
    cloth_image="temp_clothing.jpg",
    category="Upper body"
)

# 4. Save result
result_images[0].save("vton_result.jpg")
```

## Basic Preprocessing Workflow

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

### Essential Guides

- **[API Reference](../api-reference/overview)**: Complete documentation for all API integrations
  - [Segmind Try-On Diffusion](../api-reference/segmind)
  - [Kling AI Virtual Try-On](../api-reference/kling-ai)
  - [Amazon Nova Canvas](../api-reference/nova-canvas)
  - [Nano Banana Image Generation](../api-reference/nano-banana)

- **[Datasets Module](../datasets/overview)**: Load and work with fashion datasets
  - [Fashion-MNIST](../datasets/fashion-mnist)
  - [VITON-HD](../datasets/viton-hd)
  - [Subjects200K](../datasets/subjects200k)

- **[Preprocessing](../preprocessing/overview)**: Process garments, models, and images
  - [Garment Segmentation](../preprocessing/garment-segmentation)
  - [Garment Extraction](../preprocessing/garment-extraction)
  - [Human Segmentation](../preprocessing/human-segmentation)

### Additional Resources

- [Examples](../examples/basic-usage): Real-world usage examples
- [TryOnDiffusion](../tryondiffusion/overview): Advanced diffusion-based virtual try-on
- [Configuration Guide](configuration): Environment setup and API keys

