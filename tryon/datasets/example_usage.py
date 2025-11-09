"""
Example usage of dataset loaders.

This script demonstrates how to use both Fashion-MNIST and VITON-HD datasets
with their respective adapters.
"""

import numpy as np

try:
    from torchvision import transforms
    TORCHVISION_AVAILABLE = True
except ImportError:
    TORCHVISION_AVAILABLE = False
    transforms = None

from tryon.datasets import (
    FashionMNIST,
    load_fashion_mnist,
    get_fashion_mnist_class_name,
    get_fashion_mnist_class_names,
    VITONHD,
)


# ============================================================================
# FASHION-MNIST EXAMPLES
# ============================================================================

def fashion_mnist_class_based():
    """Example using the class-based approach (recommended for extensibility)."""
    print("\n" + "=" * 60)
    print("FASHION-MNIST: CLASS-BASED APPROACH")
    print("=" * 60)
    
    # Create dataset instance
    dataset = FashionMNIST(download=True)
    print(f"\nDataset: {dataset}")
    
    # Get dataset info before loading
    info = dataset.get_info()
    print(f"\nDataset info:")
    print(f"  Name: {info['name']}")
    print(f"  Classes: {info['num_classes']}")
    print(f"  Image shape: {info['image_shape']}")
    print(f"  Train size: {info['train_size']}")
    print(f"  Test size: {info['test_size']}")
    
    # Load the dataset
    (train_images, train_labels), (test_images, test_labels) = dataset.load(
        normalize=True,
        flatten=False
    )
    
    print(f"\nDataset loaded!")
    print(f"  Training set: {train_images.shape} images, {train_labels.shape} labels")
    print(f"  Test set: {test_images.shape} images, {test_labels.shape} labels")
    
    # Get updated info after loading
    info = dataset.get_info()
    print(f"\nAfter loading:")
    print(f"  Normalized: {info['normalized']}")
    print(f"  Flattened: {info['flattened']}")
    
    # Use class methods
    print(f"\nClass names:")
    for i, name in enumerate(dataset.get_class_names()):
        print(f"  {i}: {name}")
    
    # Get a random sample
    idx = np.random.randint(0, len(train_images))
    print(f"\nRandom sample:")
    print(f"  Index: {idx}")
    print(f"  Label: {train_labels[idx]} ({dataset.get_class_name(train_labels[idx])})")
    print(f"  Image shape: {train_images[idx].shape}")


def fashion_mnist_function_based():
    """Example using the function-based approach (simpler, backward compatible)."""
    print("\n" + "=" * 60)
    print("FASHION-MNIST: FUNCTION-BASED APPROACH")
    print("=" * 60)
    
    # Load the dataset using convenience function
    (train_images, train_labels), (test_images, test_labels) = load_fashion_mnist(
        download=True,
        normalize=True,
        flatten=False
    )
    
    print(f"\nDataset loaded!")
    print(f"  Training set: {train_images.shape} images, {train_labels.shape} labels")
    print(f"  Test set: {test_images.shape} images, {test_labels.shape} labels")
    print(f"  Image dtype: {train_images.dtype}")
    print(f"  Range: [{train_images.min():.2f}, {train_images.max():.2f}]")
    
    # Display class names
    print(f"\nClass names:")
    for i, name in enumerate(get_fashion_mnist_class_names()):
        print(f"  {i}: {name}")
    
    # Show label distribution
    print(f"\nLabel distribution (training set):")
    unique, counts = np.unique(train_labels, return_counts=True)
    for label, count in zip(unique, counts):
        print(f"  {label} ({get_fashion_mnist_class_name(label)}): {count} samples")
    
    # Get a random sample
    idx = np.random.randint(0, len(train_images))
    print(f"\nRandom sample:")
    print(f"  Index: {idx}")
    print(f"  Label: {train_labels[idx]} ({get_fashion_mnist_class_name(train_labels[idx])})")
    print(f"  Image shape: {train_images[idx].shape}")
    print(f"  Image stats: min={train_images[idx].min():.2f}, max={train_images[idx].max():.2f}, mean={train_images[idx].mean():.2f}")


# ============================================================================
# VITON-HD EXAMPLES
# ============================================================================

def viton_hd_dataloader():
    """Example using PyTorch DataLoader (recommended for large datasets)."""
    if not TORCHVISION_AVAILABLE:
        print("\n" + "=" * 60)
        print("VITON-HD: PYTORCH DATALOADER APPROACH (Recommended)")
        print("=" * 60)
        print("\n⚠ torchvision is not installed. Install it with: pip install torchvision")
        return
    
    print("\n" + "=" * 60)
    print("VITON-HD: PYTORCH DATALOADER APPROACH (Recommended)")
    print("=" * 60)
    
    # Create dataset instance
    dataset = VITONHD(
        data_dir="./datasets/viton_hd",  # Update with your path
        download=False
    )
    
    print(f"\nDataset: {dataset}")
    print(f"Info: {dataset.get_info()}")
    
    # Define transforms
    transform = transforms.Compose([
        transforms.Resize((512, 384)),  # Resize for faster processing
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
    ])
    
    # Get DataLoader for training
    train_loader = dataset.get_dataloader(
        split='train',
        batch_size=4,
        shuffle=True,
        num_workers=2,
        transform=transform,
        return_numpy=False  # Return PyTorch tensors
    )
    
    print(f"\nTrain DataLoader created:")
    print(f"  Batch size: {train_loader.batch_size}")
    print(f"  Number of batches: {len(train_loader)}")
    
    # Iterate through batches (lazy loading - images loaded on-demand)
    print(f"\nIterating through first 2 batches:")
    for batch_idx, batch in enumerate(train_loader):
        if batch_idx >= 2:
            break
        
        person_imgs = batch['person']
        clothing_imgs = batch['clothing']
        
        print(f"\n  Batch {batch_idx + 1}:")
        print(f"    Person images shape: {person_imgs.shape}")
        print(f"    Clothing images shape: {clothing_imgs.shape}")
        print(f"    Person paths: {batch['person_path'][:2]}")  # Show first 2 paths


