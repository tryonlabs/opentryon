"""Dataset tools for OpenTryOn MCP Server."""

from typing import Optional
from pathlib import Path

from tryon.datasets import FashionMNIST, VITONHD


def load_fashion_mnist(
    download: bool = True,
    normalize: bool = True,
    flatten: bool = False,
) -> dict:
    """
    Load Fashion-MNIST dataset.
    
    Args:
        download: Download if not present
        normalize: Normalize images
        flatten: Flatten images
        
    Returns:
        Dictionary with status and dataset information
    """
    try:
        dataset = FashionMNIST(download=download)
        (train_images, train_labels), (test_images, test_labels) = dataset.load(
            normalize=normalize,
            flatten=flatten
        )
        
        return {
            "success": True,
            "dataset": "fashion_mnist",
            "train_size": len(train_images),
            "test_size": len(test_images),
            "num_classes": 10,
            "image_shape": train_images.shape[1:],
            "message": f"Loaded Fashion-MNIST: {len(train_images)} training, {len(test_images)} test images"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def load_viton_hd(
    data_dir: str,
    split: str = "train",
    batch_size: int = 8,
) -> dict:
    """
    Load VITON-HD dataset.
    
    Args:
        data_dir: Dataset directory
        split: "train" or "test"
        batch_size: Batch size for DataLoader
        
    Returns:
        Dictionary with status and dataset information
    """
    try:
        # Validate split
        if split not in ["train", "test"]:
            return {
                "success": False,
                "error": f"Invalid split: {split}. Must be 'train' or 'test'"
            }
        
        # Validate data directory
        data_path = Path(data_dir)
        if not data_path.exists():
            return {
                "success": False,
                "error": f"Data directory does not exist: {data_dir}"
            }
        
        dataset = VITONHD(data_dir=str(data_path), download=False)
        dataloader = dataset.get_dataloader(
            split=split,
            batch_size=batch_size,
            shuffle=(split == "train")
        )
        
        return {
            "success": True,
            "dataset": "viton_hd",
            "split": split,
            "batch_size": batch_size,
            "num_batches": len(dataloader),
            "message": f"Loaded VITON-HD {split} split with batch size {batch_size}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

