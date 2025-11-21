"""
Datasets module for OpenTryOn.

This module provides easy-to-use interfaces for downloading and loading
datasets commonly used in fashion and virtual try-on applications.

The module uses a class-based adapter pattern where each dataset is implemented
as a class that extends the base Dataset interface. This allows for consistent
APIs across different datasets while maintaining flexibility for dataset-specific
features.
"""

from .base import Dataset
from .fashion_mnist import (
    FashionMNIST,
    load_fashion_mnist,
    get_fashion_mnist_class_name,
    get_fashion_mnist_class_names,
    CLASS_NAMES,
)
from .viton_hd import (
    VITONHD,
    VITONHDPyTorchDataset,
    load_viton_hd,
)
from .subjects200k import (
    Subjects200K,
    Subjects200KPyTorchDataset,
    load_subjects200k,
)

__all__ = [
    # Base class
    'Dataset',
    # Fashion-MNIST
    'FashionMNIST',
    'load_fashion_mnist',
    'get_fashion_mnist_class_name',
    'get_fashion_mnist_class_names',
    'CLASS_NAMES',
    # VITON-HD
    'VITONHD',
    'VITONHDPyTorchDataset',
    'load_viton_hd',
    # Subjects200K
    'Subjects200K',
    'Subjects200KPyTorchDataset',
    'load_subjects200k',
]

