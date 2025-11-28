# Datasets Module

The `tryon.datasets` module provides easy-to-use interfaces for downloading and loading datasets commonly used in fashion and virtual try-on applications.

## Overview

The datasets module uses a **class-based adapter pattern** where each dataset is implemented as a class that extends the base `Dataset` interface. This design ensures consistency across different datasets while allowing for dataset-specific features.

### Key Features

- **Consistent API**: All datasets follow the same interface pattern
- **Automatic Download**: Built-in download functionality for supported datasets
- **Memory Efficient**: Support for lazy loading with PyTorch DataLoader
- **Easy to Extend**: Simple interface for adding new datasets
- **State Management**: Automatic caching and metadata tracking

## Supported Datasets

### Fashion-MNIST

A dataset of Zalando's article images designed as a drop-in replacement for the original MNIST dataset. Ideal for quick prototyping, learning, and benchmarking.

- **60,000 training examples**
- **10,000 test examples**
- **10 classes**: T-shirt/top, Trouser, Pullover, Dress, Coat, Sandal, Shirt, Sneaker, Bag, Ankle boot
- **28×28 grayscale images**
- **~60MB total size**

[Learn more about Fashion-MNIST →](fashion-mnist)

### VITON-HD

A high-resolution virtual try-on dataset consisting of person images and clothing images. Perfect for training and evaluating virtual try-on models.

- **11,647 training pairs**
- **2,032 test pairs**
- **1024×768 resolution images**
- **Person and clothing image pairs**

[Learn more about VITON-HD →](viton-hd)

### Subjects200K

A large-scale dataset containing 200,000 paired images for subject consistency research. Each image pair maintains subject consistency while presenting variations in scene context. Loaded from HuggingFace.

- **~200,000 paired images**
- **Three collections**: Collection 1 (512×512), Collection 2 (512×512), Collection 3 (1024×1024)
- **Quality assessment scores** for filtering
- **HuggingFace integration** (automatic download)

[Learn more about Subjects200K →](subjects200k)

## Quick Start

### Fashion-MNIST

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
print(f"Test set: {test_images.shape}")      # (10000, 28, 28)
print(f"Class 0: {dataset.get_class_name(0)}")  # 'T-shirt/top'
```

### VITON-HD

```python
from tryon.datasets import VITONHD
from torchvision import transforms

# Create dataset instance
dataset = VITONHD(data_dir="./datasets/viton_hd", download=False)

# Define transforms
transform = transforms.Compose([
    transforms.Resize((512, 384)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
])

# Get DataLoader for efficient lazy loading
train_loader = dataset.get_dataloader(
    split='train',
    batch_size=8,
    shuffle=True,
    transform=transform
)

# Use in training loop
for batch in train_loader:
    person_imgs = batch['person']  # [batch_size, 3, H, W]
    clothing_imgs = batch['clothing']  # [batch_size, 3, H, W]
    # Train model...
```

### Subjects200K

```python
from tryon.datasets import Subjects200K
from torchvision import transforms

# Create dataset instance (loads from HuggingFace)
dataset = Subjects200K()

# Get HuggingFace dataset
hf_dataset = dataset.get_hf_dataset()
sample = hf_dataset['train'][0]
image = sample['image']  # PIL Image (composite with paired images)
collection = sample['collection']  # 'collection_1', 'collection_2', or 'collection_3'

# Get PyTorch DataLoader with quality filtering
transform = transforms.Compose([
    transforms.Resize((512, 512)),
    transforms.ToTensor(),
])

dataloader = dataset.get_dataloader(
    batch_size=16,
    transform=transform,
    collection='collection_2',
    filter_high_quality=True
)

# Use in training loop
for batch in dataloader:
    images = batch['image']  # [batch_size, 3, H, W]
    collections = batch['collection']
    quality_assessments = batch['quality_assessment']
    # Train model...
```

## Architecture

All dataset classes extend the `Dataset` base class, which provides:

- **Automatic download management**: Handles dataset downloads and verification
- **State tracking**: Tracks normalization, flattening, and other transformations
- **Metadata management**: Stores dataset information and statistics
- **Consistent interface**: Common methods like `load()`, `get_info()`, `get_class_names()`

### Base Class Interface

```python
from tryon.datasets import Dataset
from pathlib import Path

class MyDataset(Dataset):
    def _get_default_data_dir(self) -> Path:
        """Return default data directory."""
        return Path.home() / '.opentryon' / 'datasets' / 'my_dataset'
    
    def _ensure_downloaded(self) -> None:
        """Download dataset files if needed."""
        # Implement download logic
        pass
    
    def load(self, **kwargs):
        """Load and return dataset."""
        # Implement loading logic
        return (train_data, train_labels), (test_data, test_labels)
    
    def get_class_names(self) -> list:
        """Return list of class names."""
        return ['class1', 'class2', ...]
```

## Dataset Storage

By default, datasets are stored in:
- **Linux/Mac**: `~/.opentryon/datasets/`
- **Windows**: `C:\Users\<username>\.opentryon\datasets\`

You can override this by specifying a custom `data_dir` when creating a dataset instance.

## Requirements

### Fashion-MNIST
- **No additional requirements**: Uses standard Python libraries

### VITON-HD
- **PyTorch**: Required for DataLoader support
- **torchvision**: Required for transforms
- **Pillow**: Required for image loading

Install with:
```bash
pip install torch torchvision pillow
```

### Subjects200K
- **datasets**: HuggingFace datasets library (required)
- **PyTorch**: Required for DataLoader support
- **torchvision**: Required for transforms
- **Pillow**: Required for image loading

Install with:
```bash
pip install datasets torch torchvision pillow
```

## Next Steps

- [Fashion-MNIST Documentation](fashion-mnist) - Detailed guide for Fashion-MNIST dataset
- [VITON-HD Documentation](viton-hd) - Detailed guide for VITON-HD dataset
- [Subjects200K Documentation](subjects200k) - Detailed guide for Subjects200K dataset
- [API Reference](../api-reference/overview) - Complete API documentation
- [Examples](../examples/datasets) - Usage examples

