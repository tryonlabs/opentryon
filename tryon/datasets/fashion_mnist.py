"""
Fashion-MNIST Dataset Loader

A class-based adapter for downloading and loading the Fashion-MNIST dataset using NumPy.

Fashion-MNIST is a dataset of Zalando's article images consisting of:
- 60,000 training examples
- 10,000 test examples
- 10 classes (T-shirt/top, Trouser, Pullover, Dress, Coat, Sandal, Shirt, Sneaker, Bag, Ankle boot)
- 28x28 grayscale images

Reference: https://github.com/zalandoresearch/fashion-mnist
"""

import gzip
import struct
import numpy as np
from pathlib import Path
from typing import Tuple, Optional
import urllib.request
from urllib.error import URLError

from .base import Dataset


# Fashion-MNIST class names
CLASS_NAMES = [
    'T-shirt/top',
    'Trouser',
    'Pullover',
    'Dress',
    'Coat',
    'Sandal',
    'Shirt',
    'Sneaker',
    'Bag',
    'Ankle boot'
]

# Dataset URLs
BASE_URL = 'http://fashion-mnist.s3-website.eu-central-1.amazonaws.com/'
FILES = {
    'train_images': 'train-images-idx3-ubyte.gz',
    'train_labels': 'train-labels-idx1-ubyte.gz',
    'test_images': 't10k-images-idx3-ubyte.gz',
    'test_labels': 't10k-labels-idx1-ubyte.gz',
}


class FashionMNIST(Dataset):
    """
    Fashion-MNIST Dataset Adapter
    
    A class-based interface for loading the Fashion-MNIST dataset.
    
    Example:
        >>> from tryon.datasets import FashionMNIST
        >>> dataset = FashionMNIST(download=True)
        >>> (train_images, train_labels), (test_images, test_labels) = dataset.load(normalize=True)
        >>> print(f"Training set: {train_images.shape}")
        >>> print(f"Class: {dataset.get_class_name(train_labels[0])}")
    """
    
    def __init__(
        self,
        data_dir: Optional[str] = None,
        download: bool = True
    ):
        """
        Initialize Fashion-MNIST dataset.
        
        Args:
            data_dir: Directory to store the dataset. If None, uses ~/.opentryon/datasets/fashion_mnist
            download: If True, download the dataset if it doesn't exist
        """
        super().__init__(data_dir=data_dir, download=download)
        self._normalize = False
        self._flatten = False
    
    def _get_default_data_dir(self) -> Path:
        """Get the default data directory for Fashion-MNIST."""
        data_dir = Path.home() / '.opentryon' / 'datasets' / 'fashion_mnist'
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir
    
    def _download_file(self, url: str, filepath: Path) -> None:
        """
        Download a file from URL to filepath.
        
        Args:
            url: URL to download from
            filepath: Path to save the file
        """
        print(f"Downloading {filepath.name}...")
        try:
            urllib.request.urlretrieve(url, filepath)
            print(f"✓ Downloaded {filepath.name}")
        except URLError as e:
            raise RuntimeError(f"Failed to download {url}: {e}")
    
    def _ensure_downloaded(self) -> None:
        """Ensure all Fashion-MNIST files are downloaded."""
        for file_key, filename in FILES.items():
            filepath = self.data_dir / filename
            if not filepath.exists():
                url = BASE_URL + filename
                self._download_file(url, filepath)
    
    def _load_idx_file(self, filepath: Path) -> np.ndarray:
        """
        Load an IDX file format (used by MNIST/Fashion-MNIST).
        
        Args:
            filepath: Path to the .gz file
            
        Returns:
            NumPy array containing the data
        """
        with gzip.open(filepath, 'rb') as f:
            # Read magic number
            magic = struct.unpack('>I', f.read(4))[0]
            
            if magic == 2051:  # Image file magic number
                # Read dimensions
                num_images = struct.unpack('>I', f.read(4))[0]
                rows = struct.unpack('>I', f.read(4))[0]
                cols = struct.unpack('>I', f.read(4))[0]
                
                # Read image data
                buffer = f.read(num_images * rows * cols)
                data = np.frombuffer(buffer, dtype=np.uint8)
                data = data.reshape(num_images, rows, cols)
                
            elif magic == 2049:  # Label file magic number
                # Read number of labels
                num_labels = struct.unpack('>I', f.read(4))[0]
                
                # Read label data
                buffer = f.read(num_labels)
                data = np.frombuffer(buffer, dtype=np.uint8)
                
            else:
                raise ValueError(f"Unknown magic number: {magic}")
        
        return data
    
    def load(
        self,
        normalize: bool = False,
        flatten: bool = False
    ) -> Tuple[Tuple[np.ndarray, np.ndarray], Tuple[np.ndarray, np.ndarray]]:
        """
        Load Fashion-MNIST dataset.
        
        Args:
            normalize: If True, normalize pixel values to [0, 1] range
            flatten: If True, flatten images to 1D arrays (784,) instead of (28, 28)
            
        Returns:
            Tuple of (train_data, test_data) where each is (images, labels)
            - train_data: (train_images, train_labels)
            - test_data: (test_images, test_labels)
            - images: numpy array of shape (n_samples, 28, 28) or (n_samples, 784) if flatten=True
            - labels: numpy array of shape (n_samples,) with values 0-9
        """
        # Check if files exist
        train_images_path = self.data_dir / FILES['train_images']
        train_labels_path = self.data_dir / FILES['train_labels']
        test_images_path = self.data_dir / FILES['test_images']
        test_labels_path = self.data_dir / FILES['test_labels']
        
        if not all([
            train_images_path.exists(),
            train_labels_path.exists(),
            test_images_path.exists(),
            test_labels_path.exists()
        ]):
            raise FileNotFoundError(
                f"Dataset files not found in {self.data_dir}. "
                f"Set download=True to download them automatically."
            )
        
        # Load training data
        train_images = self._load_idx_file(train_images_path)
        train_labels = self._load_idx_file(train_labels_path)
        
        # Load test data
        test_images = self._load_idx_file(test_images_path)
        test_labels = self._load_idx_file(test_labels_path)
        
        # Normalize if requested
        if normalize:
            train_images = train_images.astype(np.float32) / 255.0
            test_images = test_images.astype(np.float32) / 255.0
        
        # Flatten if requested
        if flatten:
            train_images = train_images.reshape(train_images.shape[0], -1)
            test_images = test_images.reshape(test_images.shape[0], -1)
        
        # Cache the loaded data
        self._train_data = (train_images, train_labels)
        self._test_data = (test_images, test_labels)
        self._normalize = normalize
        self._flatten = flatten
        self._loaded = True
        
        return self._train_data, self._test_data
    
    def get_class_names(self) -> list:
        """Get all Fashion-MNIST class names."""
        return CLASS_NAMES.copy()
    
    def get_info(self) -> dict:
        """Get Fashion-MNIST dataset information."""
        info = super().get_info()
        info.update({
            'num_classes': len(CLASS_NAMES),
            'class_names': CLASS_NAMES,
            'image_shape': (28, 28),
            'train_size': 60000,
            'test_size': 10000,
        })
        if self._loaded:
            train_images, train_labels = self._train_data
            test_images, test_labels = self._test_data
            info.update({
                'train_images_shape': train_images.shape,
                'train_labels_shape': train_labels.shape,
                'test_images_shape': test_images.shape,
                'test_labels_shape': test_labels.shape,
                'normalized': self._normalize,
                'flattened': self._flatten,
            })
        return info


