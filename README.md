# OpenTryOn: Open-source AI toolkit for fashion tech and virtual try-on

[![Documentation](https://img.shields.io/badge/Documentation-Read%20Docs-teal?style=flat-square)](https://tryonlabs.github.io/opentryon/)
[![Discord](https://img.shields.io/badge/Discord-Join%20Chat-blue?style=flat-square&logo=discord)](https://discord.gg/T5mPpZHxkY)
[![License](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg?style=flat-square)](https://creativecommons.org/licenses/by-nc/4.0/)

OpenTryOn is an open-source AI toolkit designed for fashion technology and virtual try-on applications. This project provides a comprehensive suite of tools for garment segmentation, human parsing, pose estimation, and virtual try-on using state-of-the-art diffusion models.

📚 **Documentation**: Comprehensive documentation is available at [https://tryonlabs.github.io/opentryon/](https://tryonlabs.github.io/opentryon/)

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=tryonlabs/opentryon&type=date&legend=top-left)](https://www.star-history.com/#tryonlabs/opentryon&type=date&legend=top-left)

## 🎯 Features

- **Virtual Try-On**: 
  - Amazon Nova Canvas virtual try-on using AWS Bedrock
  - Kling AI virtual try-on using Kolors API
  - Segmind Try-On Diffusion API integration
  - Advanced diffusion-based virtual try-on capabilities using TryOnDiffusion
- **Image Generation**: 
  - Nano Banana (Gemini 2.5 Flash Image) for fast, efficient image generation
  - Nano Banana Pro (Gemini 3 Pro Image Preview) for advanced 4K image generation with search grounding
  - FLUX.2 [PRO] high-quality image generation with text-to-image, image editing, and multi-image composition
  - FLUX.2 [FLEX] flexible image generation with advanced controls (guidance, steps, prompt upsampling)
  - Photon-Flash-1 (Luma AI): Fast and cost efficient image generation, ideal for rapid iteration and scale
  - Photon-1 (Luma AI): High-fidelity default model for professional-grade quality, creativity and detailed prompt handling
  - GPT-Image-1 & GPT-Image-1.5 (OpenAI): High-quality image generation with strong prompt understanding, consistent composition, and reliable visual accuracy. GPT-Image-1.5 offers enhanced quality and better consistency
- **Video Generation**:
  - Luma AI Video Generation Model (Dream Machine): High-quality video generation with text-to-image and image-to-video modes.
- **Datasets Module**: 
  - Fashion-MNIST dataset loader with automatic download
  - VITON-HD dataset loader with lazy loading via PyTorch DataLoader
  - Class-based adapter pattern for easy dataset integration
  - Support for both small and large datasets
- **Garment Preprocessing**: 
  - Garment segmentation using U2Net
  - Garment extraction and preprocessing
  - Human segmentation and parsing
- **Pose Estimation**: OpenPose-based pose keypoint extraction for garments and humans
- **Outfit Generation**: FLUX.1-dev LoRA-based outfit generation from text descriptions
- **Model Swap**: Swap garments on different models
- **Interactive Demos**: Gradio-based web interfaces for all features
- **Preprocessing Pipeline**: Complete preprocessing pipeline for training and inference

## 📋 Table of Contents

- [Documentation](#documentation)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
  - [Datasets Module](#datasets-module)
  - [Virtual Try-On with Amazon Nova Canvas](#virtual-try-on-with-amazon-nova-canvas)
  - [Virtual Try-On with Kling AI](#virtual-try-on-with-kling-ai)
  - [Virtual Try-On with Segmind](#virtual-try-on-with-segmind)
  - [Image Generation with Nano Banana](#image-generation-with-nano-banana)
  - [Image Generation with FLUX.2](#image-generation-with-flux2)
  - [Image Generation with Luma AI](#luma-ai-image-generation)
  - [Image Generation with OpenAI](#image-generation-with-gpt-image-1)
  - [Video Generation with Luma AI](#video-generation-with-luma-ai)
  - [Preprocessing Functions](#preprocessing-functions)
- [Demos](#demos)
- [Project Structure](#project-structure)
- [TryOnDiffusion Roadmap](#tryondiffusion-roadmap)
- [Contributing](#contributing)
- [License](#license)

## 📚 Documentation

**Complete documentation** for OpenTryOn is available at **[https://tryonlabs.github.io/opentryon/](https://tryonlabs.github.io/opentryon/)**

The documentation includes:
- Getting Started guides
- API Reference for all modules
- Usage examples and tutorials
- Datasets documentation (Fashion-MNIST, VITON-HD)
- API adapters documentation (Segmind, Kling AI, Amazon Nova Canvas)
- Interactive demos and examples
- Advanced guides and troubleshooting

Visit the [documentation site](https://tryonlabs.github.io/opentryon/) to explore all features, learn how to use OpenTryOn, and get started quickly!

## 🚀 Installation

### Prerequisites

- Python 3.10
- CUDA-capable GPU (recommended)
- Conda or Miniconda

### Step 1: Clone the Repository

```bash
git clone https://github.com/tryonlabs/opentryon.git
cd opentryon
```

### Step 2: Create Conda Environment

```bash
conda env create -f environment.yml
conda activate opentryon
```

Alternatively, you can install dependencies using pip:

```bash
pip install -r requirements.txt
```

### Step 3: Install Package

```bash
pip install -e .
```

### Step 4: Environment Variables

Create a `.env` file in the project root with the following variables:

```env
U2NET_CLOTH_SEG_CHECKPOINT_PATH=cloth_segm.pth

# AWS Credentials for Amazon Nova Canvas (optional, can use AWS CLI default profile)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AMAZON_NOVA_REGION=us-east-1  # Optional: us-east-1, ap-northeast-1, eu-west-1
AMAZON_NOVA_MODEL_ID=amazon.nova-canvas-v1:0  # Optional

# Kling AI Credentials (required for Kling AI virtual try-on)
KLING_AI_API_KEY=your_kling_api_key
KLING_AI_SECRET_KEY=your_kling_secret_key
KLING_AI_BASE_URL=https://api-singapore.klingai.com  # Optional, defaults to Singapore endpoint

# Segmind Credentials (required for Segmind virtual try-on)
SEGMIND_API_KEY=your_segmind_api_key

# Google Gemini Credentials (required for Nano Banana image generation)
GEMINI_API_KEY=your_gemini_api_key

# BFL API Credentials (required for FLUX.2 image generation)
BFL_API_KEY=your_bfl_api_key

# Luma AI Credentials (required for Luma AI image generation)
LUMA_AI_API_KEY=your_luma_ai_api_key

# OpenAI Credentials (required for OpenAI GPT-Image-1 image generation)
OPENAI_API_KEY=your_openai_api_key
```

**Notes**: 
- Download the U2Net checkpoint file from the [huggingface-cloth-segmentation repository](https://github.com/wildoctopus/huggingface-cloth-segmentation)
- For Amazon Nova Canvas, ensure you have AWS credentials configured (via `.env` file or AWS CLI) and Nova Canvas enabled in your AWS Bedrock console
- For Kling AI, obtain your API key and secret key from the [Kling AI Developer Portal](https://app.klingai.com/global/dev/document-api/apiReference/model/functionalityTry)

- For Segmind, obtain your API key from the [Segmind API Portal](https://www.segmind.com/models/try-on-diffusion/api)
- For Nano Banana, obtain your API key from the [Google AI Studio](https://aistudio.google.com/app/apikey)
- For FLUX.2 models, obtain your API key from [BFL AI](https://docs.bfl.ai/)

- For FLUX.2 models, obtain your API key from [BFL AI](https://docs.bfl.ai/)
- For Luma AI, obtain your API key from [Luma Labs AI](https://lumalabs.ai/api)
- For OpenAI, obtain your API key from [OpenAI Platform](https://platform.openai.com/settings/organization/api-keys) 

## 🎮 Quick Start

### Basic Preprocessing

```python
from dotenv import load_dotenv
load_dotenv()

from tryon.preprocessing import segment_garment, extract_garment, segment_human

# Segment garment
segment_garment(
    inputs_dir="data/original_cloth",
    outputs_dir="data/garment_segmented",
    cls="upper"  # Options: "upper", "lower", "all"
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

### Command Line Interface

```bash
# Segment garment
python main.py --dataset data --action segment_garment --cls upper

# Extract garment
python main.py --dataset data --action extract_garment --cls upper

# Segment human
python main.py --dataset data --action segment_human
```

## 📖 Usage

### Datasets Module

The `tryon.datasets` module provides easy-to-use interfaces for downloading and loading datasets commonly used in fashion and virtual try-on applications. The module uses a class-based adapter pattern for consistency and extensibility.

#### Supported Datasets

- **Fashion-MNIST**: A dataset of Zalando's article images (60K training, 10K test, 10 classes, 28×28 grayscale images)
- **VITON-HD**: A high-resolution virtual try-on dataset (11,647 training pairs, 2,032 test pairs, 1024×768 RGB images)
- **Subjects200K**: A large-scale dataset with 200,000 paired images for subject consistency research (loaded from HuggingFace)

#### Quick Example

```python
from tryon.datasets import FashionMNIST, VITONHD
from torchvision import transforms

# Fashion-MNIST: Small dataset, loads entirely into memory
fashion_dataset = FashionMNIST(download=True)
(train_images, train_labels), (test_images, test_labels) = fashion_dataset.load(
    normalize=True,
    flatten=False
)
print(f"Training set: {train_images.shape}")  # (60000, 28, 28)

# VITON-HD: Large dataset, uses lazy loading via DataLoader
viton_dataset = VITONHD(data_dir="./datasets/viton_hd", download=False)
transform = transforms.Compose([
    transforms.Resize((512, 384)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
])
train_loader = viton_dataset.get_dataloader(
    split='train',
    batch_size=8,
    shuffle=True,
    transform=transform
)

# Subjects200K: Large-scale paired images from HuggingFace
from tryon.datasets import Subjects200K

subjects_dataset = Subjects200K()
hf_dataset = subjects_dataset.get_hf_dataset()
sample = hf_dataset['train'][0]
image = sample['image']  # PIL Image with paired images
collection = sample['collection']  # 'collection_1', 'collection_2', or 'collection_3'

# Get PyTorch DataLoader with quality filtering
dataloader = subjects_dataset.get_dataloader(
    batch_size=16,
    transform=transform,
    collection='collection_2',
    filter_high_quality=True
)
```

#### Documentation

For comprehensive documentation, API reference, usage examples, and best practices, see the [Datasets Module Documentation](tryon/datasets/README.md).

**Key Features:**
- ✅ Automatic download for Fashion-MNIST
- ✅ Lazy loading for large datasets (VITON-HD)
- ✅ PyTorch DataLoader integration
- ✅ Consistent API across datasets
- ✅ Class-based and function-based interfaces
- ✅ Support for custom transforms and preprocessing

### Virtual Try-On with Amazon Nova Canvas

Generate realistic virtual try-on images using Amazon Nova Canvas through AWS Bedrock. This feature combines a source image (person/model) with a reference image (garment/product) to create realistic try-on results.

#### Prerequisites

1. **AWS Account Setup**: 
   - Ensure you have an AWS account with access to Amazon Bedrock
   - Enable Nova Canvas model access in the AWS Bedrock console (Model access section)
   - Configure AWS credentials (via `.env` file or AWS CLI)

2. **Image Requirements**:
   - Maximum image size: 4.1M pixels (equivalent to 2,048 x 2,048)
   - Supported formats: JPG, PNG
   - Both source and reference images must meet size requirements

#### Command Line Usage

```bash
# Basic usage with GARMENT mask (default) - Nova Canvas
python vton.py --provider nova --source data/person.jpg --reference data/garment.jpg

# Specify garment class - Nova Canvas
python vton.py --provider nova --source person.jpg --reference garment.jpg --garment-class LOWER_BODY

# Use IMAGE mask type with custom mask - Nova Canvas
python vton.py --provider nova --source person.jpg --reference garment.jpg --mask-type IMAGE --mask-image mask.png

# Use different AWS region - Nova Canvas
python vton.py --provider nova --source person.jpg --reference garment.jpg --region ap-northeast-1

# Basic usage - Kling AI
python vton.py --provider kling --source person.jpg --reference garment.jpg

# Specify model version - Kling AI
python vton.py --provider kling --source person.jpg --reference garment.jpg --model kolors-virtual-try-on-v1-5

# Basic usage - Segmind
python vton.py --provider segmind --source person.jpg --reference garment.jpg --category "Upper body"

# Specify inference parameters - Segmind
python vton.py --provider segmind --source person.jpg --reference garment.jpg --category "Lower body" --num-steps 35 --guidance-scale 2.5

# Save output to specific directory
python vton.py --provider nova --source person.jpg --reference garment.jpg --output-dir results/
```

#### Python API Usage

```python
from dotenv import load_dotenv
load_dotenv()

from tryon.api import AmazonNovaCanvasVTONAdapter
from PIL import Image

# Initialize adapter
adapter = AmazonNovaCanvasVTONAdapter(region="us-east-1")

# Generate virtual try-on images
images = adapter.generate_and_decode(
    source_image="data/person.jpg",
    reference_image="data/garment.jpg",
    mask_type="GARMENT",  # Options: "GARMENT", "IMAGE"
    garment_class="UPPER_BODY"  # Options: "UPPER_BODY", "LOWER_BODY", "FULL_BODY", "FOOTWEAR"
)

# Save results
for idx, image in enumerate(images):
    image.save(f"outputs/vton_result_{idx}.png")
```

#### Mask Types

1. **GARMENT** (Default): Automatically detects and masks garment area based on garment class
   - `UPPER_BODY`: Tops, shirts, jackets, hoodies
   - `LOWER_BODY`: Pants, skirts, shorts
   - `FULL_BODY`: Dresses, jumpsuits
   - `FOOTWEAR`: Shoes, boots

2. **IMAGE**: Uses a custom black-and-white mask image
   - Black areas = replaced with garment
   - White areas = preserved from source image

#### Supported AWS Regions

- `us-east-1` (US East - N. Virginia) - Default
- `ap-northeast-1` (Asia Pacific - Tokyo)
- `eu-west-1` (Europe - Ireland)

#### Example: Complete Workflow

```python
from tryon.api import AmazonNovaCanvasVTONAdapter

# Initialize adapter
adapter = AmazonNovaCanvasVTONAdapter(region="us-east-1")

# Generate try-on for upper body garment
images = adapter.generate_and_decode(
    source_image="data/person.jpg",
    reference_image="data/shirt.jpg",
    mask_type="GARMENT",
    garment_class="UPPER_BODY"
)

# Generate try-on for lower body garment
images = adapter.generate_and_decode(
    source_image="data/person.jpg",
    reference_image="data/pants.jpg",
    mask_type="GARMENT",
    garment_class="LOWER_BODY"
)

# Save all results
for idx, image in enumerate(images):
    image.save(f"outputs/result_{idx}.png")
```

**Reference**: [Amazon Nova Canvas Virtual Try-On Documentation](https://aws.amazon.com/blogs/aws/amazon-nova-canvas-update-virtual-try-on-and-style-options-now-available/)

### Virtual Try-On with Kling AI

Generate realistic virtual try-on images using Kling AI's Kolors virtual try-on API. This feature combines a source image (person/model) with a reference image (garment/product) to create realistic try-on results with automatic task polling until completion.

#### Prerequisites

1. **Kling AI Account Setup**: 
   - Sign up for a Kling AI account at [Kling AI Developer Portal](https://app.klingai.com/)
   - Obtain your API key (access key) and secret key from the developer portal
   - Configure credentials in your `.env` file (see Environment Variables section)

2. **Image Requirements**:
   - Maximum image size: 16M pixels (equivalent to 4,096 x 4,096)
   - Maximum dimension: 4,096 pixels per side
   - Supported formats: JPG, PNG
   - Both source and reference images must meet size requirements

#### Command Line Usage

```bash
# Basic usage
python vton.py --provider kling --source person.jpg --reference garment.jpg

# Specify model version
python vton.py --provider kling --source person.jpg --reference garment.jpg --model kolors-virtual-try-on-v1-5

# Use custom base URL
python vton.py --provider kling --source person.jpg --reference garment.jpg --base-url https://api-singapore.klingai.com

# Save output to specific directory
python vton.py --provider kling --source person.jpg --reference garment.jpg --output-dir results/
```

#### Python API Usage

```python
from dotenv import load_dotenv
load_dotenv()

from tryon.api import KlingAIVTONAdapter
from PIL import Image

# Initialize adapter (uses environment variables by default)
adapter = KlingAIVTONAdapter()

# Or specify credentials directly
adapter = KlingAIVTONAdapter(
    api_key="your_api_key",
    secret_key="your_secret_key",
    base_url="https://api-singapore.klingai.com"  # Optional
)

# Generate virtual try-on images
images = adapter.generate_and_decode(
    source_image="data/person.jpg",
    reference_image="data/garment.jpg",
    model="kolors-virtual-try-on-v1-5"  # Optional, uses API default if not specified
)

# Save results
for idx, image in enumerate(images):
    image.save(f"outputs/vton_result_{idx}.png")
```

#### Model Versions

Kling AI supports multiple model versions:
- `kolors-virtual-try-on-v1`: Original model version
- `kolors-virtual-try-on-v1-5`: Enhanced version

If not specified, the API uses the default model version.

#### Asynchronous Processing

Kling AI processes virtual try-on requests asynchronously. The adapter automatically:
1. Submits the request and receives a `task_id`
2. Polls the task status endpoint until completion
3. Returns image URLs when the task succeeds
4. Raises errors if the task fails or times out (default timeout: 5 minutes)

You can customize polling behavior:

```python
# Manual polling
adapter = KlingAIVTONAdapter()

# Submit task
response = adapter.generate(
    source_image="person.jpg",
    reference_image="garment.jpg"
)
# This automatically polls until completion

# Or poll manually with custom settings
task_id = "your_task_id"
image_urls = adapter.poll_task_until_complete(
    task_id=task_id,
    poll_interval=2,  # Check every 2 seconds
    max_wait_time=600  # Maximum 10 minutes
)
```

#### Example: Complete Workflow

```python
from tryon.api import KlingAIVTONAdapter

# Initialize adapter
adapter = KlingAIVTONAdapter()

# Generate try-on
images = adapter.generate_and_decode(
    source_image="data/person.jpg",
    reference_image="data/shirt.jpg",
    model="kolors-virtual-try-on-v1-5"
)

# Save all results
for idx, image in enumerate(images):
    image.save(f"outputs/result_{idx}.png")
```

#### Supported Base URLs

- `https://api-singapore.klingai.com` (Singapore) - Default
- Other regional endpoints may be available (check Kling AI documentation)

**Reference**: [Kling AI API Documentation](https://app.klingai.com/global/dev/document-api/apiReference/model/functionalityTry)

### Virtual Try-On with Segmind

Generate realistic virtual try-on images using Segmind's Try-On Diffusion API. This feature combines a model image (person) with a cloth image (garment/product) to create realistic try-on results.

#### Prerequisites

1. **Segmind Account Setup**: 
   - Sign up for a Segmind account at [Segmind API Portal](https://www.segmind.com/models/try-on-diffusion/api)
   - Obtain your API key from the Segmind dashboard
   - Configure credentials in your `.env` file (see Environment Variables section)

2. **Image Requirements**:
   - Images can be provided as file paths, URLs, or base64-encoded strings
   - Supported formats: JPG, PNG
   - Both model and cloth images must be valid image files

#### Command Line Usage

```bash
# Basic usage
python vton.py --provider segmind --source person.jpg --reference garment.jpg --category "Upper body"

# Specify garment category
python vton.py --provider segmind --source person.jpg --reference garment.jpg --category "Lower body"

# Use custom inference parameters
python vton.py --provider segmind --source person.jpg --reference garment.jpg --category "Dress" --num-steps 35 --guidance-scale 2.5 --seed 42

# Save output to specific directory
python vton.py --provider segmind --source person.jpg --reference garment.jpg --category "Upper body" --output-dir results/
```

#### Python API Usage

```python
from dotenv import load_dotenv
load_dotenv()

from tryon.api import SegmindVTONAdapter
from PIL import Image

# Initialize adapter (uses environment variable by default)
adapter = SegmindVTONAdapter()

# Or specify API key directly
adapter = SegmindVTONAdapter(api_key="your_api_key")

# Generate virtual try-on images
images = adapter.generate_and_decode(
    model_image="data/person.jpg",
    cloth_image="data/garment.jpg",
    category="Upper body",  # Options: "Upper body", "Lower body", "Dress"
    num_inference_steps=35,  # Optional: 20-100, default: 25
    guidance_scale=2.5,  # Optional: 1-25, default: 2
    seed=42  # Optional: -1 to 999999999999999, default: -1
)

# Save results
for idx, image in enumerate(images):
    image.save(f"outputs/vton_result_{idx}.png")
```

#### Garment Categories

Segmind supports three garment categories:
- `"Upper body"`: Tops, shirts, jackets, hoodies (default)
- `"Lower body"`: Pants, skirts, shorts
- `"Dress"`: Dresses, jumpsuits

#### Inference Parameters

- **num_inference_steps**: Number of denoising steps (default: 25, range: 20-100)
  - Higher values may produce better quality but take longer
- **guidance_scale**: Scale for classifier-free guidance (default: 2, range: 1-25)
  - Higher values make the model follow the input more closely
- **seed**: Seed for reproducible results (default: -1 for random, range: -1 to 999999999999999)

#### Example: Complete Workflow

```python
from tryon.api import SegmindVTONAdapter

# Initialize adapter
adapter = SegmindVTONAdapter()

# Generate try-on for upper body garment
images = adapter.generate_and_decode(
    model_image="data/person.jpg",
    cloth_image="data/shirt.jpg",
    category="Upper body"
)

# Generate try-on for lower body garment with custom parameters
images = adapter.generate_and_decode(
    model_image="data/person.jpg",
    cloth_image="data/pants.jpg",
    category="Lower body",
    num_inference_steps=35,
    guidance_scale=2.5,
    seed=42
)

# Save all results
for idx, image in enumerate(images):
    image.save(f"outputs/result_{idx}.png")
```

**Reference**: [Segmind Try-On Diffusion API Documentation](https://www.segmind.com/models/try-on-diffusion/api)

### Image Generation with Nano Banana

Generate high-quality images using Google's Gemini image generation models (Nano Banana and Nano Banana Pro). These models support text-to-image generation, image editing, multi-image composition, and batch generation.

#### Prerequisites

1. **Google Gemini Account Setup**: 
   - Sign up for a Google AI Studio account at [Google AI Studio](https://aistudio.google.com/)
   - Obtain your API key from the [API Keys page](https://aistudio.google.com/app/apikey)
   - Configure credentials in your `.env` file (see Environment Variables section)

2. **Model Selection**:
   - **Nano Banana (Gemini 2.5 Flash Image)**: Fast, efficient, 1024px resolution - ideal for high-volume tasks
   - **Nano Banana Pro (Gemini 3 Pro Image Preview)**: Advanced, up to 4K resolution, search grounding - ideal for professional production

#### Command Line Usage

```bash
# Text-to-image with Nano Banana (Fast)
python image_gen.py --provider nano-banana --prompt "A stylish fashion model wearing a modern casual outfit in a studio setting"

# Text-to-image with Nano Banana Pro (4K)
python image_gen.py --provider nano-banana-pro --prompt "Professional fashion photography of elegant evening wear on a runway" --resolution 4K

# Image editing
python image_gen.py --provider nano-banana --mode edit --image person.jpg --prompt "Change the outfit to a formal business suit"

# Multi-image composition
python image_gen.py --provider nano-banana --mode compose --images outfit1.jpg outfit2.jpg --prompt "Create a fashion catalog layout combining these clothing styles"

# Batch generation
python image_gen.py --provider nano-banana --batch prompts.txt --output-dir results/
```

#### Python API Usage

**Nano Banana (Fast):**

```python
from dotenv import load_dotenv
load_dotenv()

from tryon.api.nano_banana import NanoBananaAdapter

# Initialize adapter
adapter = NanoBananaAdapter()

# Text-to-image generation
images = adapter.generate_text_to_image(
    prompt="A stylish fashion model wearing a modern casual outfit in a studio setting",
    aspect_ratio="16:9"  # Optional: "1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"
)

# Image editing
images = adapter.generate_image_edit(
    image="person.jpg",
    prompt="Change the outfit to a formal business suit"
)

# Multi-image composition
images = adapter.generate_multi_image(
    images=["outfit1.jpg", "outfit2.jpg"],
    prompt="Create a fashion catalog layout combining these clothing styles"
)

# Batch generation
results = adapter.generate_batch([
    "A fashion model showcasing summer collection",
    "Professional photography of formal wear",
    "Casual street style outfit on a model"
])

# Save results
for idx, image in enumerate(images):
    image.save(f"outputs/generated_{idx}.png")
```

**Nano Banana Pro (Advanced):**

```python
from tryon.api.nano_banana import NanoBananaProAdapter

# Initialize adapter
adapter = NanoBananaProAdapter()

# Text-to-image with 4K resolution
images = adapter.generate_text_to_image(
    prompt="Professional fashion photography of elegant evening wear on a runway",
    resolution="4K",  # Options: "1K", "2K", "4K"
    aspect_ratio="16:9",
    use_search_grounding=True  # Optional: Use Google Search for real-world grounding
)

# Image editing with 2K resolution
images = adapter.generate_image_edit(
    image="person.jpg",
    prompt="Change the outfit to a formal business suit",
    resolution="2K"
)

# Save results
images[0].save("result.png")
```

#### Supported Features

- **Text-to-Image**: Generate images from text descriptions
- **Image Editing**: Edit images using text prompts (add, remove, modify elements)
- **Multi-Image Composition**: Combine multiple images with style transfer
- **Batch Generation**: Generate multiple images in batch
- **Aspect Ratios**: 10 supported aspect ratios (1:1, 2:3, 3:2, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9, 21:9)
- **High Resolution**: Up to 4K resolution with Nano Banana Pro
- **Search Grounding**: Real-world grounding using Google Search (Nano Banana Pro only)

#### Aspect Ratios

**Nano Banana (1024px):**
- `"1:1"` (1024x1024)
- `"16:9"` (1344x768)
- `"9:16"` (768x1344)
- And 7 more options

**Nano Banana Pro (1K/2K/4K):**
- Same aspect ratios with resolution-specific dimensions
- `"1K"`: Standard resolution
- `"2K"`: High resolution
- `"4K"`: Ultra-high resolution

**Reference**: [Gemini Image Generation Documentation](https://ai.google.dev/gemini-api/docs/image-generation)

### Image Generation with FLUX.2

Generate high-quality images using FLUX.2 [PRO] and FLUX.2 [FLEX] models from BFL AI. These models support text-to-image generation, image editing, multi-image composition, and advanced controls.

#### Prerequisites

1. **BFL AI Account Setup**: 
   - Sign up for a BFL AI account at [BFL AI](https://docs.bfl.ai/)
   - Obtain your API key from the BFL AI dashboard
   - Configure credentials in your `.env` file (see Environment Variables section)

2. **Model Selection**:
   - **FLUX.2 [PRO]**: High-quality image generation with standard controls - ideal for most use cases
   - **FLUX.2 [FLEX]**: Flexible generation with advanced controls (guidance scale, steps, prompt upsampling) - ideal for fine-tuned control

#### Command Line Usage

```bash
# Text-to-image with FLUX.2 PRO
python image_gen.py --provider flux2-pro --prompt "A professional fashion model wearing elegant evening wear" --width 1024 --height 1024

# Text-to-image with FLUX.2 FLEX (Advanced controls)
python image_gen.py --provider flux2-flex --prompt "A stylish fashion model wearing elegant evening wear" --width 1024 --height 1024 --guidance 7.5 --steps 50

# Image editing
python image_gen.py --provider flux2-pro --mode edit --image person.jpg --prompt "Change the outfit to casual streetwear"

# Multi-image composition
python image_gen.py --provider flux2-pro --mode compose --images outfit1.jpg outfit2.jpg --prompt "Combine these clothing styles into a cohesive outfit"
```

#### Python API Usage

**FLUX.2 [PRO]:**

```python
from dotenv import load_dotenv
load_dotenv()

from tryon.api import Flux2ProAdapter

# Initialize adapter
adapter = Flux2ProAdapter()

# Text-to-image generation
images = adapter.generate_text_to_image(
    prompt="A professional fashion model wearing elegant evening wear on a runway",
    width=1024,
    height=1024,
    seed=42
)

# Image editing
images = adapter.generate_image_edit(
    prompt="Change the outfit to casual streetwear style",
    input_image="model.jpg",
    width=1024,
    height=1024
)

# Multi-image composition
images = adapter.generate_multi_image(
    prompt="Create a fashion catalog layout combining these clothing styles",
    images=["outfit1.jpg", "outfit2.jpg", "accessories.jpg"],
    width=1024,
    height=1024
)

# Save results
images[0].save("result.png")
```

**FLUX.2 [FLEX]:**

```python
from tryon.api import Flux2FlexAdapter

# Initialize adapter
adapter = Flux2FlexAdapter()

# Text-to-image with advanced controls
images = adapter.generate_text_to_image(
    prompt="A stylish fashion model wearing elegant evening wear",
    width=1024,
    height=1024,
    guidance=7.5,  # Higher guidance = more adherence to prompt (1.5-10)
    steps=50,  # More steps = higher quality (default: 28)
    prompt_upsampling=True,  # Enhance prompt quality
    seed=42
)

# Image editing with advanced controls
images = adapter.generate_image_edit(
    prompt="Transform the outfit to match a vintage 1920s fashion style",
    input_image="model.jpg",
    width=1024,
    height=1024,
    guidance=8.0,
    steps=50,
    prompt_upsampling=True
)

# Save results
images[0].save("result.png")
```

#### Supported Features

- **Text-to-Image**: Generate images from text descriptions
- **Image Editing**: Edit images using text prompts (add, remove, modify elements)
- **Multi-Image Composition**: Combine up to 8 images with style transfer
- **Custom Dimensions**: Control width and height (minimum: 64 pixels)
- **Advanced Controls** (FLEX only): Guidance scale (1.5-10), steps (default: 28), prompt upsampling
- **Reproducibility**: Seed support for consistent results
- **Safety Controls**: Moderation tolerance (0-5, default: 2)
- **Output Formats**: JPEG or PNG

#### Key Differences: PRO vs FLEX

- **FLUX.2 [PRO]**: Simpler API, faster generation, good for most use cases
- **FLUX.2 [FLEX]**: Advanced controls (guidance, steps, prompt upsampling), more fine-tuned control over generation quality

**Reference**: [FLUX.2 API Documentation](https://docs.bfl.ai/api-reference/models/generate-or-edit-an-image-with-flux2-[pro])

### Luma AI Image Generation

Generate high-quality images using Luma AI’s (Photon-Flash-1 and Photon-1) models. Supports text-to-image generation, image reference, style reference, character reference and precise image modification for production workflows.

#### Prerequisites

1. **Luma AI Account Setup**: 
   - Sign up for a Luma AI account at the [Luma AI Developer Console](https://lumalabs.ai/)
   - Create and copy your API key from the [API Keys section](https://lumalabs.ai/api)
   - Add the key to your `.env` file (see Environment Variables section)

2. **Model Selection**:
   - **Luma AI (Photon-Flash-1)**: Fast and cost efficient image generation, ideal for rapid iteration and scale
   - **Luma AI (Photon-1)**: High-fidelity default model for professional-grade quality, creativity and detailed prompt handling

#### Command Line Usage

```bash
# Text-to-image with Luma AI ((default) photon-1, photon-flash-1)
python luma_image.py --provider photon-1 --prompt "A stylish fashion model wearing a modern casual outfit in a studio setting"

# Text-to-image with Luma AI (with aspect ratio)
python luma_image.py --provider photon-1 --prompt "A model wearing a red saree" --aspect_ratio "16:9"

# Ouptput to a particular directory
python luma_image.py --provider photon-1 --prompt "A model wearing a red saree" --aspect_ratio "16:9" --output_dir folder_name

# Image generation using Image Reference (single image)
python luma_image.py --provider photon-1 --mode img-ref --prompt "model wearing sunglasses" --images person.jpg --weights 0.8 --aspect_ratio "1:1"

# Image generation using Image Reference (multiple images)
python luma_image.py --provider photon-flash-1 --mode img-ref --prompt "model wearing sunglasses" --images person_1.jpg person_2.jpg --weights 0.8 0.9 --aspect_ratio "9:21"

# Image generation using Style Reference(single image)
python luma_image.py --provider photon-flash-1 --mode style-ref --prompt "model wearing a blue shirt" --images person.jpg --weights 0.75 --aspect_ratio "16:9"

# Image generation using Style Reference(multiple images)
python luma_image.py --provider photon-flash-1 --mode style-ref --prompt "hat" --images person_1.jpg person_2.jpg --weights 0.75 0.9 --aspect_ratio "16:9"

# Image generation using Character Reference
python luma_image.py --provider photon-flash-1 --mode char-ref --char_id identity0 --prompt "Professional fashion photography of elegant evening wear on a runway" --char_images person.jpg --aspect_ratio "16:9"

# Image modification (only single image)
python luma_image.py --provider photon-flash-1 --mode modify --prompt "change the suit color to yellow" --images person.jpg --weights 0.85
```

#### Python API Usage

**Luma AI:**

```python
from dotenv import load_dotenv
load_dotenv()

from tryon.api.lumaAI import LumaAIAdapter

adapter = LumaAIAdapter()

list_of_images = []

images = adapter.generate_text_to_image(
    prompt="person with a hat",
    aspect_ratio= "16:9"
)

list_of_images.extend(images)

images = adapter.generate_with_image_reference(
    prompt="hat",
    aspect_ratio= '16:9',
    image_ref= [
      {
        "url": "person.jpg",
        "weight": 0.85
      }
    ]
)

list_of_images.extend(images)

images = adapter.generate_with_style_reference(
    prompt="tiger",
    aspect_ratio= '16:9',
    style_ref= [
      {
        "url": "person.jpg",
        "weight": 0.8
      }
    ]
)

list_of_images.extend(images)

images = adapter.generate_with_character_reference(
    prompt="man as a pilot",
    aspect_ratio= '16:9',
    character_ref= {
        "identity0": {
          "images": [
            "person.jpg"
          ]
        }
      }
)

list_of_images.extend(images)

images = adapter.generate_with_modify_image(
    prompt="transform all flowers to oranges",
    images= "person.jpg",
    weights= 0.9,
    aspect_ratio= '16:9'
)

list_of_images.extend(images)

for idx, img in enumerate(list_of_images):
    img.save(f"outputs/generated_{idx}.png")
```

#### Supported Features

- **Text-to-Image**: Generate images from text descriptions
- **Image Reference**: Useful when you want to create variations of an image
- **Style Reference**: Apply specific style to the generation
- **Character Reference**: A feature that allows you to create consistent and personalized characters
- **Modify Image**: Make changes to an image
- **Weights**: weight value can be any float value from (0 - 1)
- **Aspect Ratios**: 7 supported aspect ratios (1:1, 3:4, 4:3, 9:16, 16:9, 21:9, 9:21)
- **Multiple Images**: Accepts upto 4 images for image-reference, style-reference and character-reference modes
- **Output Format**: JPEG

#### Aspect Ratios

**LUMA AI:**
- `"1:1"` (1536x1536)
- `"16:9"` (2048x1152)
- `"9:16"` (1152x2048)
- And 4 more options

**Reference**: [Luma AI Image Generation Documentation](https://docs.lumalabs.ai/docs/python-image-generation)

### Image Generation with OpenAI GPT-Image

Generate high-quality images using OpenAI's GPT-Image models (GPT-Image-1 and GPT-Image-1.5).
These models support precise prompt-driven image generation, image editing with masks, multi-image conditioning with consistent visual quality.

**Available Models:**
- **GPT-Image-1**: High-quality image generation with strong prompt understanding
- **GPT-Image-1.5**: Enhanced quality, better consistency, improved prompt understanding (recommended)

#### Prerequisites

1. **OpenAI Account Setup**:
- Sign up for an OpenAI account at [OpenAI Platform](https://platform.openai.com/settings/organization/general)
- Obtain your API key from the [API Keys page](https://platform.openai.com/settings/organization/api-key)
- Configure credentials in your `.env` file (see Environment Variables section)

#### Command Line Usage

```bash
# Text-to-image (uses GPT-Image-1.5 by default)
python gpt_image.py --mode text --prompt "A female model in a traditional green saree" --size 1024x1024 --quality high

# Specify model version explicitly
python gpt_image.py --mode text --prompt "A fashion model in elegant attire" --model gpt-image-1.5 --size 1024x1024 --quality high

# Use GPT-Image-1 (previous version)
python gpt_image.py --mode text --prompt "A fashion model" --model gpt-image-1 --size 1024x1024 --quality high

# With transparent background and output directory
python gpt_image.py --mode text --prompt "A female model in a traditional green saree" --size 1024x1024 --quality high --background transparent --output_dir outputs/

# Image-to-Image
python gpt_image.py --mode image --prompt "change the flowers in the background" --images "person.jpg" --size 1536x1024 --quality medium --n 2

# Image-to-Image with input fidelity (preserve input image details better)
python gpt_image.py --mode image --prompt "change the flowers in the background" --images "person.jpg" --size 1536x1024 --quality medium --inp_fid high

# Image-to-Image with mask Image
python gpt_image.py --mode image --images "scene.png" --mask "mask.png" --prompt "Replace the masked area with a swimming pool"
```

#### Python API Usage

**Using GPT-Image-1.5 (Latest - Recommended):**

```python
from dotenv import load_dotenv
load_dotenv()

import os
from tryon.api.openAI.image_adapter import GPTImageAdapter 

# Default uses GPT-Image-1.5 (latest model)
adapter = GPTImageAdapter()

list_of_images = []

# ---------- Text → Image ----------
images = adapter.generate_text_to_image(
    prompt="A person wearing a leather jacket with sun glasses",
    size="1024x1024",
    quality="high",
    n=1
)

list_of_images.extend(images)

# ---------- Image → Image ----------
images = adapter.generate_image_edit(
    images= "data/image.png",
    prompt="Make the hat red and stylish",
    size="1024x1024",
    quality="high",
    n=1
)

list_of_images.extend(images)

# ---------- Save outputs ----------
os.makedirs("outputs", exist_ok=True)

for idx, img_bytes in enumerate(list_of_images):
    with open(f"outputs/generated_{idx}.png", "wb") as f:
        f.write(img_bytes)

print(f"Saved {len(list_of_images)} images.")
```

**Using GPT-Image-1 (Previous Version):**

```python
from tryon.api.openAI.image_adapter import GPTImageAdapter 

# Explicitly use GPT-Image-1
adapter = GPTImageAdapter(model_version="gpt-image-1")

images = adapter.generate_text_to_image(
    prompt="A fashion model in elegant attire",
    size="1024x1024",
    quality="high"
)

with open("output.png", "wb") as f:
    f.write(images[0])
```

#### Supported Features

- **Text-to-Image**: Generate Images from text descriptions
- **Image Editing**: Edit images using a multiple base images
- **Edit with Mask**: Edit an image using a masked image
- **Size**: Supported sizes (1024x1024, 1536x1024, 1024x1536, auto)
- **Quality**: Supported quality Options (low, high, medium, auto)
- **Background**: Supported background Options (transparent, opaque, auto)
- **Input Fidelity**: Supported Options (low, high)

**References**: 
- [OpenAI Image Generation Documentation](https://platform.openai.com/docs/guides/image-generation)
- [GPT-Image-1.5 Model Card](https://platform.openai.com/docs/models/gpt-image-1.5)


### Video Generation with OpenAI Sora

Generate high-quality videos using OpenAI's Sora models (Sora 2 and Sora 2 Pro). These models support text-to-video and image-to-video generation with flexible durations (4-12 seconds) and multiple resolutions.

**Available Models:**
- **Sora 2**: Fast, high-quality video generation (recommended for most use cases)
- **Sora 2 Pro**: Enhanced quality with superior temporal consistency and prompt understanding

#### Prerequisites

1. **OpenAI Account Setup**:
   - Sign up for an OpenAI account at [OpenAI Platform](https://platform.openai.com/)
   - Obtain your API key from the [API Keys page](https://platform.openai.com/settings/organization/api-keys)
   - Configure credentials in your `.env` file (see Environment Variables section)

#### Command Line Usage

```bash
# Basic text-to-video (uses Sora 2 by default)
python sora_video.py --prompt "A fashion model walking down a runway" --output runway.mp4

# High-quality with Sora 2 Pro
python sora_video.py --prompt "Cinematic fashion runway show" \
                     --model sora-2-pro \
                     --duration 12 \
                     --resolution 1920x1080 \
                     --output runway_hd.mp4

# Image-to-video (animate a static image)
python sora_video.py --image model_photo.jpg \
                     --prompt "The model turns and smiles at the camera" \
                     --duration 4 \
                     --output animated.mp4

# Asynchronous mode (non-blocking)
python sora_video.py --prompt "Fabric flowing in slow motion" \
                     --duration 8 \
                     --async \
                     --output fabric.mp4

# With verbose output
python sora_video.py --prompt "A person trying on different outfits" \
                     --duration 8 \
                     --resolution 1280x720 \
                     --verbose \
                     --output outfit_changes.mp4
```

#### Python API Usage

**Text-to-Video (Synchronous):**

```python
from dotenv import load_dotenv
load_dotenv()

from tryon.api.openAI.video_adapter import SoraVideoAdapter

# Initialize adapter (uses Sora 2 by default)
adapter = SoraVideoAdapter()

# Generate video from text prompt
video_bytes = adapter.generate_text_to_video(
    prompt="A fashion model walking down a runway wearing an elegant evening gown",
    duration=8,  # seconds (4, 8, or 12)
    resolution="1920x1080"  # Full HD
)

# Save the video
with open("runway_walk.mp4", "wb") as f:
    f.write(video_bytes)

print("Video generated successfully!")
```

**Using Sora 2 Pro for Higher Quality:**

```python
# Initialize with Sora 2 Pro
adapter = SoraVideoAdapter(model_version="sora-2-pro")

video_bytes = adapter.generate_text_to_video(
    prompt="Cinematic slow-motion shot of fabric flowing in the wind",
    duration=12,
    resolution="1920x1080"
)

with open("fabric_flow.mp4", "wb") as f:
    f.write(video_bytes)
```

**Image-to-Video (Animate Static Images):**

```python
adapter = SoraVideoAdapter()

# Animate a static image with a text prompt
video_bytes = adapter.generate_image_to_video(
    image="model_portrait.jpg",
    prompt="The model turns around and smiles at the camera",
    duration=4,
    resolution="1280x720"
)

with open("animated_model.mp4", "wb") as f:
    f.write(video_bytes)
```

**Asynchronous Generation with Callbacks:**

```python
adapter = SoraVideoAdapter()

# Define callback functions
def on_complete(video_bytes):
    with open("output.mp4", "wb") as f:
        f.write(video_bytes)
    print("✅ Video generation complete!")

def on_error(error):
    print(f"❌ Error: {error}")

def on_progress(status):
    print(f"Status: {status['status']}, Progress: {status.get('progress', 'N/A')}")

# Start async generation
video_id = adapter.generate_text_to_video_async(
    prompt="A person trying on different outfits in a fashion boutique",
    duration=8,
    resolution="1920x1080",
    on_complete=on_complete,
    on_error=on_error,
    on_progress=on_progress
)

print(f"Video generation started with ID: {video_id}")
# Script continues immediately, callbacks will be invoked when ready
```

**Manual Status Tracking:**

```python
import time

# Start generation without waiting
video_id = adapter.generate_text_to_video(
    prompt="Fashion runway show with multiple models",
    duration=12,
    resolution="1920x1080",
    wait=False  # Return immediately
)

# Check status manually
while True:
    status = adapter.get_video_status(video_id)
    print(f"Status: {status['status']}")
    
    if status['status'] == 'completed':
        video_bytes = adapter.download_video(video_id)
        with open("runway_show.mp4", "wb") as f:
            f.write(video_bytes)
        break
    elif status['status'] == 'failed':
        print(f"Failed: {status.get('error')}")
        break
    
    time.sleep(5)
```

#### Supported Features

- **Text-to-Video**: Generate videos from text descriptions
- **Image-to-Video**: Animate static images with text prompts
- **Durations**: 4, 8, or 12 seconds
- **Resolutions**: 
  - `720x1280` (9:16 vertical)
  - `1280x720` (16:9 horizontal)
  - `1080x1920` (9:16 Full HD vertical)
  - `1920x1080` (16:9 Full HD horizontal)
  - `1024x1792` (tall vertical)
  - `1792x1024` (wide horizontal)
- **Wait Modes**: 
  - Synchronous (blocking, wait for completion)
  - Asynchronous (callbacks, non-blocking)
  - Manual tracking (custom control flow)
- **Output Format**: MP4 (H.264)

#### Model Comparison

| Feature | Sora 2 | Sora 2 Pro |
|---------|--------|------------|
| **Speed** | Fast ⚡ | Slower 🐢 |
| **Quality** | High | Superior |
| **Temporal Consistency** | Good | Excellent |
| **Prompt Understanding** | Good | Superior |
| **Best For** | Rapid iteration, previews | Final production, marketing |

**References**: 
- [OpenAI Video Generation Documentation](https://platform.openai.com/docs/guides/video-generation)
- [Sora Models Overview](https://platform.openai.com/docs/models/sora)


### Video Generation with Luma AI

Generate smooth, high-fidelity videos using Luma AI’s Ray models (Ray 1.6, Ray 2, and Ray Flash 2). These models support text-to-video and image-to-video generation with optional keyframe interpolation. Image-to-video accepts either a single image or two keyframe images (frame0, frame1) for controlled motion.

#### Prerequisites

1. **Luma AI Account Setup**: 
   - Sign up for a Luma AI account at the [Luma AI Developer Console](https://lumalabs.ai/)
   - Create and copy your API key from the [API Keys section](https://lumalabs.ai/api)
   - Add the key to your `.env` file (see Environment Variables section)

2. **Model Selection**:
   - **Ray 1.6 (ray-1-6)**: Balanced quality model for general video generation; slower but stable.
   - **Ray 2 (ray-2)**: High-quality flagship model with the best motion, detail, and consistency.
   - **Ray Flash 2 (ray-flash-2)**: Fast, lower-latency model optimized for quick iterations and previews.

#### Command Line Usage

```bash
# Text to Video with Luma AI
python video_gen.py --provider ray-2 --mode text_video --prompt "A model walking in red saree on a ramp" --resolution 720p --duration 5s --aspect 16:9 --output_dir outputs

# Text to Video with loop
python video_gen.py --provider ray-2 --mode image_video --prompt "A model walking in red saree on a ramp" --resolution 720p --duration 5s --aspect 16:9 --loop

# Image to Video with start keyframe
python video_gen.py --provider ray-flash-2 --mode image_video --prompt "Model walking" --start_image person.jpg --resolution 4k --duration 10s --aspect 21:9 

# Image to Video with End Keyframe
python video_gen.py --provider ray-flash-2 --mode image_video --prompt "Model walking" --end_image person.jpg --resolution 720p --duration 10s --aspect 21:9 

# Image to Video with start and End Keyframe
python video_gen.py --provider ray-2 --mode image_video --prompt "Model sitting on a fence" --start_image person.jpg --end_image person.jpg --resolution 4k --duration 10s --aspect 21:9
```

#### Python API Usage

**Luma AI:**

```python

from dotenv import load_dotenv
load_dotenv()

from tryon.api.lumaAI import LumaAIVideoAdapter
from pathlib import Path

adapter = LumaAIVideoAdapter()

video_list = []


def save_video(video_bytes: bytes, idx: int):
    Path("outputs").mkdir(exist_ok=True)
    out_path = Path("outputs") / f"generated_{idx}.mp4"
    with open(out_path, "wb") as f:
        f.write(video_bytes)
    print(f"[SAVED] {out_path}")


# TEXT → VIDEO
video = adapter.generate_text_to_video(
    prompt="a model riding a car with long hair",
    resolution="540p",
    duration="5s",
    model="ray-2",
)
video_list.append(video)


# IMAGE → VIDEO (start + end)
video = adapter.generate_image_to_video(
    prompt="Man riding a bike",
    start_image="start_img.png",
    end_image="end_img.png",
    resolution="540p",
    duration="5s",
    model="ray-2",
)
video_list.append(video)


# IMAGE → VIDEO (only end image; no start)
video = adapter.generate_image_to_video(
    prompt="A man walking on a ramp",
    end_image="end_img_only.png",
    resolution="540p",
    duration="5s",
    model="ray-2",
)
video_list.append(video)

# SAVE ALL RESULTS
for idx, vid_bytes in enumerate(video_list):
    save_video(vid_bytes, idx)
```

#### Supported Features

- **Text to Video**: Generate videos using test descriptions.
- **Image to Video**: Generate videos using keyframes.
- **Keyframe Generation**: Generate videos using a start keyframe or an end keyframe or both.
- **Duration**: Durations in seconds (5s, 9s, 10s)
- **Resolution**: Quality of the Video (540p, 720p, 1080p, 4k)
- **Aspect Ratios**: 7 supported aspect ratios (1:1, 3:4, 4:3, 9:16, 16:9, 21:9, 9:21)
- **Loop**: Enable seamless looping when generating video from a single image or text prompt. Works for single image when only start_image is provided.

#### Aspect Ratios

**LUMA AI:**
- `"1:1"` (1024x1024)
- `"16:9"` (1280x720)
- `"9:16"` (720x1280)
- And 4 more options

**Reference**: [Luma AI Video Generation Documentation](https://docs.lumalabs.ai/docs/video-generation)

### Preprocessing Functions

#### Segment Garment

Segments garments from images using U2Net model.

```python
from tryon.preprocessing import segment_garment

segment_garment(
    inputs_dir="path/to/input/images",
    outputs_dir="path/to/output/segments",
    cls="upper"  # "upper", "lower", or "all"
)
```

#### Extract Garment

Extracts and preprocesses garments from images.

```python
from tryon.preprocessing import extract_garment

extract_garment(
    inputs_dir="path/to/input/images",
    outputs_dir="path/to/output/garments",
    cls="upper",
    resize_to_width=400
)
```

#### Segment Human

Segments human subjects from images.

```python
from tryon.preprocessing import segment_human

segment_human(
    image_path="path/to/human/image.jpg",
    output_dir="path/to/output/directory"
)
```

## 🎨 Demos

The project includes several interactive demos for easy experimentation:

### Virtual Try-On Demo (Web App) ⭐ NEW

A modern, full-stack virtual try-on web application with FastAPI backend and Next.js frontend.

**Features**:
- Support for 4 AI models: Nano Banana, Nano Banana Pro, FLUX 2 Pro, FLUX 2 Flex
- Multi-image upload with drag & drop
- Real-time credit estimation
- Modern, responsive UI
- Production-ready API server

**Quick Start**:

1. Start the backend:
```bash
python api_server.py
```

2. In a new terminal, start the frontend:
```bash
cd demo/virtual-tryon
npm install
npm run dev
```

3. Open `http://localhost:3000` in your browser

**Documentation**: See [`demo/virtual-tryon/README.md`](demo/virtual-tryon/README.md) and [`README_API_SERVER.md`](README_API_SERVER.md) for detailed instructions.

### Extract Garment Demo

```bash
python run_demo.py --name extract_garment
```

### Model Swap Demo

```bash
python run_demo.py --name model_swap
```

### Outfit Generator Demo

```bash
python run_demo.py --name outfit_generator
```

### Fashion Prompt Builder Demo

A modern Next.js web application for generating prompts for fashion model generation.

```bash
cd demo/fashion-prompt-builder
npm install
npm run dev
```

Open `http://localhost:3000` to access the prompt builder interface.

**Features**:
- Template-based prompt generation
- Prompt gallery with examples
- Raw prompt editor with tips
- Real-time preview and validation
- Support for multiple AI models

Gradio demos launch a web interface where you can interact with the models through a user-friendly UI.

## 📁 Project Structure

```
opentryon/
├── tryon/                    # Main try-on preprocessing module
│   ├── api/                 # API adapters
│   │   ├── nova_canvas.py  # Amazon Nova Canvas VTON adapter
│   │   ├── kling_ai.py     # Kling AI VTON adapter
│   │   ├── lumaAI/         # Luma AI Image generation adapter
│   │   │    └── adapter.py  # LumaAIAdapter
│   │   ├── segmind.py      # Segmind Try-On Diffusion adapter
│   │   ├── nano_banana/    # Nano Banana (Gemini) image generation adapters
│   │   │   └── adapter.py  # NanoBananaAdapter and NanoBananaProAdapter
│   │   └── flux2.py        # FLUX.2 [PRO] and [FLEX] image generation adapters
│   ├── datasets/            # Dataset loaders
│   │   ├── base.py         # Base dataset interface
│   │   ├── fashion_mnist.py # Fashion-MNIST dataset
│   │   ├── viton_hd.py     # VITON-HD dataset
│   │   ├── example_usage.py # Usage examples
│   │   └── README.md       # Datasets documentation
│   ├── preprocessing/        # Preprocessing utilities
│   │   ├── captioning/       # Image captioning
│   │   ├── sam2/            # SAM2 segmentation
│   │   ├── u2net/           # U2Net segmentation models
│   │   └── utils.py         # Utility functions
│   └── models/              # Model implementations
│       └── ootdiffusion/    # OOTDiffusion model
├── tryondiffusion/          # TryOnDiffusion implementation
│   ├── diffusion.py         # Diffusion model
│   ├── network.py           # Network architecture
│   ├── trainer.py           # Training utilities
│   ├── pre_processing/      # Preprocessing for training
│   └── utils/               # Utility functions
├── demo/                    # Interactive demos
│   ├── virtual-tryon/       # Virtual try-on demo (Nextjs+Tailwindcss)
│   ├── extract_garment/     # Garment extraction demo (Gradio)
│   ├── model_swap/          # Model swap demo (Gradio)
│   ├── outfit_generator/    # Outfit generator demo (Gradio)
│   └── fashion-prompt-builder/  # Fashion prompt builder (Next.js)
├── scripts/                 # Installation scripts
├── api_server.py            # FastAPI server for virtual try-on demo
├── main.py                  # Main CLI entry point
├── run_demo.py              # Demo launcher (Gradio demos)
├── vton.py                  # Virtual try-on CLI (Amazon Nova Canvas, Kling AI, Segmind)
├── image_gen.py             # Image generation CLI (Nano Banana, FLUX.2)
├── requirements.txt         # Python dependencies
├── environment.yml          # Conda environment
├── README_API_SERVER.md     # API server documentation
└── setup.py                 # Package installation
```

## 🗺️ TryOnDiffusion: Roadmap

Based on the [TryOnDiffusion paper](https://arxiv.org/abs/2306.08276):

1. ~~Prepare initial implementation~~
2. Test initial implementation with small dataset (VITON-HD)
3. Gather sufficient data and compute resources
4. Prepare and train final implementation
5. Publicly release parameters

## 🤝 Contributing

We welcome contributions! Please follow these steps:

### 1. Open an Issue

We recommend opening an issue (if one doesn't already exist) and discussing your intended changes before making any modifications. This helps us provide feedback and confirm the planned changes.

### 2. Fork and Set Up

1. Fork the repository
2. Set up the environment using the installation instructions above
3. Install dependencies
4. Make your changes

### 3. Create Pull Request

Create a pull request to the main branch from your fork's branch. Please ensure:
- Your code follows the project's style guidelines
- You've tested your changes
- Documentation is updated if needed

### 4. Review Process

Once the pull request is created, we will review the code changes and merge the pull request as soon as possible.

### Writing Documentation

If you're interested in improving documentation, you can:
- Add content to `README.md`
- Create new documentation files as needed
- Submit a pull request with your documentation improvements

For detailed contribution guidelines, see [CONTRIBUTING.md](CONTRIBUTING.md).

## 📝 Requirements

Key dependencies include:
- PyTorch (== 2.1.2)
- torchvision (== 0.16.2)
- diffusers (== 0.29.2)
- transformers (== 4.42.4)
- opencv-python (== 4.8.1.78)
- scikit-image (== 0.22.0)
- numpy (== 1.26.4)
- einops (== 0.7.0)
- requests (>= 2.31.0)
- PyJWT (>= 2.10.1)
- boto3 (== 1.40.64)
- python-dotenv (== 1.0.1)
- google-genai (>= 1.52.0)
- fastapi (== 0.124.0)
- uvicorn[standard] (== 0.38.0)
- python-multipart (== 0.0.20)
- lumaai (== 1.18.1)

See `requirements.txt` or `environment.yml` for the complete list of dependencies.

## 📚 Additional Resources

- **TryOnDiffusion Paper**: [arXiv:2306.08276](https://arxiv.org/abs/2306.08276)
- **Amazon Nova Canvas**: [AWS Blog Post](https://aws.amazon.com/blogs/aws/amazon-nova-canvas-update-virtual-try-on-and-style-options-now-available/)
- **Kling AI**: [Kling AI API Documentation](https://app.klingai.com/global/dev/document-api/apiReference/model/functionalityTry)
- **Segmind**: [Segmind Try-On Diffusion API](https://www.segmind.com/models/try-on-diffusion/api)
- **Nano Banana**: [Gemini Image Generation Documentation](https://ai.google.dev/gemini-api/docs/image-generation)
- **FLUX.2**: [BFL AI Documentation](https://docs.bfl.ai/)
- **Luma AI**: [Luma AI Image Generation Documentation](https://docs.lumalabs.ai/docs/python-image-generation)
- **Discord Community**: [Join our Discord](https://discord.gg/T5mPpZHxkY)
- **Outfit Generator Model**: [FLUX.1-dev LoRA Outfit Generator](https://huggingface.co/tryonlabs/FLUX.1-dev-LoRA-Outfit-Generator)

## 📄 License

All material is made available under [Creative Commons BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/). 

You can **use** the material for **non-commercial purposes**, as long as you:
- Give appropriate credit by **citing our original [GitHub repository](https://github.com/tryonlabs/opentryon)**
- **Indicate any changes** that you've made to the code

---

Made with ❤️ by [TryOn Labs](https://www.tryonlabs.ai)
