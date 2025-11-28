# Dataset Usage Examples

Complete examples demonstrating how to use the OpenTryOn datasets module with Fashion-MNIST, VITON-HD, and Subjects200K.

## Fashion-MNIST Examples

### Basic Usage

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
print(f"Test set: {test_images.shape}")        # (10000, 28, 28)
print(f"Class 0: {dataset.get_class_name(0)}")  # 'T-shirt/top'
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

### Class Distribution

```python
import numpy as np
from tryon.datasets import FashionMNIST

dataset = FashionMNIST()
(train_images, train_labels), (test_images, test_labels) = dataset.load()

# Count class distribution
unique, counts = np.unique(train_labels, return_counts=True)
class_names = dataset.get_class_names()

print("Training set class distribution:")
for class_id, count in zip(unique, counts):
    print(f"  {class_names[class_id]}: {count}")
```

### Custom Data Directory

```python
from tryon.datasets import FashionMNIST

# Use custom directory
dataset = FashionMNIST(
    data_dir="./my_datasets/fashion_mnist",
    download=True
)

(train_images, train_labels), (test_images, test_labels) = dataset.load()
```

## VITON-HD Examples

### Basic Usage with DataLoader

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
    person_imgs = batch['person']    # [batch_size, 3, H, W]
    clothing_imgs = batch['clothing']  # [batch_size, 3, H, W]
    # Train model...
```

### Single Sample Access

```python
from tryon.datasets import VITONHD
from PIL import Image

dataset = VITONHD(data_dir="./datasets/viton_hd")

# Get a single sample as PIL Images
sample = dataset.get_sample(0, split='train')
person_img = sample['person']      # PIL Image
clothing_img = sample['clothing']  # PIL Image

# Display images
person_img.show()
clothing_img.show()

# Get as numpy arrays
sample = dataset.get_sample(0, split='train', return_numpy=True)
person_img = sample['person']      # numpy array [H, W, 3]
clothing_img = sample['clothing']  # numpy array [H, W, 3]
```

### Training Loop Example

```python
import torch
import torch.nn as nn
from torch.optim import Adam
from tryon.datasets import VITONHD
from torchvision import transforms

# Create dataset
dataset = VITONHD(data_dir="./datasets/viton_hd")

# Define transforms with data augmentation
transform = transforms.Compose([
    transforms.Resize((512, 384)),
    transforms.RandomHorizontalFlip(),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
])

# Get DataLoaders
train_loader = dataset.get_dataloader(
    split='train',
    batch_size=8,
    shuffle=True,
    transform=transform,
    num_workers=4
)

test_loader = dataset.get_dataloader(
    split='test',
    batch_size=8,
    shuffle=False,
    transform=transform,
    num_workers=4
)

# Training loop
model = YourModel()  # Your model here
optimizer = Adam(model.parameters(), lr=1e-4)
criterion = nn.MSELoss()

for epoch in range(10):
    model.train()
    for batch in train_loader:
        person_imgs = batch['person']
        clothing_imgs = batch['clothing']
        
        # Forward pass
        output = model(person_imgs, clothing_imgs)
        loss = criterion(output, person_imgs)
        
        # Backward pass
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
    
    print(f"Epoch {epoch+1}, Loss: {loss.item()}")
```

### Dataset Information

```python
from tryon.datasets import VITONHD

dataset = VITONHD(data_dir="./datasets/viton_hd")

# Get dataset info
info = dataset.get_info()
print(f"Dataset: {info['name']}")
print(f"Train size: {info['train_size']}")
print(f"Test size: {info['test_size']}")
print(f"Image shape: {info['image_shape']}")
```

### Limited Memory Loading

```python
from tryon.datasets import VITONHD

dataset = VITONHD(data_dir="./datasets/viton_hd")

# Load only a subset to avoid memory issues
(person_imgs, clothing_imgs), metadata = dataset.load(
    split='train',
    max_samples=100,  # Limit to 100 samples
    normalize=True,
    return_numpy=True
)

print(f"Loaded {len(person_imgs)} samples")
```

## Combined Workflow Example

### Using Datasets with Virtual Try-On

```python
from tryon.datasets import VITONHD
from tryon.api import SegmindVTONAdapter
from torchvision import transforms
from dotenv import load_dotenv
load_dotenv()

# Load VITON-HD dataset
dataset = VITONHD(data_dir="./datasets/viton_hd")

# Get a sample
sample = dataset.get_sample(0, split='test')
person_img = sample['person']
clothing_img = sample['clothing']

# Save temporary images
person_img.save("temp_person.jpg")
clothing_img.save("temp_clothing.jpg")

# Use with Segmind API
adapter = SegmindVTONAdapter()
result_images = adapter.generate_and_decode(
    model_image="temp_person.jpg",
    cloth_image="temp_clothing.jpg",
    category="Upper body"
)

# Save result
result_images[0].save("vton_result.jpg")
```

## Best Practices

### Memory Management

For large datasets like VITON-HD, always use DataLoader:

```python
# ✅ Good: Use DataLoader
train_loader = dataset.get_dataloader(split='train', batch_size=8)

# ❌ Avoid: Loading everything into memory
person_imgs, clothing_imgs = dataset.load(split='train')  # Uses lots of RAM!
```

### Data Augmentation

Apply transforms through DataLoader:

```python
from torchvision import transforms

transform = transforms.Compose([
    transforms.Resize((512, 384)),
    transforms.RandomHorizontalFlip(),  # Data augmentation
    transforms.ColorJitter(brightness=0.2),  # More augmentation
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
])

train_loader = dataset.get_dataloader(
    split='train',
    batch_size=8,
    transform=transform
)
```

### Performance Optimization

Use multiple workers for faster data loading:

```python
train_loader = dataset.get_dataloader(
    split='train',
    batch_size=8,
    num_workers=4,  # Use 4 worker processes
    pin_memory=True  # Faster GPU transfer
)
```

## Subjects200K Examples

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

### DataLoader Usage

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
    # Train model...
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

## See Also

- [Datasets Overview](../datasets/overview) - Complete datasets documentation
- [Fashion-MNIST Documentation](../datasets/fashion-mnist) - Detailed Fashion-MNIST guide
- [VITON-HD Documentation](../datasets/viton-hd) - Detailed VITON-HD guide
- [Subjects200K Documentation](../datasets/subjects200k) - Detailed Subjects200K guide
- [API Reference](../api-reference/overview) - Complete API documentation