# Convenience functions for backward compatibility and simple usage
def load_fashion_mnist(
    data_dir: Optional[str] = None,
    download: bool = True,
    normalize: bool = False,
    flatten: bool = False
) -> Tuple[Tuple[np.ndarray, np.ndarray], Tuple[np.ndarray, np.ndarray]]:
    """
    Load Fashion-MNIST dataset (convenience function).
    
    This is a convenience function that creates a FashionMNIST instance and loads the data.
    For more control, use the FashionMNIST class directly.
    
    Args:
        data_dir: Directory to store the dataset. If None, uses ~/.opentryon/datasets/fashion_mnist
        download: If True, download the dataset if it doesn't exist
        normalize: If True, normalize pixel values to [0, 1] range
        flatten: If True, flatten images to 1D arrays (784,) instead of (28, 28)
        
    Returns:
        Tuple of (train_data, test_data) where each is (images, labels)
        
    Example:
        >>> from tryon.datasets import load_fashion_mnist
        >>> (train_images, train_labels), (test_images, test_labels) = load_fashion_mnist()
    """
    dataset = FashionMNIST(data_dir=data_dir, download=download)
    return dataset.load(normalize=normalize, flatten=flatten)


def get_fashion_mnist_class_name(label: int) -> str:
    """
    Get the Fashion-MNIST class name for a given label (convenience function).
    
    Args:
        label: Integer label (0-9)
        
    Returns:
        Class name string
        
    Example:
        >>> from tryon.datasets import get_fashion_mnist_class_name
        >>> print(get_fashion_mnist_class_name(0))  # 'T-shirt/top'
    """
    if not 0 <= label < len(CLASS_NAMES):
        raise ValueError(f"Label must be between 0 and {len(CLASS_NAMES) - 1}, got {label}")
    return CLASS_NAMES[label]


def get_fashion_mnist_class_names() -> list:
    """
    Get all Fashion-MNIST class names (convenience function).
    
    Returns:
        List of class name strings
        
    Example:
        >>> from tryon.datasets import get_fashion_mnist_class_names
        >>> print(get_fashion_mnist_class_names())
    """
    return CLASS_NAMES.copy()
