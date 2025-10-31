# OpenTryOn: Open-source AI toolkit for fashion tech and virtual try-on

[![Discord](https://img.shields.io/badge/Discord-Join%20Chat-blue?style=flat-square&logo=discord)](https://discord.gg/T5mPpZHxkY)
[![License](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg?style=flat-square)](https://creativecommons.org/licenses/by-nc/4.0/)

OpenTryOn is an open-source AI toolkit designed for fashion technology and virtual try-on applications. This project provides a comprehensive suite of tools for garment segmentation, human parsing, pose estimation, and virtual try-on using state-of-the-art diffusion models.

## 🎯 Features

- **Virtual Try-On**: Advanced diffusion-based virtual try-on capabilities using TryOnDiffusion
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
```

**Note**: Download the U2Net checkpoint file from the [huggingface-cloth-segmentation repository](https://github.com/wildoctopus/huggingface-cloth-segmentation).

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

See `requirements.txt` or `environment.yml` for the complete list of dependencies.

## 📚 Additional Resources

- **TryOnDiffusion Paper**: [arXiv:2306.08276](https://arxiv.org/abs/2306.08276)
- **Discord Community**: [Join our Discord](https://discord.gg/T5mPpZHxkY)
- **Outfit Generator Model**: [FLUX.1-dev LoRA Outfit Generator](https://huggingface.co/tryonlabs/FLUX.1-dev-LoRA-Outfit-Generator)

## 📄 License

All material is made available under [Creative Commons BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/). 

You can **use** the material for **non-commercial purposes**, as long as you:
- Give appropriate credit by **citing our original [GitHub repository](https://github.com/tryonlabs/opentryon)**
- **Indicate any changes** that you've made to the code

---

Made with ❤️ by [TryOn Labs](https://www.tryonlabs.ai)
