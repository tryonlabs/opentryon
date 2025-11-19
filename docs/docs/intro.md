---
slug: /
title: OpenTryOn
description: OpenTryOn is an open-source AI toolkit for fashion technology and virtual try-on applications. Features virtual try-on APIs (Amazon Nova Canvas, Kling AI, Segmind), datasets (Fashion-MNIST, VITON-HD), garment segmentation, pose estimation, and TryOnDiffusion implementation.
keywords:
  - virtual try-on
  - fashion AI
  - AI toolkit
  - virtual try-on API
  - fashion technology
  - garment segmentation
  - TryOnDiffusion
  - open source AI
  - fashion tech
  - virtual fitting
  - AI fashion
  - computer vision
  - diffusion models
  - fashion datasets
  - VITON-HD
  - Fashion-MNIST
  - Amazon Nova Canvas
  - Kling AI
  - Segmind
image: /img/opentryon-social-card.jpg
---

# Welcome to OpenTryOn

OpenTryOn is an open-source AI toolkit designed for fashion technology and virtual try-on applications. This project provides a comprehensive suite of tools for garment segmentation, human parsing, pose estimation, and virtual try-on using state-of-the-art diffusion models.

## 🎯 What is OpenTryOn?

OpenTryOn is a powerful Python library that democratizes fashion technology by providing:

- **Preprocessing Utilities**: Garment segmentation, human parsing, and pose estimation
- **TryOnDiffusion Implementation**: Dual UNet architecture for virtual try-on
- **Easy-to-Use APIs**: Simple interfaces that abstract away complexity
- **Production-Ready Code**: Comprehensive documentation and examples
- **Open Source**: Free for non-commercial use

## 🚀 Key Features

### Virtual Try-On
Advanced diffusion-based virtual try-on capabilities using TryOnDiffusion with dual UNet architecture. Also includes API adapters for cloud-based virtual try-on services like Segmind.

### Datasets Module
Easy-to-use interfaces for fashion and virtual try-on datasets:
- **Fashion-MNIST**: 60,000 training examples with 10 fashion categories
- **VITON-HD**: High-resolution virtual try-on dataset with 11,647 training pairs
- **Lazy Loading**: Efficient PyTorch DataLoader support for large datasets
- **Automatic Download**: Built-in download functionality

### API Adapters
Cloud-based virtual try-on APIs:
- **Segmind**: Try-On Diffusion API for realistic virtual try-on generation
- **Kling AI**: Virtual try-on with asynchronous processing
- **Amazon Nova Canvas**: AWS-based virtual try-on service

### Garment Preprocessing
- **Garment Segmentation**: U2Net-based segmentation for upper, lower, and dress categories
- **Garment Extraction**: Extract and preprocess garments for virtual try-on
- **Human Segmentation**: Isolate human subjects from images

### Pose Estimation
OpenPose-based pose keypoint extraction for both garments and humans, enabling accurate virtual try-on.

### Outfit Generation
FLUX.1-dev LoRA-based outfit generation from text descriptions.

### Interactive Demos
Gradio-based web interfaces for easy experimentation and testing.

## 📚 What You'll Learn

In this documentation, you'll find:

- **[Installation Guide](getting-started/installation)**: Get OpenTryOn up and running
- **[Quick Start](getting-started/quickstart)**: Start using OpenTryOn in minutes
- **[Datasets Module](datasets/overview)**: Load and use Fashion-MNIST and VITON-HD datasets
- **[API Reference](api-reference/overview)**: Complete API documentation including Segmind and other adapters
- **[Examples](examples/basic-usage)**: Real-world usage examples for datasets and virtual try-on
- **[Advanced Guides](advanced/training-guide)**: Deep dive into training and customization

## 🎓 Prerequisites

Before you begin, you should have:

- Python 3.10 or higher
- Basic knowledge of Python programming
- Familiarity with computer vision concepts (helpful but not required)
- CUDA-capable GPU (recommended for best performance)

## 💡 Quick Examples

Here are some simple examples to get you started:

### Virtual Try-On with Segmind

```python
from dotenv import load_dotenv
load_dotenv()

from tryon.api import SegmindVTONAdapter

# Initialize adapter
adapter = SegmindVTONAdapter()

# Generate virtual try-on
images = adapter.generate_and_decode(
    model_image="person.jpg",
    cloth_image="shirt.jpg",
    category="Upper body"
)

# Save result
images[0].save("result.png")
```

### Using Fashion-MNIST Dataset

```python
from tryon.datasets import FashionMNIST

# Create dataset instance (downloads automatically)
dataset = FashionMNIST(download=True)

# Load the dataset
(train_images, train_labels), (test_images, test_labels) = dataset.load(
    normalize=True,
    flatten=False
)

print(f"Training set: {train_images.shape}")  # (60000, 28, 28)
print(f"Class 0: {dataset.get_class_name(0)}")  # 'T-shirt/top'
```

### Garment Preprocessing

```python
from dotenv import load_dotenv
load_dotenv()

from tryon.preprocessing import segment_garment, extract_garment

# Segment garment
segment_garment(
    inputs_dir="data/original_cloth",
    outputs_dir="data/garment_segmented",
    cls="upper"
)

# Extract garment
extract_garment(
    inputs_dir="data/original_cloth",
    outputs_dir="data/cloth",
    cls="upper",
    resize_to_width=400
)
```

## 🤝 Get Involved

OpenTryOn is an open-source project, and we welcome contributions!

- **GitHub**: [github.com/tryonlabs/opentryon](https://github.com/tryonlabs/opentryon)
- **Discord**: [Join our community](https://discord.gg/T5mPpZHxkY)
- **Contributing**: See our [Contributing Guide](community/contributing)

## 📄 License

All material is made available under [Creative Commons BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/). You can use the material for non-commercial purposes, as long as you give appropriate credit and indicate any changes.

## 🗺️ Roadmap

Check out our [Roadmap](community/roadmap) to see what's coming next!

## 🆘 Need Help?

- Check our [Troubleshooting Guide](advanced/troubleshooting)
- Join our [Discord community](https://discord.gg/T5mPpZHxkY)
- Open an issue on [GitHub](https://github.com/tryonlabs/opentryon/issues)

---

Ready to get started? Head over to the [Installation Guide](getting-started/installation)!

