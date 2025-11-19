# VITON-HD Dataset

VITON-HD is a high-resolution virtual try-on dataset consisting of person images and clothing images. It's perfect for training and evaluating virtual try-on models.

## Overview

**Dataset Statistics:**
- **11,647 training pairs**
- **2,032 test pairs**
- **1024×768 resolution images**
- **Person and clothing image pairs**

**Dataset Structure:**
- Person images: High-resolution images of people
- Clothing images: Corresponding garment images
- Pairs file: Text file mapping person images to clothing images

**Reference:** 
- [VITON-HD GitHub](https://github.com/shadow2496/VITON-HD)
- [Paper](https://arxiv.org/abs/2103.16874)

## Installation

VITON-HD requires PyTorch and torchvision for DataLoader support:

```bash
pip install torch torchvision pillow
```

## Usage

### Class-Based Approach (Recommended)

```python
from tryon.datasets import VITONHD
from torchvision import transforms

# Create dataset instance
dataset = VITONHD(data_dir="./datasets/viton_hd", download=False)

# Get dataset info
info = dataset.get_info()
print(f"Train size: {info['train_size']}")  # 11647
print(f"Test size: {info['test_size']}")    # 2032

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
    person_imgs = batch['person']    # [batch_size, 3, H, W]
    clothing_imgs = batch['clothing']  # [batch_size, 3, H, W]
    # Train model...
```

### Single Sample Access

```python
from tryon.datasets import VITONHD

dataset = VITONHD(data_dir="./datasets/viton_hd")

# Get a single sample
sample = dataset.get_sample(0, split='train')
person_img = sample['person']      # PIL Image
clothing_img = sample['clothing']  # PIL Image

# Or get as numpy arrays
sample = dataset.get_sample(0, split='train', return_numpy=True)
person_img = sample['person']      # numpy array
clothing_img = sample['clothing']  # numpy array
```

### Function-Based Approach

```python
from tryon.datasets import load_viton_hd

# Load dataset (use with caution - loads all data into memory)
person_imgs, clothing_imgs = load_viton_hd(
    data_dir="./datasets/viton_hd",
    split='train',
    max_samples=100,  # Limit to avoid memory issues
    normalize=True
)
```

## API Reference

### Class: `VITONHD`

VITON-HD dataset adapter class with lazy loading support via PyTorch DataLoader.

#### Constructor

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
- `download` (bool): If `True`, attempt to download the dataset. Default: `False` (manual download required)
- `train_pairs_file` (str): Name of training pairs file. Default: `"train_pairs.txt"`
- `test_pairs_file` (str): Name of test pairs file. Default: `"test_pairs.txt"`
- `person_dir` (str): Directory name containing person images. Default: `"person"`
- `clothing_dir` (str): Directory name containing clothing images. Default: `"clothing"`

**Example:**
```python
# Use default directory
dataset = VITONHD(download=False)

# Use custom directory
dataset = VITONHD(
    data_dir="./my_datasets/viton_hd",
    download=False
)
```

#### Methods

##### `get_dataloader(split='train', batch_size=1, shuffle=False, transform=None, num_workers=0, **kwargs)`

Get a PyTorch DataLoader for efficient batch processing.

**Parameters:**
- `split` (str): Dataset split. Options: `'train'` or `'test'`. Default: `'train'`
- `batch_size` (int): Batch size. Default: `1`
- `shuffle` (bool): Whether to shuffle the data. Default: `False`
- `transform` (callable, optional): Transform to apply to images. Default: `None`
- `num_workers` (int): Number of worker processes for data loading. Default: `0`
- `**kwargs`: Additional arguments passed to `torch.utils.data.DataLoader`

**Returns:**
- `torch.utils.data.DataLoader`: DataLoader yielding batches of dictionaries with keys:
  - `'person'`: Person image tensor `[batch_size, 3, H, W]`
  - `'clothing'`: Clothing image tensor `[batch_size, 3, H, W]`

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
    batch_size=8,
    shuffle=True,
    transform=transform,
    num_workers=4
)

for batch in train_loader:
    person_batch = batch['person']    # [8, 3, 384, 512]
    clothing_batch = batch['clothing']  # [8, 3, 384, 512]
```

##### `get_sample(idx, split='train', return_numpy=False)`

Get a single sample from the dataset.

**Parameters:**
- `idx` (int): Sample index
- `split` (str): Dataset split. Options: `'train'` or `'test'`. Default: `'train'`
- `return_numpy` (bool): If `True`, return numpy arrays instead of PIL Images. Default: `False`

**Returns:**
- `dict`: Dictionary with keys:
  - `'person'`: Person image (PIL Image or numpy array)
  - `'clothing'`: Clothing image (PIL Image or numpy array)

**Example:**
```python
# Get as PIL Images
sample = dataset.get_sample(0, split='train')
person_img = sample['person']      # PIL Image
clothing_img = sample['clothing']  # PIL Image

# Get as numpy arrays
sample = dataset.get_sample(0, split='train', return_numpy=True)
person_img = sample['person']      # numpy array [H, W, 3]
clothing_img = sample['clothing']  # numpy array [H, W, 3]
```

##### `get_info()`

Get dataset information and metadata.

**Returns:**
- `dict`: Dictionary containing:
  - `name`: Dataset name ("VITON-HD")
  - `train_size`: Number of training pairs (11647)
  - `test_size`: Number of test pairs (2032)
  - `image_shape`: Image shape tuple `(768, 1024)` (H, W)
  - `data_dir`: Dataset directory path

**Example:**
```python
info = dataset.get_info()
print(info)
# {
#     'name': 'VITON-HD',
#     'train_size': 11647,
#     'test_size': 2032,
#     'image_shape': (768, 1024),
#     'data_dir': PosixPath('/path/to/viton_hd')
# }
```

##### `load(split='train', max_samples=None, normalize=False, return_numpy=True)`

Load dataset into memory (use with caution for large datasets).

**Parameters:**
- `split` (str): Dataset split. Options: `'train'` or `'test'`. Default: `'train'`
- `max_samples` (int, optional): Maximum number of samples to load. Default: `None` (load all)
- `normalize` (bool): Normalize pixel values to [0, 1]. Default: `False`
- `return_numpy` (bool): Return numpy arrays instead of PIL Images. Default: `True`

**Returns:**
- `(person_images, clothing_images), metadata` tuple:
  - `person_images`: List of person images or numpy array
  - `clothing_images`: List of clothing images or numpy array
  - `metadata`: Dictionary with dataset information

**Warning:** Loading the full dataset into memory requires significant RAM. Use `max_samples` to limit the number of samples.

**Example:**
```python
# Load limited samples
(person_imgs, clothing_imgs), metadata = dataset.load(
    split='train',
    max_samples=100,
    normalize=True,
    return_numpy=True
)
```

### Class: `VITONHDPyTorchDataset`

Low-level PyTorch Dataset class for VITON-HD. Use `VITONHD.get_dataloader()` instead for most use cases.

### Functions

#### `load_viton_hd(data_dir, split='train', max_samples=None, normalize=False)`

Convenience function to load VITON-HD dataset into memory.

**Parameters:**
- `data_dir` (str): Directory containing the dataset
- `split` (str): Dataset split. Options: `'train'` or `'test'`. Default: `'train'`
- `max_samples` (int, optional): Maximum number of samples to load. Default: `None`
- `normalize` (bool): Normalize pixel values to [0, 1]. Default: `False`

**Returns:**
- `(person_images, clothing_images)` tuple of numpy arrays

**Warning:** Use with caution - loads all data into memory.

## Best Practices

### Use DataLoader for Training

For training models, always use `get_dataloader()` for efficient batch processing:

```python
from torchvision import transforms

transform = transforms.Compose([
    transforms.Resize((512, 384)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
])

train_loader = dataset.get_dataloader(
    split='train',
    batch_size=8,
    shuffle=True,
    transform=transform,
    num_workers=4  # Use multiple workers for faster loading
)
```

### Memory Management

VITON-HD is large (~13GB). Use lazy loading with DataLoader instead of loading everything into memory:

```python
# ✅ Good: Use DataLoader
train_loader = dataset.get_dataloader(split='train', batch_size=8)

# ❌ Avoid: Loading everything into memory
person_imgs, clothing_imgs = dataset.load(split='train')  # Uses lots of RAM!
```

### Transforms

Apply transforms through DataLoader for consistency:

```python
from torchvision import transforms

# Define transforms
transform = transforms.Compose([
    transforms.Resize((512, 384)),
    transforms.RandomHorizontalFlip(),  # Data augmentation
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
])

train_loader = dataset.get_dataloader(
    split='train',
    batch_size=8,
    transform=transform
)
```

## Performance Considerations

### DataLoader Workers

Use multiple workers for faster data loading:

```python
train_loader = dataset.get_dataloader(
    split='train',
    batch_size=8,
    num_workers=4  # Use 4 worker processes
)
```

**Note:** More workers use more CPU and memory. Adjust based on your system.

### Batch Size

Larger batch sizes improve GPU utilization but require more memory:

```python
# Small batch size (less memory)
train_loader = dataset.get_dataloader(batch_size=4)

# Large batch size (more memory, better GPU utilization)
train_loader = dataset.get_dataloader(batch_size=32)
```

## Examples

See [Dataset Examples](../examples/datasets) for complete usage examples.

## Troubleshooting

### Dataset Not Found

If you get a "dataset not found" error:

1. Download the VITON-HD dataset manually from the [official repository](https://github.com/shadow2496/VITON-HD)
2. Extract it to your data directory
3. Ensure the directory structure matches:
   ```
   viton_hd/
   ├── train_pairs.txt
   ├── test_pairs.txt
   ├── person/
   │   └── *.jpg
   └── clothing/
       └── *.jpg
   ```

### Memory Issues

If you encounter out-of-memory errors:

- Reduce `batch_size` in `get_dataloader()`
- Use `max_samples` when calling `load()`
- Reduce `num_workers` in DataLoader
- Use smaller image sizes in transforms

### Slow Data Loading

To speed up data loading:

- Increase `num_workers` in DataLoader
- Use SSD storage for dataset
- Pre-process images to smaller sizes
- Use data caching if available

