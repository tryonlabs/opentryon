---
sidebar_position: 3
title: Subjects200K Dataset
description: Large-scale dataset with 200,000 paired images for subject consistency research, loaded from HuggingFace.
keywords:
  - Subjects200K
  - paired images
  - subject consistency
  - HuggingFace
  - OminiControl
  - dataset
---

# Subjects200K Dataset

Subjects200K is a large-scale dataset containing 200,000 paired images, introduced as part of the OminiControl project. Each image pair maintains subject consistency while presenting variations in scene context.

## Overview

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

## Installation

Subjects200K requires the HuggingFace datasets library:

```bash
pip install datasets
```

## Quick Start

### Basic Usage

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
```

### PyTorch DataLoader

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
for batch in dataloader:
    images = batch['image']  # [batch_size, 3, H, W]
    collections = batch['collection']
    quality_assessments = batch['quality_assessment']
```

## API Reference

### Subjects200K

#### Constructor

```python
Subjects200K(data_dir: Optional[str] = None, download: bool = True, cache_dir: Optional[str] = None)
```

**Parameters:**
- `data_dir` (str, optional): Directory to store the dataset cache. Defaults to `~/.opentryon/datasets/subjects200k`
- `download` (bool): If `True`, download the dataset if it doesn't exist. Default: `True`
- `cache_dir` (str, optional): Optional cache directory for HuggingFace datasets

#### Methods

##### `get_hf_dataset() -> Any`

Get the HuggingFace dataset instance.

**Returns:**
- HuggingFace dataset instance with 'train' split

##### `filter_high_quality(collection=None, min_quality_score=5, num_proc=None, cache_file_name=None) -> Any`

Filter high-quality image pairs from the dataset.

**Parameters:**
- `collection` (str, optional): Collection filter ('collection_1', 'collection_2', 'collection_3')
- `min_quality_score` (int): Minimum quality score threshold (default: 5)
- `num_proc` (int, optional): Number of processes for filtering
- `cache_file_name` (str, optional): Optional cache file path for filtered dataset

##### `get_dataloader(split='train', batch_size=8, shuffle=True, num_workers=0, transform=None, collection=None, filter_high_quality=False, **dataloader_kwargs) -> DataLoader`

Get a PyTorch DataLoader for Subjects200K.

**Parameters:**
- `split` (str): Dataset split ('train' or 'test'). Default: 'train'
- `batch_size` (int): Batch size for DataLoader. Default: 8
- `shuffle` (bool): Whether to shuffle the dataset. Default: True
- `num_workers` (int): Number of worker processes. Default: 0
- `transform` (Callable, optional): Optional transform to apply to images
- `collection` (str, optional): Collection filter
- `filter_high_quality` (bool): If True, filter samples with quality scores >= 5

##### `get_sample(index, split='train', return_numpy=False) -> Dict[str, Any]`

Get a single sample from the dataset.

**Parameters:**
- `index` (int): Sample index
- `split` (str): Dataset split ('train' or 'test')
- `return_numpy` (bool): If True, return image as numpy array

## Usage Examples

### Filter High-Quality Samples

```python
from tryon.datasets import Subjects200K

dataset = Subjects200K()

# Filter high-quality pairs from collection_2
filtered = dataset.filter_high_quality(
    collection='collection_2',
    min_quality_score=5
)

print(f"High-quality pairs: {len(filtered)}")
```

### Get Individual Samples

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
```

## Best Practices

1. **Use DataLoader for training**: Always use `get_dataloader()` for efficient batch processing
2. **Filter high-quality samples**: Use `filter_high_quality=True` for better training data
3. **Specify collection**: Filter by collection if you need specific resolution or quality
4. **Use transforms**: Apply appropriate transforms for your model requirements
5. **Set num_workers**: Use `num_workers > 0` for faster data loading
6. **Cache filtered datasets**: Use `cache_file_name` parameter to cache filtered datasets
7. **Memory management**: Don't use `load()` method for large collections; use DataLoader instead

## Performance Considerations

- **HuggingFace caching**: Dataset is cached locally after first download
- **Lazy loading**: DataLoader uses lazy loading, so only batches are loaded into memory
- **Filtering overhead**: Quality filtering can be slow; use `cache_file_name` to cache results
- **Multi-processing**: Use `num_workers > 0` in DataLoader for parallel data loading
- **Collection selection**: Filtering by collection reduces dataset size and improves performance

## References

- [Subjects200K GitHub](https://github.com/Yuanshi9815/Subjects200K)
- [HuggingFace Dataset](https://huggingface.co/datasets/Yuanshi/Subjects200K)

