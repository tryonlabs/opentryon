"""
VITON-HD Dataset Loader

A class-based adapter for the VITON-HD dataset using PyTorch DataLoader for efficient
lazy loading of high-resolution images.

VITON-HD is a high-resolution virtual try-on dataset consisting of:
- 11,647 training pairs
- 2,032 test pairs
- 1024x768 resolution images
- Person images and clothing images

This module provides two main classes:
1. `VITONHDPyTorchDataset`: A PyTorch Dataset for lazy loading individual samples
2. `VITONHD`: A high-level adapter that provides DataLoader integration and convenience methods

Reference: https://github.com/shadow2496/VITON-HD
Paper: https://arxiv.org/abs/2103.16874

Example Usage:
    Basic usage with DataLoader:
        >>> from tryon.datasets import VITONHD
        >>> from torchvision import transforms
        >>> 
        >>> dataset = VITONHD(data_dir="./viton_hd", download=False)
        >>> transform = transforms.Compose([
        ...     transforms.Resize((512, 384)),
        ...     transforms.ToTensor(),
        ...     transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
        ... ])
        >>> 
        >>> train_loader = dataset.get_dataloader(
        ...     split='train',
        ...     batch_size=8,
        ...     transform=transform
        ... )
        >>> 
        >>> for batch in train_loader:
        ...     person_imgs = batch['person']  # Shape: [batch_size, 3, H, W]
        ...     clothing_imgs = batch['clothing']  # Shape: [batch_size, 3, H, W]
        ...     # Process batch...

    Single sample access:
        >>> sample = dataset.get_sample(0, split='train', return_numpy=True)
        >>> person_img = sample['person']  # numpy array
        >>> clothing_img = sample['clothing']  # numpy array

    Loading into memory (use with caution):
        >>> person_imgs, clothing_imgs = load_viton_hd(
        ...     data_dir="./viton_hd",
        ...     split='train',
        ...     max_samples=100,  # Limit to avoid memory issues
        ...     normalize=True
        ... )
"""

from pathlib import Path
from typing import Tuple, Optional, Dict, Any, List, Callable, Union
import numpy as np
from PIL import Image
import torch
from torch.utils.data import Dataset as PyTorchDataset, DataLoader

from .base import Dataset


