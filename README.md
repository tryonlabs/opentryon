# OpenTryOn: Open-source AI toolkit for fashion tech and virtual try-on

[![Discord](https://img.shields.io/badge/Discord-Join%20Chat-blue?style=flat-square&logo=discord)](https://discord.gg/T5mPpZHxkY)
[![License](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg?style=flat-square)](https://creativecommons.org/licenses/by-nc/4.0/)

OpenTryOn is an open-source AI toolkit designed for fashion technology and virtual try-on applications. This project provides a comprehensive suite of tools for garment segmentation, human parsing, pose estimation, and virtual try-on using state-of-the-art diffusion models.

## 🎯 Features

- **Virtual Try-On**: 
  - Amazon Nova Canvas virtual try-on using AWS Bedrock
  - Kling AI virtual try-on using Kolors API
  - Advanced diffusion-based virtual try-on capabilities using TryOnDiffusion
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

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
  - [Datasets Module](#datasets-module)
  - [Virtual Try-On with Amazon Nova Canvas](#virtual-try-on-with-amazon-nova-canvas)
  - [Virtual Try-On with Kling AI](#virtual-try-on-with-kling-ai)
  - [Preprocessing Functions](#preprocessing-functions)
- [Demos](#demos)
- [Project Structure](#project-structure)
- [TryOnDiffusion Roadmap](#tryondiffusion-roadmap)
- [Contributing](#contributing)
- [License](#license)

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
```

**Notes**: 
- Download the U2Net checkpoint file from the [huggingface-cloth-segmentation repository](https://github.com/wildoctopus/huggingface-cloth-segmentation)
- For Amazon Nova Canvas, ensure you have AWS credentials configured (via `.env` file or AWS CLI) and Nova Canvas enabled in your AWS Bedrock console
- For Kling AI, obtain your API key and secret key from the [Kling AI Developer Portal](https://app.klingai.com/global/dev/document-api/apiReference/model/functionalityTry)

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

The project includes several interactive Gradio demos for easy experimentation:

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

Each demo launches a web interface where you can interact with the models through a user-friendly UI.

## 📁 Project Structure

```
opentryon/
├── tryon/                    # Main try-on preprocessing module
│   ├── api/                 # API adapters
│   │   ├── nova_canvas.py  # Amazon Nova Canvas VTON adapter
│   │   └── kling_ai.py     # Kling AI VTON adapter
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
│   ├── extract_garment/     # Garment extraction demo
│   ├── model_swap/          # Model swap demo
│   └── outfit_generator/    # Outfit generator demo
├── scripts/                 # Installation scripts
├── main.py                  # Main CLI entry point
├── vton.py                  # Virtual try-on CLI (Amazon Nova Canvas & Kling AI)
├── run_demo.py              # Demo launcher
├── requirements.txt         # Python dependencies
└── environment.yml          # Conda environment
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
- gradio (== 4.44.1)
- opencv-python (== 4.8.1.78)
- scikit-image (== 0.22.0)
- numpy (== 1.26.4)
- einops (== 0.7.0)
- requests (>= 2.31.0)
- PyJWT (>= 2.10.1)
- boto3 (== 1.40.64)
- python-dotenv (== 1.0.1)

See `requirements.txt` or `environment.yml` for the complete list of dependencies.

## 📚 Additional Resources

- **TryOnDiffusion Paper**: [arXiv:2306.08276](https://arxiv.org/abs/2306.08276)
- **Amazon Nova Canvas**: [AWS Blog Post](https://aws.amazon.com/blogs/aws/amazon-nova-canvas-update-virtual-try-on-and-style-options-now-available/)
- **Kling AI**: [Kling AI API Documentation](https://app.klingai.com/global/dev/document-api/apiReference/model/functionalityTry)
- **Discord Community**: [Join our Discord](https://discord.gg/T5mPpZHxkY)
- **Outfit Generator Model**: [FLUX.1-dev LoRA Outfit Generator](https://huggingface.co/tryonlabs/FLUX.1-dev-LoRA-Outfit-Generator)

## 📄 License

All material is made available under [Creative Commons BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/). 

You can **use** the material for **non-commercial purposes**, as long as you:
- Give appropriate credit by **citing our original [GitHub repository](https://github.com/tryonlabs/opentryon)**
- **Indicate any changes** that you've made to the code

---

Made with ❤️ by [TryOn Labs](https://www.tryonlabs.ai)
