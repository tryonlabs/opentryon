# Fashion-MNIST Dataset

Fashion-MNIST is a dataset of Zalando's article images designed as a drop-in replacement for the original MNIST dataset. It's ideal for quick prototyping, learning, and benchmarking classification algorithms.

## Overview

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

## Installation

Fashion-MNIST requires no additional dependencies beyond the core OpenTryOn package. The dataset will be automatically downloaded on first use.

## Usage

### Class-Based Approach (Recommended)

```python
from tryon.datasets import FashionMNIST

# Create dataset instance (downloads automatically)
dataset = FashionMNIST(download=True)

# Get dataset info
info = dataset.get_info()
print(f"Train size: {info['train_size']}")  # 60000
print(f"Test size: {info['test_size']}")    # 10000
print(f"Classes: {info['num_classes']}")    # 10

# Load the dataset
(train_images, train_labels), (test_images, test_labels) = dataset.load(
    normalize=True,
    flatten=False
)

print(f"Training set: {train_images.shape}")  # (60000, 28, 28)
print(f"Test set: {test_images.shape}")        # (10000, 28, 28)

# Get class names
print(dataset.get_class_name(0))  # 'T-shirt/top'
print(dataset.get_class_names())  # ['T-shirt/top', 'Trouser', ...]
```

### Function-Based Approach

```python
from tryon.datasets import load_fashion_mnist, get_fashion_mnist_class_name

# Load dataset
(train_images, train_labels), (test_images, test_labels) = load_fashion_mnist(
    normalize=True,
    flatten=False
)

# Get class name
class_name = get_fashion_mnist_class_name(0)  # 'T-shirt/top'
```

## API Reference

### Class: `FashionMNIST`

Fashion-MNIST dataset adapter class.

#### Constructor

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

#### Methods

##### `load(normalize=False, flatten=False)`

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
dataset = FashionMNIST()

# Load without normalization
(train_images, train_labels), (test_images, test_labels) = dataset.load(
    normalize=False,
    flatten=False
)
print(train_images.dtype)  # uint8
print(train_images.shape)  # (60000, 28, 28)

# Load with normalization
(train_images, train_labels), (test_images, test_labels) = dataset.load(
    normalize=True,
    flatten=False
)
print(train_images.dtype)  # float32
print(train_images.min(), train_images.max())  # 0.0 1.0

# Load flattened
(train_images, train_labels), (test_images, test_labels) = dataset.load(
    normalize=True,
    flatten=True
)
print(train_images.shape)  # (60000, 784)
```

##### `get_info()`

Get dataset information and metadata.

**Returns:**
- `dict`: Dictionary containing:
  - `name`: Dataset name ("Fashion-MNIST")
  - `train_size`: Number of training examples (60000)
  - `test_size`: Number of test examples (10000)
  - `num_classes`: Number of classes (10)
  - `image_shape`: Image shape tuple `(28, 28)`
  - `normalized`: Whether data is normalized (updated after `load()`)
  - `flattened`: Whether data is flattened (updated after `load()`)

**Example:**
```python
dataset = FashionMNIST()
info = dataset.get_info()
print(info)
# {
#     'name': 'Fashion-MNIST',
#     'train_size': 60000,
#     'test_size': 10000,
#     'num_classes': 10,
#     'image_shape': (28, 28),
#     'normalized': False,
#     'flattened': False
# }
```

##### `get_class_name(class_id: int)`

Get the name of a class by its ID.

**Parameters:**
- `class_id` (int): Class ID (0-9)

**Returns:**
- `str`: Class name

**Example:**
```python
dataset = FashionMNIST()
print(dataset.get_class_name(0))  # 'T-shirt/top'
print(dataset.get_class_name(9))  # 'Ankle boot'
```

##### `get_class_names()`

Get all class names.

**Returns:**
- `list[str]`: List of all class names

**Example:**
```python
dataset = FashionMNIST()
class_names = dataset.get_class_names()
print(class_names)
# ['T-shirt/top', 'Trouser', 'Pullover', 'Dress', 'Coat',
#  'Sandal', 'Shirt', 'Sneaker', 'Bag', 'Ankle boot']
```

### Functions

#### `load_fashion_mnist(normalize=False, flatten=False)`

Convenience function to load Fashion-MNIST dataset.

**Parameters:**
- `normalize` (bool): Normalize pixel values to [0, 1]. Default: `False`
- `flatten` (bool): Flatten images to 1D arrays. Default: `False`

**Returns:**
- `(train_data, test_data)` tuple where each is `(images, labels)`

**Example:**
```python
from tryon.datasets import load_fashion_mnist

(train_images, train_labels), (test_images, test_labels) = load_fashion_mnist(
    normalize=True,
    flatten=False
)
```

#### `get_fashion_mnist_class_name(class_id: int)`

Get class name by ID.

**Parameters:**
- `class_id` (int): Class ID (0-9)

**Returns:**
- `str`: Class name

#### `get_fashion_mnist_class_names()`

Get all class names.

**Returns:**
- `list[str]`: List of all class names

## Best Practices

### Normalization

For machine learning models, it's recommended to normalize pixel values:

```python
dataset = FashionMNIST()
(train_images, train_labels), (test_images, test_labels) = dataset.load(
    normalize=True,  # Normalize to [0, 1]
    flatten=False
)
```

### Memory Management

Fashion-MNIST is small enough (~60MB) to load entirely into memory. However, if you're working with limited memory:

```python
# Load only what you need
dataset = FashionMNIST()
(train_images, train_labels), _ = dataset.load(normalize=True)
# Use only training set, ignore test set
```

### Visualization

```python
import matplotlib.pyplot as plt
from tryon.datasets import FashionMNIST

dataset = FashionMNIST()
(train_images, train_labels), (test_images, test_labels) = dataset.load(
    normalize=False,
    flatten=False
)

# Visualize a sample
plt.figure(figsize=(10, 10))
for i in range(25):
    plt.subplot(5, 5, i + 1)
    plt.imshow(train_images[i], cmap='gray')
    plt.title(dataset.get_class_name(train_labels[i]))
    plt.axis('off')
plt.tight_layout()
plt.show()
```

## Examples

See [Dataset Examples](../examples/datasets) for complete usage examples.

## Troubleshooting

### Download Issues

If the dataset fails to download:

1. Check your internet connection
2. Verify write permissions to the data directory
3. Try specifying a custom `data_dir`:
   ```python
   dataset = FashionMNIST(data_dir="./my_datasets/fashion_mnist", download=True)
   ```

### Memory Issues

Fashion-MNIST is small, but if you encounter memory issues:

- Use `normalize=False` to keep data as `uint8` (smaller memory footprint)
- Load only the split you need (train or test)