def viton_hd_single_sample():
    """Example loading a single sample."""
    print("\n" + "=" * 60)
    print("VITON-HD: SINGLE SAMPLE APPROACH")
    print("=" * 60)
    
    dataset = VITONHD(
        data_dir="./datasets/viton_hd",  # Update with your path
        download=False
    )
    
    # Get a single sample
    sample = dataset.get_sample(
        index=0,
        split='train',
        return_numpy=True
    )
    
    print(f"\nSample 0:")
    print(f"  Person image shape: {sample['person'].shape}")
    print(f"  Clothing image shape: {sample['clothing'].shape}")
    print(f"  Person path: {sample['person_path']}")
    print(f"  Clothing path: {sample['clothing_path']}")
    print(f"  Index: {sample['index']}")


def viton_hd_load_to_memory():
    """Example loading samples into memory (use with caution for large datasets)."""
    print("\n" + "=" * 60)
    print("VITON-HD: LOAD TO MEMORY APPROACH (Use with caution)")
    print("=" * 60)
    
    dataset = VITONHD(
        data_dir="./datasets/viton_hd",  # Update with your path
        download=False
    )
    
    # Load only first 10 samples (to avoid memory issues)
    (person_imgs, clothing_imgs), _ = dataset.load(
        split='train',
        max_samples=10,  # Limit to 10 samples
        normalize=True
    )
    
    print(f"\nLoaded samples:")
    print(f"  Person images shape: {person_imgs.shape}")
    print(f"  Clothing images shape: {clothing_imgs.shape}")
    print(f"  Data type: {person_imgs.dtype}")
    print(f"  Value range: [{person_imgs.min():.2f}, {person_imgs.max():.2f}]")


def viton_hd_custom_transform():
    """Example with custom transforms."""
    if not TORCHVISION_AVAILABLE:
        print("\n" + "=" * 60)
        print("VITON-HD: CUSTOM TRANSFORMS APPROACH")
        print("=" * 60)
        print("\n⚠ torchvision is not installed. Install it with: pip install torchvision")
        return
    
    print("\n" + "=" * 60)
    print("VITON-HD: CUSTOM TRANSFORMS APPROACH")
    print("=" * 60)
    
    dataset = VITONHD(
        data_dir="./datasets/viton_hd",  # Update with your path
        download=False
    )
    
    # Custom transform pipeline
    custom_transform = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.ColorJitter(brightness=0.2, contrast=0.2),
        transforms.ToTensor(),
    ])
    
    train_loader = dataset.get_dataloader(
        split='train',
        batch_size=2,
        shuffle=True,
        transform=custom_transform
    )
    
    print(f"\nCustom transform DataLoader created")
    print(f"  Applied transforms: Resize, RandomHorizontalFlip, ColorJitter, ToTensor")
    
    # Get one batch
    batch = next(iter(train_loader))
    print(f"\n  Batch shape: {batch['person'].shape}")


# ============================================================================
# MAIN FUNCTION
# ============================================================================

def main():
    """Run all examples."""
    print("=" * 60)
    print("DATASET USAGE EXAMPLES")
    print("=" * 60)
    print("\nThis script demonstrates usage of both Fashion-MNIST and VITON-HD datasets.")
    print("\n" + "-" * 60)
    print("FASHION-MNIST")
    print("-" * 60)
    print("Small dataset (60MB) - loads entirely into memory")
    print("Use cases: Classification, quick prototyping")
    
    print("\n" + "-" * 60)
    print("VITON-HD")
    print("-" * 60)
    print("Large dataset (4.6GB) - uses lazy loading via PyTorch DataLoader")
    print("Use cases: Virtual try-on, high-resolution image generation")
    print("\nNote: Update 'data_dir' path for VITON-HD to point to your dataset")
    print("VITON-HD dataset structure should be:")
    print("  data_dir/")
    print("    person/")
    print("    clothing/")
    print("    train_pairs.txt")
    print("    test_pairs.txt")
    
    print("\n" + "=" * 60)
    print("FASHION-MNIST EXAMPLES")
    print("=" * 60)
    
    # Uncomment the Fashion-MNIST examples you want to run:
    # fashion_mnist_class_based()
    # fashion_mnist_function_based()
    
    print("\n" + "=" * 60)
    print("VITON-HD EXAMPLES")
    print("=" * 60)
    
    # Uncomment the VITON-HD examples you want to run:
    # viton_hd_dataloader()
    # viton_hd_single_sample()
    # viton_hd_load_to_memory()
    # viton_hd_custom_transform()
    
    print("\n" + "=" * 60)
    print("Examples ready! Uncomment the functions you want to run.")
    print("=" * 60)


if __name__ == '__main__':
    main()