def _collate_dict_batch(batch: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Custom collate function for batching dictionary samples.
    
    Handles both tensor and numpy array batching. For numpy arrays,
    converts them to tensors before batching.
    
    Args:
        batch: List of dictionary samples from the dataset
        
    Returns:
        Batched dictionary with stacked tensors/arrays
    """
    # Separate different types of data
    person_imgs = []
    clothing_imgs = []
    person_paths = []
    clothing_paths = []
    indices = []
    
    for sample in batch:
        person_imgs.append(sample['person'])
        clothing_imgs.append(sample['clothing'])
        person_paths.append(sample['person_path'])
        clothing_paths.append(sample['clothing_path'])
        indices.append(sample['index'])
    
    # Batch images
    def _batch_images(imgs: List[Any]) -> torch.Tensor:
        """Convert list of images to batched tensor."""
        # If first image is a tensor, stack directly
        if isinstance(imgs[0], torch.Tensor):
            return torch.stack(imgs)
        # If numpy array, convert to tensor then stack
        elif isinstance(imgs[0], np.ndarray):
            return torch.stack([torch.from_numpy(img) for img in imgs])
        # If PIL Image, convert to tensor then stack
        elif isinstance(imgs[0], Image.Image):
            return torch.stack([torch.from_numpy(np.array(img)) for img in imgs])
        else:
            raise TypeError(f"Unsupported image type: {type(imgs[0])}")
    
    return {
        'person': _batch_images(person_imgs),
        'clothing': _batch_images(clothing_imgs),
        'person_path': person_paths,
        'clothing_path': clothing_paths,
        'index': torch.tensor(indices)
    }


class VITONHDPyTorchDataset(PyTorchDataset):
    """
    PyTorch Dataset class for VITON-HD.
    
    This class handles lazy loading of images from disk, making it memory-efficient
    for large datasets. Images are loaded on-demand when accessed via indexing.
    
    Attributes:
        data_dir: Root directory of the dataset
        pairs_file: Path to pairs file
        person_dir: Directory containing person images
        clothing_dir: Directory containing clothing images
        transform: Optional transform to apply to images
        return_numpy: If True, return numpy arrays instead of PIL Images
        pairs: List of (person_image_name, clothing_image_name) tuples
    
    Example:
        >>> dataset = VITONHDPyTorchDataset(
        ...     data_dir=Path("./viton_hd"),
        ...     pairs_file="train_pairs.txt"
        ... )
        >>> sample = dataset[0]
        >>> person_img = sample['person']  # PIL Image
        >>> clothing_img = sample['clothing']  # PIL Image
    """
    
    def __init__(
        self,
        data_dir: Path,
        pairs_file: str,
        person_dir: str = "person",
        clothing_dir: str = "clothing",
        transform: Optional[Callable] = None,
        return_numpy: bool = False
    ):
        """
        Initialize VITON-HD PyTorch Dataset.
        
        Args:
            data_dir: Root directory of the dataset
            pairs_file: Path to pairs file (e.g., 'test_pairs.txt' or 'train_pairs.txt')
            person_dir: Directory name containing person images
            clothing_dir: Directory name containing clothing images
            transform: Optional transform to apply to images (should accept PIL Images)
            return_numpy: If True, return numpy arrays instead of PIL Images.
                        Note: Transforms are applied before conversion to numpy.
        
        Raises:
            FileNotFoundError: If required directories or files are missing
        """
        self.data_dir = Path(data_dir)
        self.pairs_file = self.data_dir / pairs_file
        self.person_dir = self.data_dir / person_dir
        self.clothing_dir = self.data_dir / clothing_dir
        self.transform = transform
        self.return_numpy = return_numpy
        
        # Verify directories exist before loading pairs
        if not self.person_dir.exists():
            raise FileNotFoundError(f"Person directory not found: {self.person_dir}")
        if not self.clothing_dir.exists():
            raise FileNotFoundError(f"Clothing directory not found: {self.clothing_dir}")
        
        # Load pairs
        self.pairs = self._load_pairs()
        
        # Validate that at least some image files exist
        if len(self.pairs) > 0:
            first_person_path = self.person_dir / self.pairs[0][0]
            first_clothing_path = self.clothing_dir / self.pairs[0][1]
            if not first_person_path.exists():
                raise FileNotFoundError(
                    f"Sample person image not found: {first_person_path}\n"
                    f"This may indicate the dataset is incomplete or paths are incorrect."
                )
            if not first_clothing_path.exists():
                raise FileNotFoundError(
                    f"Sample clothing image not found: {first_clothing_path}\n"
                    f"This may indicate the dataset is incomplete or paths are incorrect."
                )
    
    def _load_pairs(self) -> List[Tuple[str, str]]:
        """
        Load image pairs from pairs file.
        
        Expected format: Each line contains "person_image.jpg clothing_image.jpg"
        Lines starting with '#' are treated as comments and ignored.
        Empty lines are skipped.
        
        Returns:
            List of (person_image_name, clothing_image_name) tuples
        
        Raises:
            FileNotFoundError: If pairs file doesn't exist
        """
        if not self.pairs_file.exists():
            raise FileNotFoundError(
                f"Pairs file not found: {self.pairs_file}\n"
                f"Please ensure the dataset is properly downloaded and extracted."
            )
        
        pairs = []
        with open(self.pairs_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, start=1):
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                parts = line.split()
                if len(parts) >= 2:
                    person_img = parts[0]
                    clothing_img = parts[1]
                    pairs.append((person_img, clothing_img))
                else:
                    # Warn about malformed lines but don't fail
                    import warnings
                    warnings.warn(
                        f"Skipping malformed line {line_num} in {self.pairs_file}: '{line}'"
                    )
        
        if not pairs:
            raise ValueError(
                f"No valid pairs found in {self.pairs_file}. "
                f"Please check the file format."
            )
        
        return pairs
    
    def __len__(self) -> int:
        """Return the number of pairs in the dataset."""
        return len(self.pairs)
    
    def __getitem__(self, idx: int) -> Dict[str, Any]:
        """
        Get a single pair from the dataset.
        
        Images are loaded from disk on-demand. If transforms are provided,
        they are applied to PIL Images before conversion to numpy (if requested).
        
        Args:
            idx: Index of the pair (0-indexed)
            
        Returns:
            Dictionary containing:
            - 'person': Person image (PIL Image, numpy array, or tensor depending on transform/return_numpy)
            - 'clothing': Clothing image (same type as 'person')
            - 'person_path': Path to person image (string)
            - 'clothing_path': Path to clothing image (string)
            - 'index': Original index (int)
        
        Raises:
            IndexError: If idx is out of range
            FileNotFoundError: If image files are missing
            IOError: If images cannot be loaded
        """
        if idx < 0 or idx >= len(self.pairs):
            raise IndexError(
                f"Index {idx} out of range for dataset of size {len(self.pairs)}"
            )
        
        person_img_name, clothing_img_name = self.pairs[idx]
        
        person_path = self.person_dir / person_img_name
        clothing_path = self.clothing_dir / clothing_img_name
        
        # Validate files exist
        if not person_path.exists():
            raise FileNotFoundError(f"Person image not found: {person_path}")
        if not clothing_path.exists():
            raise FileNotFoundError(f"Clothing image not found: {clothing_path}")
        
        try:
            # Load images as PIL Images (most flexible format)
            person_img = Image.open(person_path).convert('RGB')
            clothing_img = Image.open(clothing_path).convert('RGB')
        except Exception as e:
            raise IOError(
                f"Failed to load images at index {idx}:\n"
                f"  Person: {person_path}\n"
                f"  Clothing: {clothing_path}\n"
                f"  Error: {str(e)}"
            ) from e
        
        # Apply transforms if provided (transforms expect PIL Images)
        if self.transform is not None:
            try:
                person_img = self.transform(person_img)
                clothing_img = self.transform(clothing_img)
            except Exception as e:
                raise RuntimeError(
                    f"Transform failed for images at index {idx}:\n"
                    f"  Person: {person_path}\n"
                    f"  Clothing: {clothing_path}\n"
                    f"  Error: {str(e)}"
                ) from e
        
        # Convert to numpy if requested (after transforms)
        if self.return_numpy:
            if isinstance(person_img, torch.Tensor):
                person_img = person_img.numpy()
            elif isinstance(person_img, Image.Image):
                person_img = np.array(person_img)
            # If already numpy, keep as is
            
            if isinstance(clothing_img, torch.Tensor):
                clothing_img = clothing_img.numpy()
            elif isinstance(clothing_img, Image.Image):
                clothing_img = np.array(clothing_img)
            # If already numpy, keep as is
        
        return {
            'person': person_img,
            'clothing': clothing_img,
            'person_path': str(person_path),
            'clothing_path': str(clothing_path),
            'index': idx
        }


class VITONHD(Dataset):
    """
    VITON-HD Dataset Adapter
    
    A high-level interface for loading the VITON-HD dataset with lazy loading
    support via PyTorch DataLoader. This class provides convenient methods for
    accessing the dataset without directly managing PyTorch Dataset instances.
    
    The dataset uses lazy loading by default - images are loaded from disk only
    when accessed, making it memory-efficient for large datasets.
    
    Attributes:
        data_dir: Directory containing the dataset
        train_pairs_file: Name of training pairs file
        test_pairs_file: Name of test pairs file
        person_dir: Directory name containing person images
        clothing_dir: Directory name containing clothing images
    
    Example:
        Basic usage:
            >>> from tryon.datasets import VITONHD
            >>> dataset = VITONHD(data_dir="./viton_hd", download=False)
            >>> 
            >>> # Get dataset info
            >>> info = dataset.get_info()
            >>> print(f"Train size: {info['train_size']}")
            >>> print(f"Test size: {info['test_size']}")
        
        Using DataLoader (recommended for training):
            >>> from torchvision import transforms
            >>> 
            >>> transform = transforms.Compose([
            ...     transforms.Resize((512, 384)),
            ...     transforms.ToTensor(),
            ...     transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
            ... ])
            >>> 
            >>> train_loader = dataset.get_dataloader(
            ...     split='train',
            ...     batch_size=8,
            ...     shuffle=True,
            ...     transform=transform
            ... )
            >>> 
            >>> for batch in train_loader:
            ...     person_batch = batch['person']  # [batch_size, 3, H, W]
            ...     clothing_batch = batch['clothing']  # [batch_size, 3, H, W]
            ...     # Train model...
        
        Single sample access:
            >>> sample = dataset.get_sample(0, split='train')
            >>> person_img = sample['person']  # PIL Image
            >>> clothing_img = sample['clothing']  # PIL Image
        
        Loading into memory (use with caution):
            >>> (person_imgs, clothing_imgs), _ = dataset.load(
            ...     split='train',
            ...     max_samples=100,  # Limit to avoid memory issues
            ...     normalize=True
            ... )
    """
    
    def __init__(
        self,
        data_dir: Optional[Union[str, Path]] = None,
        download: bool = False,
        train_pairs_file: str = "train_pairs.txt",
        test_pairs_file: str = "test_pairs.txt",
        person_dir: str = "person",
        clothing_dir: str = "clothing"
    ):
        """
        Initialize VITON-HD dataset.
        
        Args:
            data_dir: Directory containing the dataset. If None, uses default location
                     (~/.opentryon/datasets/viton_hd)
            download: If True, attempt to download the dataset (not implemented yet).
                     Currently, users must manually download the dataset.
            train_pairs_file: Name of training pairs file (default: "train_pairs.txt")
            test_pairs_file: Name of test pairs file (default: "test_pairs.txt")
            person_dir: Directory name containing person images (default: "person")
            clothing_dir: Directory name containing clothing images (default: "clothing")
        
        Raises:
            FileNotFoundError: If dataset structure is invalid or missing
        """
        super().__init__(data_dir=data_dir, download=download)
        self.train_pairs_file = train_pairs_file
        self.test_pairs_file = test_pairs_file
        self.person_dir = person_dir
        self.clothing_dir = clothing_dir
        
        # Initialize PyTorch datasets (lazy, won't load until accessed)
        self._train_dataset: Optional[VITONHDPyTorchDataset] = None
        self._test_dataset: Optional[VITONHDPyTorchDataset] = None
    
    def _get_default_data_dir(self) -> Path:
        """
        Get the default data directory for VITON-HD.
        
        Returns:
            Path to default data directory (~/.opentryon/datasets/viton_hd)
        """
        data_dir = Path.home() / '.opentryon' / 'datasets' / 'viton_hd'
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir
    
    def _ensure_downloaded(self) -> None:
        """
        Ensure the dataset is downloaded.
        
        Note: VITON-HD dataset download is not automated due to its size (4.6GB).
        Users should manually download from the official repository.
        
        Raises:
            FileNotFoundError: If dataset structure is invalid or missing
        """
        # Check if dataset structure exists
        required_dirs = [self.person_dir, self.clothing_dir]
        required_files = [self.train_pairs_file, self.test_pairs_file]
        
        missing = []
        for dir_name in required_dirs:
            if not (self.data_dir / dir_name).exists():
                missing.append(f"Directory: {dir_name}")
        
        for file_name in required_files:
            if not (self.data_dir / file_name).exists():
                missing.append(f"File: {file_name}")
        
        if missing:
            raise FileNotFoundError(
                f"VITON-HD dataset not found in {self.data_dir}.\n"
                f"Missing: {', '.join(missing)}\n\n"
                f"Please download the dataset from:\n"
                f"  https://github.com/shadow2496/VITON-HD\n\n"
                f"Expected structure:\n"
                f"  {self.data_dir}/\n"
                f"    {self.person_dir}/\n"
                f"    {self.clothing_dir}/\n"
                f"    {self.train_pairs_file}\n"
                f"    {self.test_pairs_file}\n\n"
                f"After downloading, extract the dataset to match this structure."
            )
    
    def _get_pytorch_dataset(
        self,
        split: str = 'train',
        transform: Optional[Callable] = None,
        return_numpy: bool = False
    ) -> VITONHDPyTorchDataset:
        """
        Get or create PyTorch dataset for the specified split.
        
        Creates a new dataset instance if transform or return_numpy settings differ
        from the cached instance. This ensures that different DataLoaders can use
        different transforms without interfering with each other.
        
        Args:
            split: 'train' or 'test'
            transform: Optional transform to apply to images
            return_numpy: If True, return numpy arrays instead of PIL Images
        
        Returns:
            VITONHDPyTorchDataset instance configured with the specified settings
        
        Raises:
            ValueError: If split is not 'train' or 'test'
        """
        if split not in ('train', 'test'):
            raise ValueError(f"Split must be 'train' or 'test', got {split}")
        
        pairs_file = self.train_pairs_file if split == 'train' else self.test_pairs_file
        
        # Create new dataset instance with specified settings
        # This allows multiple DataLoaders with different transforms
        return VITONHDPyTorchDataset(
            data_dir=self.data_dir,
            pairs_file=pairs_file,
            person_dir=self.person_dir,
            clothing_dir=self.clothing_dir,
            transform=transform,
            return_numpy=return_numpy
        )
    
    def get_dataloader(
        self,
        split: str = 'train',
        batch_size: int = 8,
        shuffle: bool = True,
        num_workers: int = 4,
        pin_memory: bool = True,
        transform: Optional[Callable] = None,
        return_numpy: bool = False,
        collate_fn: Optional[Callable] = None
    ) -> DataLoader:
        """
        Get a PyTorch DataLoader for the specified split.
        
        This is the recommended way to access the dataset for training, as it
        provides efficient batching, shuffling, and multi-process data loading.
        
        Args:
            split: 'train' or 'test'
            batch_size: Batch size for the DataLoader (default: 8)
            shuffle: Whether to shuffle the data (default: True for training)
            num_workers: Number of worker processes for data loading (default: 4).
                        Set to 0 for single-process loading.
            pin_memory: Whether to pin memory for faster GPU transfer (default: True)
            transform: Optional transform to apply to images. Should accept PIL Images
                      and return tensors or numpy arrays. Common transforms from
                      torchvision.transforms work well here.
            return_numpy: If True, return numpy arrays instead of PIL Images.
                        Note: If transform outputs tensors, they will be converted
                        to numpy. For best performance with DataLoader, use transforms
                        that output tensors and set return_numpy=False.
            collate_fn: Custom collate function for batching. If None, uses default
                       dictionary collate function that handles both tensors and numpy arrays.
        
        Returns:
            PyTorch DataLoader instance
        
        Example:
            >>> from torchvision import transforms
            >>> 
            >>> transform = transforms.Compose([
            ...     transforms.Resize((512, 384)),
            ...     transforms.ToTensor(),
            ...     transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
            ... ])
            >>> 
            >>> train_loader = dataset.get_dataloader(
            ...     split='train',
            ...     batch_size=16,
            ...     shuffle=True,
            ...     num_workers=4,
            ...     transform=transform
            ... )
            >>> 
            >>> for batch in train_loader:
            ...     person_batch = batch['person']  # [16, 3, 384, 512]
            ...     clothing_batch = batch['clothing']  # [16, 3, 384, 512]
        """
        dataset = self._get_pytorch_dataset(
            split=split,
            transform=transform,
            return_numpy=return_numpy
        )
        
        # Use custom collate function if provided, otherwise use default
        if collate_fn is None:
            collate_fn = _collate_dict_batch
        
        return DataLoader(
            dataset,
            batch_size=batch_size,
            shuffle=shuffle,
            num_workers=num_workers,
            pin_memory=pin_memory,
            collate_fn=collate_fn
        )
    
    def get_sample(
        self,
        index: int,
        split: str = 'train',
        return_numpy: bool = True
    ) -> Dict[str, Any]:
        """
        Get a single sample from the dataset.
        
        This method is useful for inspection, visualization, or single-sample inference.
        For training, use `get_dataloader()` instead.
        
        Args:
            index: Index of the sample (0-indexed)
            split: 'train' or 'test'
            return_numpy: If True, return numpy arrays instead of PIL Images
        
        Returns:
            Dictionary containing:
            - 'person': Person image (PIL Image or numpy array)
            - 'clothing': Clothing image (PIL Image or numpy array)
            - 'person_path': Path to person image (string)
            - 'clothing_path': Path to clothing image (string)
            - 'index': Original index (int)
        
        Raises:
            IndexError: If index is out of range
        
        Example:
            >>> sample = dataset.get_sample(0, split='train', return_numpy=True)
            >>> person_img = sample['person']  # numpy array
            >>> clothing_img = sample['clothing']  # numpy array
            >>> print(f"Person shape: {person_img.shape}")
            >>> print(f"Clothing shape: {clothing_img.shape}")
        """
        dataset = self._get_pytorch_dataset(split=split, return_numpy=return_numpy)
        
        if index < 0 or index >= len(dataset):
            raise IndexError(
                f"Index {index} out of range for {split} split (size: {len(dataset)})"
            )
        
        return dataset[index]
    
    def load(
        self,
        split: str = 'train',
        normalize: bool = False,
        flatten: bool = False,
        max_samples: Optional[int] = None,
        **kwargs
    ) -> Tuple[Tuple[np.ndarray, np.ndarray], Tuple[np.ndarray, np.ndarray]]:
        """
        Load dataset samples into memory.
        
        ⚠️ Warning: This method loads all images into memory. For large datasets
        like VITON-HD (4.6GB), this can cause memory issues. Use `get_dataloader()`
        instead for lazy loading.
        
        This method is provided for compatibility with the base Dataset interface
        and for cases where you need all data in memory (e.g., small subsets for
        quick prototyping).
        
        Args:
            split: 'train' or 'test'
            normalize: If True, normalize pixel values to [0, 1] range
            flatten: If True, flatten images to 1D arrays (not recommended for
                    high-resolution images)
            max_samples: Maximum number of samples to load (None for all).
                       Use this to limit memory usage.
            **kwargs: Additional arguments (ignored)
        
        Returns:
            Tuple of (train_data, test_data) where each is (person_images, clothing_images).
            Note: For compatibility with base interface, returns empty arrays for
            the split that wasn't requested.
        
        Example:
            >>> # Load only first 100 samples to avoid memory issues
            >>> (person_imgs, clothing_imgs), _ = dataset.load(
            ...     split='train',
            ...     max_samples=100,
            ...     normalize=True
            ... )
            >>> print(f"Loaded {len(person_imgs)} samples")
            >>> print(f"Person images shape: {person_imgs.shape}")
        """
        dataset = self._get_pytorch_dataset(split=split, return_numpy=True)
        
        person_images = []
        clothing_images = []
        
        num_samples = len(dataset) if max_samples is None else min(max_samples, len(dataset))
        
        for i in range(num_samples):
            sample = dataset[i]
            person_img = sample['person']
            clothing_img = sample['clothing']
            
            # Ensure numpy arrays
            if isinstance(person_img, Image.Image):
                person_img = np.array(person_img)
            elif isinstance(person_img, torch.Tensor):
                person_img = person_img.numpy()
            
            if isinstance(clothing_img, Image.Image):
                clothing_img = np.array(clothing_img)
            elif isinstance(clothing_img, torch.Tensor):
                clothing_img = clothing_img.numpy()
            
            if normalize:
                person_img = person_img.astype(np.float32) / 255.0
                clothing_img = clothing_img.astype(np.float32) / 255.0
            
            if flatten:
                person_img = person_img.reshape(-1)
                clothing_img = clothing_img.reshape(-1)
            
            person_images.append(person_img)
            clothing_images.append(clothing_img)
        
        person_images = np.array(person_images)
        clothing_images = np.array(clothing_images)
        
        self._loaded = True
        
        if split == 'train':
            return (person_images, clothing_images), (np.array([]), np.array([]))
        else:
            return (np.array([]), np.array([])), (person_images, clothing_images)
    
    def get_class_names(self) -> List[str]:
        """
        Get class names for VITON-HD.
        
        Note: VITON-HD doesn't have traditional classification classes, but we return
        descriptive labels for the dataset structure.
        
        Returns:
            List of class names: ['person', 'clothing']
        """
        return ['person', 'clothing']
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get VITON-HD dataset information.
        
        Returns comprehensive information about the dataset including sizes,
        image resolution, and directory structure.
        
        Returns:
            Dictionary containing:
            - 'name': Dataset class name
            - 'data_dir': Path to dataset directory
            - 'loaded': Whether data has been loaded into memory
            - 'train_size': Number of training pairs
            - 'test_size': Number of test pairs
            - 'image_resolution': Expected image resolution (string)
            - 'image_shape': Actual image shape from a sample (H, W)
            - 'person_dir': Directory name for person images
            - 'clothing_dir': Directory name for clothing images
        
        Example:
            >>> info = dataset.get_info()
            >>> print(f"Train size: {info['train_size']}")
            >>> print(f"Test size: {info['test_size']}")
            >>> print(f"Image shape: {info['image_shape']}")
        """
        info = super().get_info()
        
        # Try to get additional info, but don't fail if dataset isn't loaded yet
        try:
            train_dataset = self._get_pytorch_dataset('train')
            test_dataset = self._get_pytorch_dataset('test')
            
            info.update({
                'train_size': len(train_dataset),
                'test_size': len(test_dataset),
                'image_resolution': '1024x768',
                'person_dir': self.person_dir,
                'clothing_dir': self.clothing_dir,
            })
            
            # Get sample image shape if available
            if len(train_dataset) > 0:
                try:
                    sample = train_dataset[0]
                    if isinstance(sample['person'], Image.Image):
                        info['image_shape'] = sample['person'].size[::-1]  # (H, W)
                    elif isinstance(sample['person'], np.ndarray):
                        info['image_shape'] = sample['person'].shape[:2]
                    elif isinstance(sample['person'], torch.Tensor):
                        if sample['person'].dim() == 3:
                            info['image_shape'] = sample['person'].shape[1:]  # (H, W)
                        else:
                            info['image_shape'] = sample['person'].shape[-2:]
                except (FileNotFoundError, IOError, IndexError):
                    # If we can't load a sample, skip image_shape
                    pass
        except (FileNotFoundError, ValueError) as e:
            # If dataset structure is invalid, add error info
            info['error'] = str(e)
        
        return info


# Convenience functions
def load_viton_hd(
    data_dir: Optional[Union[str, Path]] = None,
    split: str = 'train',
    max_samples: Optional[int] = None,
    normalize: bool = False
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load VITON-HD dataset samples (convenience function).
    
    ⚠️ Warning: This function loads images into memory. For large datasets,
    use the `VITONHD` class with `get_dataloader()` for lazy loading.
    
    This is a convenience function for quick access to the dataset. For more
    control and better memory efficiency, use the `VITONHD` class directly.
    
    Args:
        data_dir: Directory containing the dataset. If None, uses default location
        split: 'train' or 'test'
        max_samples: Maximum number of samples to load (None for all).
                    Use this to limit memory usage.
        normalize: If True, normalize pixel values to [0, 1] range
    
    Returns:
        Tuple of (person_images, clothing_images) as numpy arrays.
        Shapes: (num_samples, H, W, 3) if not normalized, (num_samples, H, W, 3) if normalized
    
    Example:
        >>> # Load first 100 training samples
        >>> person_imgs, clothing_imgs = load_viton_hd(
        ...     data_dir="./viton_hd",
        ...     split='train',
        ...     max_samples=100,
        ...     normalize=True
        ... )
        >>> print(f"Person images shape: {person_imgs.shape}")
        >>> print(f"Clothing images shape: {clothing_imgs.shape}")
    """
    dataset = VITONHD(data_dir=data_dir, download=False)
    (person_imgs, clothing_imgs), _ = dataset.load(
        split=split,
        max_samples=max_samples,
        normalize=normalize
    )
    return person_imgs, clothing_imgs
