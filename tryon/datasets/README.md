# Datasets Module

The `tryon.datasets` module provides easy-to-use interfaces for downloading and loading datasets commonly used in fashion and virtual try-on applications.

## Table of Contents

- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Fashion-MNIST](#fashion-mnist)
  - [Overview](#overview)
  - [API Reference](#api-reference)
  - [Usage Examples](#usage-examples)
  - [Best Practices](#best-practices)
- [VITON-HD](#viton-hd)
  - [Overview](#overview-1)
  - [API Reference](#api-reference-1)
  - [Usage Examples](#usage-examples-1)
  - [Best Practices](#best-practices-1)
  - [Performance Considerations](#performance-considerations)
- [Subjects200K](#subjects200k)
  - [Overview](#overview-2)
  - [API Reference](#api-reference-2)
  - [Usage Examples](#usage-examples-2)
  - [Best Practices](#best-practices-2)
  - [Performance Considerations](#performance-considerations-1)
- [Adding New Datasets](#adding-new-datasets)
- [Dataset Storage](#dataset-storage)
- [Requirements](#requirements)
- [Troubleshooting](#troubleshooting)

## Architecture

The module uses a **class-based adapter pattern** where each dataset is implemented as a class that extends the base `Dataset` interface. This design:

- ✅ **Ensures consistency** across different datasets
- ✅ **Makes it easy to add new datasets** by implementing the base interface
- ✅ **Allows for dataset-specific features** while maintaining a common API
- ✅ **Provides state management** (caching, metadata tracking)
- ✅ **Maintains backward compatibility** with convenience functions

### Base Class Interface

All dataset classes extend the `Dataset` base class:

```python
from tryon.datasets import Dataset
from pathlib import Path
import numpy as np

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

## Quick Start

### Fashion-MNIST (Small Dataset)

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

### VITON-HD (Large Dataset)

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

---

## Fashion-MNIST

### Overview

Fashion-MNIST is a dataset of Zalando's article images designed as a drop-in replacement for the original MNIST dataset. It's ideal for:

- **Quick prototyping** and experimentation
- **Learning** machine learning basics
- **Benchmarking** classification algorithms
- **Testing** preprocessing pipelines

**Dataset Statistics:**
- **60,000 training examples**
- **10,000 test examples**
- **10 classes**: T-shirt/top, Trouser, Pullover, Dress, Coat, Sandal, Shirt, Sneaker, Bag, Ankle boot
- **28×28 grayscale images**
- **~60MB total size** (downloads quickly)

**Class Labels:**
- `0`: T-shirt/top
- `1`: Trouser
- `2`: Pullover
- `3`: Dress
- `4`: Coat
- `5`: Sandal
- `6`: Shirt
- `7`: Sneaker
- `8`: Bag
- `9`: Ankle boot

**Reference:** [Fashion-MNIST GitHub](https://github.com/zalandoresearch/fashion-mnist)

### API Reference

#### Class: `FashionMNIST`

Fashion-MNIST dataset adapter class.

##### Constructor

```python
FashionMNIST(data_dir: Optional[str] = None, download: bool = True)
```

**Parameters:**
- `data_dir` (str, optional): Directory to store the dataset. Defaults to `~/.opentryon/datasets/fashion_mnist`
- `download` (bool): If `True`, download the dataset if it doesn't exist. Default: `True`

**Example:**
```python
# Use default directory
dataset = FashionMNIST(download=True)

# Use custom directory
dataset = FashionMNIST(
    data_dir="./my_datasets/fashion_mnist",
    download=True
)
```

##### Methods

###### `load(normalize=False, flatten=False)`

Load Fashion-MNIST dataset into memory.

**Parameters:**
- `normalize` (bool): If `True`, normalize pixel values to [0, 1] range. Default: `False`
  - When `False`: pixel values are integers 0-255
  - When `True`: pixel values are floats 0.0-1.0
- `flatten` (bool): If `True`, flatten images to 1D arrays. Default: `False`
  - When `False`: images are shape `(28, 28)`
  - When `True`: images are shape `(784,)`

**Returns:**
- `(train_data, test_data)` tuple where each is `(images, labels)`
  - `train_images`: numpy array of shape `(60000, 28, 28)` or `(60000, 784)` if `flatten=True`
  - `train_labels`: numpy array of shape `(60000,)` with integer values 0-9
  - `test_images`: numpy array of shape `(10000, 28, 28)` or `(10000, 784)` if `flatten=True`
  - `test_labels`: numpy array of shape `(10000,)` with integer values 0-9

**Data Types:**
- Images: `uint8` if `normalize=False`, `float32` if `normalize=True`
- Labels: `uint8`

**Example:**
```python
# Load with normalization
(train_images, train_labels), (test_images, test_labels) = dataset.load(
    normalize=True,
    flatten=False
)

# Load flattened for ML algorithms that expect 1D features
(train_images, train_labels), (test_images, test_labels) = dataset.load(
    normalize=True,
    flatten=True
)
```

###### `get_class_names() -> List[str]`

Get all class names.

**Returns:**
- `list`: List of all 10 class name strings in order (0-9)

**Example:**
```python
class_names = dataset.get_class_names()
print(class_names[0])  # 'T-shirt/top'
```

###### `get_class_name(label: int) -> str`

Get the class name for a given label.

**Parameters:**
- `label` (int): Integer label (0-9)

**Returns:**
- `str`: Class name string

**Raises:**
- `ValueError`: If label is out of range (0-9)

**Example:**
```python
print(dataset.get_class_name(0))  # 'T-shirt/top'
print(dataset.get_class_name(9))  # 'Ankle boot'
```

###### `get_info() -> Dict[str, Any]`

Get comprehensive dataset information including metadata.

**Returns:**
- `dict`: Dictionary containing:
  - `name`: Dataset class name (`'FashionMNIST'`)
  - `data_dir`: Path to dataset directory
  - `loaded`: Whether data has been loaded into memory
  - `num_classes`: Number of classes (10)
  - `image_shape`: Image shape tuple `(28, 28)`
  - `train_size`: Number of training samples (60000)
  - `test_size`: Number of test samples (10000)
  - `normalized`: Whether data is normalized (if loaded)
  - `flattened`: Whether data is flattened (if loaded)
  - `train_images_shape`: Shape of training images (if loaded)
  - `test_images_shape`: Shape of test images (if loaded)

**Example:**
```python
info = dataset.get_info()
print(f"Dataset: {info['name']}")
print(f"Classes: {info['num_classes']}")
print(f"Train size: {info['train_size']}")

# After loading
dataset.load(normalize=True)
info = dataset.get_info()
print(f"Normalized: {info['normalized']}")
print(f"Train shape: {info['train_images_shape']}")
```

### Convenience Functions

For backward compatibility and simplicity, the module provides convenience functions:

#### `load_fashion_mnist(data_dir=None, download=True, normalize=False, flatten=False)`

Load Fashion-MNIST dataset using a simple function interface.

**Parameters:**
- `data_dir` (str, optional): Directory to store the dataset
- `download` (bool): If `True`, download the dataset if needed
- `normalize` (bool): If `True`, normalize pixel values to [0, 1] range
- `flatten` (bool): If `True`, flatten images to 1D arrays

**Returns:**
- Same as `FashionMNIST.load()`

**Example:**
```python
from tryon.datasets import load_fashion_mnist

(train_images, train_labels), (test_images, test_labels) = load_fashion_mnist(
    normalize=True
)
```

#### `get_fashion_mnist_class_name(label: int) -> str`

Get the Fashion-MNIST class name for a given label.

**Parameters:**
- `label` (int): Integer label (0-9)

**Returns:**
- `str`: Class name string

#### `get_fashion_mnist_class_names() -> List[str]`

Get all Fashion-MNIST class names.

**Returns:**
- `list`: List of all 10 class name strings

### Usage Examples

#### Basic Usage

```python
from tryon.datasets import FashionMNIST
import numpy as np

# Create dataset instance
dataset = FashionMNIST(download=True)

# Get dataset info before loading
info = dataset.get_info()
print(f"Dataset: {info['name']}")
print(f"Classes: {info['num_classes']}")
print(f"Train size: {info['train_size']}")

# Load with normalization
(train_images, train_labels), (test_images, test_labels) = dataset.load(
    normalize=True,
    flatten=False
)

# Use dataset methods
print(f"Training set shape: {train_images.shape}")  # (60000, 28, 28)
print(f"Test set shape: {test_images.shape}")      # (10000, 28, 28)
print(f"Class 0: {dataset.get_class_name(0)}")      # 'T-shirt/top'

# Get updated info after loading
info = dataset.get_info()
print(f"Loaded: {info['loaded']}")
print(f"Normalized: {info['normalized']}")
```

#### Function-Based Usage

```python
from tryon.datasets import load_fashion_mnist, get_fashion_mnist_class_name
import numpy as np

# Load dataset
(train_images, train_labels), (test_images, test_labels) = load_fashion_mnist(
    normalize=True
)

# Get a random sample
idx = np.random.randint(0, len(train_images))
label = train_labels[idx]
class_name = get_fashion_mnist_class_name(label)

print(f"Sample {idx}:")
print(f"  Label: {label} ({class_name})")
print(f"  Image shape: {train_images[idx].shape}")
print(f"  Pixel range: [{train_images[idx].min():.2f}, {train_images[idx].max():.2f}]")
```

#### Custom Data Directory

```python
from tryon.datasets import FashionMNIST

# Specify custom directory
dataset = FashionMNIST(
    data_dir="./my_datasets/fashion_mnist",
    download=True
)

(train_images, train_labels), (test_images, test_labels) = dataset.load()
```

### Best Practices

1. **Use normalization** for neural networks: `normalize=True`
2. **Use flattening** for traditional ML algorithms: `flatten=True`
3. **Check dataset info** before loading: `dataset.get_info()`
4. **Use class-based approach** for state management and caching
5. **Use function-based approach** for simple scripts and quick prototyping

---

## VITON-HD

### Overview

VITON-HD is a high-resolution virtual try-on dataset designed for training and evaluating virtual try-on models. It's ideal for:

- **Virtual try-on research** and development
- **High-resolution image generation** tasks
- **Fashion AI applications**
- **Computer vision research**

**Dataset Statistics:**
- **11,647 training pairs**
- **2,032 test pairs**
- **1024×768 resolution** RGB images
- **~4.6GB total size** (requires manual download)

**Dataset Structure:**
```
viton_hd/
├── person/          # Person images
├── clothing/        # Clothing images
├── train_pairs.txt  # Training pairs (person, clothing)
└── test_pairs.txt   # Test pairs (person, clothing)
```

**⚠️ Important Notes:**
- **Large dataset**: Uses **lazy loading** via PyTorch DataLoader to avoid memory issues
- **Manual download required**: Dataset must be downloaded manually from the official repository
- **High memory usage**: Each image is ~2.4MB uncompressed
- **PyTorch required**: Uses PyTorch DataLoader for efficient batching

**Reference:** 
- [VITON-HD GitHub](https://github.com/shadow2496/VITON-HD)
- [Paper](https://arxiv.org/abs/2103.16874)

### API Reference

#### Class: `VITONHD`

VITON-HD dataset adapter class with lazy loading support via PyTorch DataLoader.

##### Constructor

```python
VITONHD(
    data_dir: Optional[Union[str, Path]] = None,
    download: bool = False,
    train_pairs_file: str = "train_pairs.txt",
    test_pairs_file: str = "test_pairs.txt",
    person_dir: str = "person",
    clothing_dir: str = "clothing"
)
```

**Parameters:**
- `data_dir` (str or Path, optional): Directory containing the dataset. Defaults to `~/.opentryon/datasets/viton_hd`
- `download` (bool): Currently not implemented. Dataset must be downloaded manually. Default: `False`
- `train_pairs_file` (str): Name of training pairs file. Default: `"train_pairs.txt"`
- `test_pairs_file` (str): Name of test pairs file. Default: `"test_pairs.txt"`
- `person_dir` (str): Directory name containing person images. Default: `"person"`
- `clothing_dir` (str): Directory name containing clothing images. Default: `"clothing"`

**Raises:**
- `FileNotFoundError`: If dataset structure is invalid or missing

**Example:**
```python
# Use default directory
dataset = VITONHD(download=False)

# Use custom directory
dataset = VITONHD(data_dir="./datasets/viton_hd", download=False)
```

##### Methods

###### `get_dataloader(split='train', batch_size=8, shuffle=True, num_workers=4, pin_memory=True, transform=None, return_numpy=False, collate_fn=None) -> DataLoader`

Get a PyTorch DataLoader for efficient lazy loading. **This is the recommended method for training.**

**Parameters:**
- `split` (str): `'train'` or `'test'`
- `batch_size` (int): Batch size for the DataLoader. Default: `8`
- `shuffle` (bool): Whether to shuffle the data. Default: `True` (recommended for training)
- `num_workers` (int): Number of worker processes for data loading. Default: `4`
  - Set to `0` for single-process loading (useful for debugging)
  - Higher values improve throughput but use more memory
- `pin_memory` (bool): Whether to pin memory for faster GPU transfer. Default: `True`
- `transform` (Callable, optional): Transform to apply to images. Should accept PIL Images and return tensors or numpy arrays. Common transforms from `torchvision.transforms` work well.
- `return_numpy` (bool): If `True`, return numpy arrays instead of PIL Images. Default: `False`
  - **Note**: For best performance with DataLoader, use transforms that output tensors and set `return_numpy=False`
- `collate_fn` (Callable, optional): Custom collate function for batching. If `None`, uses default dictionary collate function that handles tensors, numpy arrays, and PIL Images.

**Returns:**
- `DataLoader`: PyTorch DataLoader instance

**Batch Format:**
Each batch is a dictionary with:
- `'person'`: Batched person images `[batch_size, 3, H, W]` (tensor) or `[batch_size, H, W, 3]` (numpy)
- `'clothing'`: Batched clothing images `[batch_size, 3, H, W]` (tensor) or `[batch_size, H, W, 3]` (numpy)
- `'person_path'`: List of person image paths (strings)
- `'clothing_path'`: List of clothing image paths (strings)
- `'index'`: Tensor of sample indices

**Example:**
```python
from torchvision import transforms

transform = transforms.Compose([
    transforms.Resize((512, 384)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
])

train_loader = dataset.get_dataloader(
    split='train',
    batch_size=16,
    shuffle=True,
    num_workers=4,
    transform=transform
)

for batch in train_loader:
    person_batch = batch['person']  # [16, 3, 384, 512]
    clothing_batch = batch['clothing']  # [16, 3, 384, 512]
    # Train model...
```

###### `get_sample(index, split='train', return_numpy=True) -> Dict[str, Any]`

Get a single sample from the dataset. Useful for inspection, visualization, or single-sample inference.

**Parameters:**
- `index` (int): Index of the sample (0-indexed)
- `split` (str): `'train'` or `'test'`
- `return_numpy` (bool): If `True`, return numpy arrays instead of PIL Images. Default: `True`

**Returns:**
- `dict`: Dictionary containing:
  - `'person'`: Person image (PIL Image or numpy array)
  - `'clothing'`: Clothing image (PIL Image or numpy array)
  - `'person_path'`: Path to person image (string)
  - `'clothing_path'`: Path to clothing image (string)
  - `'index'`: Original index (int)

**Raises:**
- `IndexError`: If index is out of range

**Example:**
```python
sample = dataset.get_sample(0, split='train', return_numpy=True)
person_img = sample['person']  # numpy array shape: (768, 1024, 3)
clothing_img = sample['clothing']  # numpy array shape: (768, 1024, 3)
print(f"Person shape: {person_img.shape}")
print(f"Person path: {sample['person_path']}")
```

###### `load(split='train', normalize=False, flatten=False, max_samples=None, **kwargs) -> Tuple[Tuple[np.ndarray, np.ndarray], Tuple[np.ndarray, np.ndarray]]`

⚠️ **Warning**: This method loads images into memory. For large datasets like VITON-HD, this can cause memory issues. Use `get_dataloader()` instead for lazy loading.

Load dataset samples into memory. Provided for compatibility with the base Dataset interface and for cases where you need all data in memory (e.g., small subsets for quick prototyping).

**Parameters:**
- `split` (str): `'train'` or `'test'`
- `normalize` (bool): If `True`, normalize pixel values to [0, 1] range. Default: `False`
- `flatten` (bool): If `True`, flatten images to 1D arrays. **Not recommended** for high-resolution images. Default: `False`
- `max_samples` (int, optional): Maximum number of samples to load. Use this to limit memory usage. Default: `None` (loads all)

**Returns:**
- `(train_data, test_data)` tuple where each is `(person_images, clothing_images)`
  - For compatibility, returns empty arrays for the split that wasn't requested
  - `person_images`: numpy array of shape `(num_samples, H, W, 3)`
  - `clothing_images`: numpy array of shape `(num_samples, H, W, 3)`

**Example:**
```python
# Load only first 100 samples to avoid memory issues
(person_imgs, clothing_imgs), _ = dataset.load(
    split='train',
    max_samples=100,
    normalize=True
)
print(f"Loaded {len(person_imgs)} samples")
print(f"Person images shape: {person_imgs.shape}")  # (100, 768, 1024, 3)
```

###### `get_class_names() -> List[str]`

Get class names for VITON-HD.

**Note**: VITON-HD doesn't have traditional classification classes, but returns descriptive labels for the dataset structure.

**Returns:**
- `list`: `['person', 'clothing']`

###### `get_info() -> Dict[str, Any]`

Get comprehensive VITON-HD dataset information.

**Returns:**
- `dict`: Dictionary containing:
  - `name`: Dataset class name (`'VITONHD'`)
  - `data_dir`: Path to dataset directory
  - `loaded`: Whether data has been loaded into memory
  - `train_size`: Number of training pairs
  - `test_size`: Number of test pairs
  - `image_resolution`: Expected image resolution (`'1024x768'`)
  - `image_shape`: Actual image shape from a sample `(H, W)` (if available)
  - `person_dir`: Directory name for person images
  - `clothing_dir`: Directory name for clothing images

**Example:**
```python
info = dataset.get_info()
print(f"Train size: {info['train_size']}")  # 11647
print(f"Test size: {info['test_size']}")    # 2032
print(f"Image resolution: {info['image_resolution']}")  # '1024x768'
```

### Convenience Functions

#### `load_viton_hd(data_dir=None, split='train', max_samples=None, normalize=False) -> Tuple[np.ndarray, np.ndarray]`

⚠️ **Warning**: This function loads images into memory. For large datasets, use the `VITONHD` class with `get_dataloader()`.

Load VITON-HD dataset samples (convenience function).

**Parameters:**
- `data_dir` (str or Path, optional): Directory containing the dataset
- `split` (str): `'train'` or `'test'`
- `max_samples` (int, optional): Maximum number of samples to load
- `normalize` (bool): If `True`, normalize pixel values to [0, 1] range

**Returns:**
- `(person_images, clothing_images)`: Tuple of numpy arrays

**Example:**
```python
from tryon.datasets import load_viton_hd

person_imgs, clothing_imgs = load_viton_hd(
    data_dir="./datasets/viton_hd",
    split='train',
    max_samples=100,
    normalize=True
)
```

### Usage Examples

#### Training with PyTorch DataLoader (Recommended)

```python
from tryon.datasets import VITONHD
from torchvision import transforms
import torch
import torch.nn as nn

# Setup
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
dataset = VITONHD(data_dir="./datasets/viton_hd", download=False)

# Define transforms
transform = transforms.Compose([
    transforms.Resize((512, 384)),
    transforms.RandomHorizontalFlip(p=0.5),  # Data augmentation
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
])

# Get DataLoaders
train_loader = dataset.get_dataloader(
    split='train',
    batch_size=8,
    shuffle=True,
    num_workers=4,
    transform=transform
)

test_loader = dataset.get_dataloader(
    split='test',
    batch_size=8,
    shuffle=False,
    num_workers=4,
    transform=transform
)

# Training loop
model = YourModel().to(device)
optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)
criterion = nn.MSELoss()

for epoch in range(num_epochs):
    model.train()
    for batch in train_loader:
        person_imgs = batch['person'].to(device)
        clothing_imgs = batch['clothing'].to(device)
        
        # Forward pass
        output = model(person_imgs, clothing_imgs)
        loss = criterion(output, target)
        
        # Backward pass
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
```

#### Custom Transforms

```python
from tryon.datasets import VITONHD
from torchvision import transforms

dataset = VITONHD(data_dir="./datasets/viton_hd")

# Custom transform pipeline with data augmentation
custom_transform = transforms.Compose([
    transforms.Resize((256, 256)),
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
    transforms.RandomRotation(degrees=10),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])  # ImageNet stats
])

train_loader = dataset.get_dataloader(
    split='train',
    batch_size=4,
    shuffle=True,
    transform=custom_transform
)
```

#### Single Sample Access

```python
from tryon.datasets import VITONHD
import matplotlib.pyplot as plt

dataset = VITONHD(data_dir="./datasets/viton_hd")

# Get a single sample
sample = dataset.get_sample(index=0, split='train', return_numpy=True)
person_img = sample['person']  # numpy array
clothing_img = sample['clothing']  # numpy array

# Visualize
fig, axes = plt.subplots(1, 2, figsize=(12, 6))
axes[0].imshow(person_img)
axes[0].set_title('Person Image')
axes[0].axis('off')
axes[1].imshow(clothing_img)
axes[1].set_title('Clothing Image')
axes[1].axis('off')
plt.tight_layout()
plt.show()
```

#### Loading Limited Samples to Memory

```python
from tryon.datasets import VITONHD

dataset = VITONHD(data_dir="./datasets/viton_hd")

# Load only first 100 samples (to avoid memory issues)
(person_imgs, clothing_imgs), _ = dataset.load(
    split='train',
    max_samples=100,
    normalize=True
)

print(f"Loaded {len(person_imgs)} samples")
print(f"Person images shape: {person_imgs.shape}")  # (100, 768, 1024, 3)
print(f"Clothing images shape: {clothing_imgs.shape}")  # (100, 768, 1024, 3)
print(f"Memory usage: ~{person_imgs.nbytes / 1024**2:.2f} MB")
```

#### Dataset Information

```python
from tryon.datasets import VITONHD

dataset = VITONHD(data_dir="./datasets/viton_hd")

# Get comprehensive info
info = dataset.get_info()
print(f"Dataset: {info['name']}")
print(f"Train size: {info['train_size']}")  # 11647
print(f"Test size: {info['test_size']}")    # 2032
print(f"Image resolution: {info['image_resolution']}")  # '1024x768'
print(f"Image shape: {info.get('image_shape', 'N/A')}")  # (768, 1024)
```

### Best Practices

1. **Use DataLoader for training**: Always use `get_dataloader()` for training loops
2. **Limit memory usage**: Use `max_samples` when loading to memory
3. **Use appropriate batch sizes**: Start with 4-8 for high-resolution images
4. **Optimize num_workers**: Use 4-8 workers for faster data loading
5. **Apply transforms**: Use `torchvision.transforms` for preprocessing and augmentation
6. **Pin memory**: Keep `pin_memory=True` for GPU training
7. **Validate dataset**: Check `get_info()` before training

### Performance Considerations

**Memory Usage:**
- Each image is ~2.4MB uncompressed (1024×768×3)
- Full training set: ~28GB uncompressed
- Use `get_dataloader()` with appropriate `batch_size` to avoid OOM errors

**Loading Speed:**
- `num_workers=4-8` provides good balance between speed and memory
- `pin_memory=True` speeds up GPU transfer
- SSD storage significantly improves loading speed

**Recommended Settings:**
- **Training**: `batch_size=4-8`, `num_workers=4-8`, `shuffle=True`
- **Inference**: `batch_size=8-16`, `num_workers=2-4`, `shuffle=False`
- **Debugging**: `batch_size=1`, `num_workers=0`, `shuffle=False`

---

## Subjects200K

### Overview

Subjects200K is a large-scale dataset containing 200,000 paired images, introduced as part of the OminiControl project. Each image pair maintains subject consistency while presenting variations in scene context. The dataset is ideal for:

- **Subject consistency research** and training
- **Multi-image generation** and composition
- **Style transfer** and scene variation studies
- **Large-scale training** with paired image data

**Dataset Statistics:**
- **Collection 1**: 512×512 resolution, 18,396 image pairs (8,200 high-quality)
- **Collection 2**: 512×512 resolution, 187,840 image pairs (111,767 high-quality)
- **Collection 3**: 1024×1024 resolution
- **Total**: ~200,000 paired images
- **Format**: Each image is a composite containing a pair of images with 16-pixel padding

**Key Features:**
- ✅ Loaded from HuggingFace (no manual download needed)
- ✅ Quality assessment scores for filtering
- ✅ Three collections with different resolutions
- ✅ PyTorch DataLoader integration
- ✅ Lazy loading support for efficient memory usage
- ✅ Collection and quality filtering options

**Reference:** 
- [Subjects200K GitHub](https://github.com/Yuanshi9815/Subjects200K)
- [HuggingFace Dataset](https://huggingface.co/datasets/Yuanshi/Subjects200K)

### API Reference

#### Class: `Subjects200K`

Subjects200K dataset adapter class that loads data from HuggingFace.

##### Constructor

```python
Subjects200K(data_dir: Optional[str] = None, download: bool = True, cache_dir: Optional[str] = None)
```

**Parameters:**
- `data_dir` (str, optional): Directory to store the dataset cache. Defaults to `~/.opentryon/datasets/subjects200k`
- `download` (bool): If `True`, download the dataset if it doesn't exist (always True for HuggingFace). Default: `True`
- `cache_dir` (str, optional): Optional cache directory for HuggingFace datasets. If None, uses `~/.cache/huggingface/datasets`

**Example:**
```python
# Use default directory
dataset = Subjects200K()

# Use custom cache directory
dataset = Subjects200K(cache_dir="./hf_cache")
```

##### Methods

###### `get_hf_dataset() -> Any`

Get the HuggingFace dataset instance.

**Returns:**
- HuggingFace dataset instance with 'train' split

**Example:**
```python
hf_dataset = dataset.get_hf_dataset()
sample = hf_dataset['train'][0]
image = sample['image']  # PIL Image
collection = sample['collection']  # 'collection_1', 'collection_2', or 'collection_3'
quality = sample['quality_assessment']  # Dict with quality scores
```

###### `filter_high_quality(collection=None, min_quality_score=5, num_proc=None, cache_file_name=None) -> Any`

Filter high-quality image pairs from the dataset.

**Parameters:**
- `collection` (str, optional): Collection filter ('collection_1', 'collection_2', 'collection_3'). If None, filters across all collections.
- `min_quality_score` (int): Minimum quality score threshold (default: 5). Filters samples where all quality dimensions (compositeStructure, objectConsistency, imageQuality) are >= min_quality_score.
- `num_proc` (int, optional): Number of processes for filtering (default: None, uses all available).
- `cache_file_name` (str, optional): Optional cache file path for filtered dataset.

**Returns:**
- Filtered HuggingFace dataset

**Example:**
```python
# Filter high-quality pairs from collection_2
filtered = dataset.filter_high_quality(
    collection='collection_2',
    min_quality_score=5
)
print(f"High-quality pairs: {len(filtered)}")
```

###### `get_pytorch_dataset(split='train', transform=None, collection=None, filter_high_quality=False) -> Subjects200KPyTorchDataset`

Get a PyTorch Dataset instance for Subjects200K.

**Parameters:**
- `split` (str): Dataset split ('train' or 'test'). Default: 'train'
- `transform` (Callable, optional): Optional transform to apply to images
- `collection` (str, optional): Collection filter ('collection_1', 'collection_2', 'collection_3')
- `filter_high_quality` (bool): If True, filter samples with quality scores >= 5. Default: False

**Returns:**
- `Subjects200KPyTorchDataset` instance

**Example:**
```python
from torchvision import transforms

transform = transforms.Compose([
    transforms.Resize((512, 512)),
    transforms.ToTensor(),
])

pytorch_dataset = dataset.get_pytorch_dataset(
    transform=transform,
    collection='collection_2',
    filter_high_quality=True
)
```

###### `get_dataloader(split='train', batch_size=8, shuffle=True, num_workers=0, transform=None, collection=None, filter_high_quality=False, **dataloader_kwargs) -> DataLoader`

Get a PyTorch DataLoader for Subjects200K.

**Parameters:**
- `split` (str): Dataset split ('train' or 'test'). Default: 'train'
- `batch_size` (int): Batch size for DataLoader. Default: 8
- `shuffle` (bool): Whether to shuffle the dataset. Default: True
- `num_workers` (int): Number of worker processes for data loading. Default: 0
- `transform` (Callable, optional): Optional transform to apply to images
- `collection` (str, optional): Collection filter ('collection_1', 'collection_2', 'collection_3')
- `filter_high_quality` (bool): If True, filter samples with quality scores >= 5. Default: False
- `**dataloader_kwargs`: Additional arguments for DataLoader

**Returns:**
- PyTorch DataLoader instance

**Example:**
```python
dataloader = dataset.get_dataloader(
    batch_size=16,
    transform=transform,
    collection='collection_2',
    filter_high_quality=True,
    num_workers=4
)

for batch in dataloader:
    images = batch['image']  # [batch_size, 3, H, W]
    collections = batch['collection']
    quality_assessments = batch['quality_assessment']
```

###### `get_sample(index, split='train', return_numpy=False) -> Dict[str, Any]`

Get a single sample from the dataset.

**Parameters:**
- `index` (int): Sample index
- `split` (str): Dataset split ('train' or 'test'). Default: 'train'
- `return_numpy` (bool): If True, return image as numpy array instead of PIL Image. Default: False

**Returns:**
- Dictionary containing sample data with keys: 'image', 'collection', 'quality_assessment', 'description', 'index'

**Example:**
```python
sample = dataset.get_sample(0)
image = sample['image']  # PIL Image
collection = sample['collection']
quality = sample['quality_assessment']
```

###### `load(normalize=False, flatten=False, **kwargs) -> tuple`

⚠️ **Warning**: This method loads the entire dataset into memory, which may not be feasible for large collections. Use `get_dataloader()` for efficient batch processing.

Load Subjects200K dataset into memory (for compatibility with base Dataset interface).

**Parameters:**
- `normalize` (bool): Not applicable for this dataset (images are already in [0, 255])
- `flatten` (bool): Not applicable for this dataset
- `**kwargs`: Additional arguments (ignored)

**Returns:**
- Tuple containing `(train_data, test_data)` where each is `(images, metadata)`

**Note:** This method is provided for compatibility but is not recommended for large datasets. Use `get_dataloader()` instead.

###### `get_class_names() -> List[str]`

Get collection names for Subjects200K.

**Returns:**
- List of collection names: `['collection_1', 'collection_2', 'collection_3']`

###### `get_info() -> Dict[str, Any]`

Get comprehensive Subjects200K dataset information.

**Returns:**
- Dictionary containing:
  - `name`: Dataset class name (`'Subjects200K'`)
  - `data_dir`: Path to dataset directory
  - `loaded`: Whether data has been loaded into memory
  - `hf_dataset_name`: HuggingFace dataset name (`'Yuanshi/Subjects200K'`)
  - `collections`: List of collection names
  - `total_samples`: Total number of samples (if loaded)

**Example:**
```python
info = dataset.get_info()
print(f"Dataset: {info['name']}")
print(f"Collections: {info['collections']}")
print(f"Total samples: {info['total_samples']}")
```

### Convenience Functions

#### `load_subjects200k(data_dir=None, download=True, cache_dir=None) -> Any`

Load Subjects200K dataset from HuggingFace (convenience function).

**Parameters:**
- `data_dir` (str, optional): Directory to store the dataset cache
- `download` (bool): If True, download the dataset if it doesn't exist
- `cache_dir` (str, optional): Optional cache directory for HuggingFace datasets

**Returns:**
- HuggingFace dataset instance

**Example:**
```python
from tryon.datasets import load_subjects200k

hf_dataset = load_subjects200k()
sample = hf_dataset['train'][0]
```

### Usage Examples

#### Basic Usage

```python
from tryon.datasets import Subjects200K

# Create dataset instance (loads from HuggingFace)
dataset = Subjects200K()

# Get HuggingFace dataset
hf_dataset = dataset.get_hf_dataset()
print(f"Total samples: {len(hf_dataset['train'])}")

# Access a sample
sample = hf_dataset['train'][0]
image = sample['image']  # PIL Image (composite with paired images)
collection = sample['collection']  # 'collection_1', 'collection_2', or 'collection_3'
quality = sample['quality_assessment']  # Dict with quality scores
description = sample.get('description')  # Optional description
```

#### Filter High-Quality Samples

```python
from tryon.datasets import Subjects200K

dataset = Subjects200K()

# Filter high-quality pairs from collection_2
filtered = dataset.filter_high_quality(
    collection='collection_2',
    min_quality_score=5
)

print(f"High-quality pairs: {len(filtered)}")

# Access filtered samples
for idx in range(min(10, len(filtered))):
    sample = filtered[idx]
    quality = sample['quality_assessment']
    print(f"Sample {idx}: {quality}")
```

#### PyTorch DataLoader Usage

```python
from tryon.datasets import Subjects200K
from torchvision import transforms

# Create dataset
dataset = Subjects200K()

# Define transforms
transform = transforms.Compose([
    transforms.Resize((512, 512)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
])

# Get DataLoader with quality filtering
dataloader = dataset.get_dataloader(
    batch_size=16,
    shuffle=True,
    transform=transform,
    collection='collection_2',
    filter_high_quality=True,
    num_workers=4
)

# Use in training loop
for batch_idx, batch in enumerate(dataloader):
    images = batch['image']  # [batch_size, 3, H, W]
    collections = batch['collection']
    quality_assessments = batch['quality_assessment']
    
    # Train model...
    if batch_idx >= 10:  # Limit for example
        break
```

#### Get Individual Samples

```python
from tryon.datasets import Subjects200K

dataset = Subjects200K()

# Get a specific sample
sample = dataset.get_sample(0)
image = sample['image']  # PIL Image
collection = sample['collection']
quality = sample['quality_assessment']

print(f"Collection: {collection}")
print(f"Quality scores: {quality}")

# Get sample as numpy array
sample_np = dataset.get_sample(0, return_numpy=True)
image_array = sample_np['image']  # numpy array
```

### Best Practices

1. **Use DataLoader for training**: Always use `get_dataloader()` for efficient batch processing
2. **Filter high-quality samples**: Use `filter_high_quality=True` for better training data
3. **Specify collection**: Filter by collection if you need specific resolution or quality
4. **Use transforms**: Apply appropriate transforms for your model requirements
5. **Set num_workers**: Use `num_workers > 0` for faster data loading (if you have multiple CPU cores)
6. **Cache filtered datasets**: Use `cache_file_name` parameter to cache filtered datasets for faster subsequent loads
7. **Memory management**: Don't use `load()` method for large collections; use DataLoader instead

### Performance Considerations

1. **HuggingFace caching**: The dataset is cached locally after first download, so subsequent loads are faster
2. **Lazy loading**: DataLoader uses lazy loading, so only batches are loaded into memory
3. **Filtering overhead**: Quality filtering can be slow for large datasets; use `cache_file_name` to cache results
4. **Multi-processing**: Use `num_workers > 0` in DataLoader for parallel data loading
5. **Collection selection**: Filtering by collection reduces dataset size and improves performance

**Note**: Subjects200K is a very large dataset (~200K samples). It's recommended to:
- Use DataLoader with batching instead of loading entire dataset
- Filter by collection or quality to reduce dataset size
- Use appropriate batch sizes based on your GPU memory
- Cache filtered datasets for faster subsequent access

---

## Adding New Datasets

To add a new dataset, create a class that extends `Dataset`:

```python
from tryon.datasets import Dataset
from pathlib import Path
import numpy as np

class MyNewDataset(Dataset):
    def _get_default_data_dir(self) -> Path:
        """Return default data directory."""
        return Path.home() / '.opentryon' / 'datasets' / 'my_dataset'
    
    def _ensure_downloaded(self) -> None:
        """Download dataset files if needed."""
        # Check if files exist
        required_files = ['file1.npy', 'file2.npy']
        for file in required_files:
            if not (self.data_dir / file).exists():
                # Download logic here
                self._download_file(url, self.data_dir / file)
    
    def load(self, normalize=False, **kwargs):
        """Load and return dataset."""
        # Load data
        train_images = np.load(self.data_dir / 'train_images.npy')
        train_labels = np.load(self.data_dir / 'train_labels.npy')
        
        if normalize:
            train_images = train_images.astype(np.float32) / 255.0
        
        # Return in standard format
        return (train_images, train_labels), (test_images, test_labels)
    
    def get_class_names(self) -> list:
        """Return list of class names."""
        return ['class1', 'class2', 'class3']
```

## Dataset Storage

By default, datasets are stored in:
```
~/.opentryon/datasets/{dataset_name}/
```

### Fashion-MNIST Storage

Location: `~/.opentryon/datasets/fashion_mnist/`

Files:
- `train-images-idx3-ubyte.gz` - Training images (compressed)
- `train-labels-idx1-ubyte.gz` - Training labels (compressed)
- `t10k-images-idx3-ubyte.gz` - Test images (compressed)
- `t10k-labels-idx1-ubyte.gz` - Test labels (compressed)

**Total size**: ~60MB (compressed)

### VITON-HD Storage

Location: `~/.opentryon/datasets/viton_hd/` (or custom path)

### Subjects200K Storage

Location: `~/.opentryon/datasets/subjects200k/` (or custom path)

**HuggingFace Cache:**
- Default cache: `~/.cache/huggingface/datasets/`
- Can be customized via `cache_dir` parameter
- Dataset is cached after first download for faster subsequent loads

Structure:
```
viton_hd/
├── person/          # Person images directory
│   ├── 00001_00.jpg
│   ├── 00001_01.jpg
│   └── ...
├── clothing/        # Clothing images directory
│   ├── 00001_00.jpg
│   ├── 00001_01.jpg
│   └── ...
├── train_pairs.txt  # Training pairs file
└── test_pairs.txt   # Test pairs file
```

**Total size**: ~4.6GB (uncompressed)

**Pairs file format:**
```
person_image.jpg clothing_image.jpg
00001_00.jpg 00001_00.jpg
00001_01.jpg 00001_01.jpg
...
```

### Subjects200K Storage

Location: `~/.opentryon/datasets/subjects200k/` (or custom path)

**HuggingFace Cache:**
- Default cache: `~/.cache/huggingface/datasets/`
- Can be customized via `cache_dir` parameter
- Dataset is cached after first download for faster subsequent loads

**Dataset Structure:**
- Loaded from HuggingFace: `Yuanshi/Subjects200K`
- Each sample contains:
  - `image`: PIL Image (composite with paired images, 16-pixel padding)
  - `collection`: Collection identifier ('collection_1', 'collection_2', 'collection_3')
  - `quality_assessment`: Dict with quality scores (compositeStructure, objectConsistency, imageQuality)
  - `description`: Optional text description

**Collections:**
- Collection 1: 512×512 resolution, 18,396 pairs (8,200 high-quality)
- Collection 2: 512×512 resolution, 187,840 pairs (111,767 high-quality)
- Collection 3: 1024×1024 resolution

## Requirements

### Core Dependencies
- `numpy` - For array operations
- Standard library: `os`, `gzip`, `struct`, `urllib.request`, `pathlib`

### VITON-HD Additional Dependencies
- `torch` - PyTorch for DataLoader support
- `torchvision` - For transforms (optional but recommended)
- `PIL` (Pillow) - For image loading

### Subjects200K Additional Dependencies
- `datasets` - HuggingFace datasets library (required)
  ```bash
  pip install datasets
  ```
- `torch` - PyTorch for DataLoader support
- `torchvision` - For transforms (optional but recommended)
- `PIL` (Pillow) - For image loading

### Installation

```bash
# Core dependencies
pip install numpy

# For VITON-HD
pip install torch torchvision pillow
```

## Troubleshooting

### Fashion-MNIST

**Issue: Download fails**
- **Solution**: Check internet connection. The dataset is hosted on AWS S3. Try downloading manually from [Fashion-MNIST GitHub](https://github.com/zalandoresearch/fashion-mnist).

**Issue: File not found errors**
- **Solution**: Ensure `data_dir` path is correct and has write permissions.

**Issue: Memory errors with large batches**
- **Solution**: Fashion-MNIST is small (~60MB), but if you're loading multiple copies, reduce batch size or use generators.

### VITON-HD

**Issue: `FileNotFoundError: Dataset not found`**
- **Solution**: 
  1. Download the dataset manually from [VITON-HD GitHub](https://github.com/shadow2496/VITON-HD)
  2. Extract to the expected directory structure
  3. Ensure `train_pairs.txt` and `test_pairs.txt` exist
  4. Verify `person/` and `clothing/` directories contain images

**Issue: `FileNotFoundError: Person/Clothing directory not found`**
- **Solution**: Check that the directory structure matches the expected format. Verify directory names match constructor parameters.

**Issue: Out of memory errors**
- **Solution**:
  - Reduce `batch_size` (try 2, 4, or 8)
  - Reduce `num_workers` (try 0, 2, or 4)
  - Use `max_samples` when loading to memory
  - Use `get_dataloader()` instead of `load()`

**Issue: Slow data loading**
- **Solution**:
  - Increase `num_workers` (but watch memory usage)
  - Use SSD storage instead of HDD
  - Reduce image resolution with transforms
  - Use `pin_memory=True` for GPU training

**Issue: Transform errors**
- **Solution**: Ensure transforms accept PIL Images. Most `torchvision.transforms` work correctly. If using custom transforms, ensure they handle PIL Image input.

**Issue: Batch shape errors**
- **Solution**: The default collate function handles tensors, numpy arrays, and PIL Images. If you need custom batching, provide a custom `collate_fn` to `get_dataloader()`.

**Issue: Index out of range**
- **Solution**: Check dataset size with `dataset.get_info()`. Ensure index is within `[0, dataset_size)`.

---

## Notes

- **Fashion-MNIST**: 
  - Downloads automatically on first use (if `download=True`)
  - Files are stored in compressed `.gz` format and decompressed on-the-fly
  - Follows the same format as the original MNIST dataset
  - All images are grayscale with pixel values 0-255 (or 0-1 if normalized)
  
- **VITON-HD**:
  - Requires manual download due to size (4.6GB)
  - Uses lazy loading to avoid memory issues
  - High-resolution images require careful memory management
  - PyTorch DataLoader provides efficient batching and multi-process loading

- **General**:
  - The class-based approach allows for caching and state management
  - Convenience functions are provided for backward compatibility and simplicity
  - All datasets follow a consistent API for easy switching between datasets
