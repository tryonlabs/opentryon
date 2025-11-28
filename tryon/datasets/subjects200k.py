"""
Subjects200K Dataset Loader

A class-based adapter for the Subjects200K dataset using HuggingFace datasets library.

Subjects200K is a large-scale dataset containing 200,000 paired images, introduced as part
of the OminiControl project. Each image pair maintains subject consistency while presenting
variations in scene context.

The dataset consists of three collections:
- Collection 1: 512×512 resolution, 18,396 image pairs (8,200 high-quality)
- Collection 2: 512×512 resolution, 187,840 image pairs (111,767 high-quality)
- Collection 3: 1024×1024 resolution

Each image is a composite containing a pair of images with 16-pixel padding.

Reference: https://github.com/Yuanshi9815/Subjects200K
HuggingFace: https://huggingface.co/datasets/Yuanshi/Subjects200K

Example Usage:
    Basic usage:
        >>> from tryon.datasets import Subjects200K
        >>> dataset = Subjects200K()
        >>> # Access dataset via HuggingFace datasets
        >>> hf_dataset = dataset.get_hf_dataset()
        >>> sample = hf_dataset['train'][0]
        >>> image = sample['image']  # PIL Image
        >>> collection = sample['collection']
        >>> quality = sample['quality_assessment']
    
    Filter high-quality pairs from collection_2:
        >>> dataset = Subjects200K()
        >>> hf_dataset = dataset.get_hf_dataset()
        >>> filtered = dataset.filter_high_quality(
        ...     collection='collection_2',
        ...     min_quality_score=5
        ... )
        >>> print(f"High-quality pairs: {len(filtered)}")
    
    Get DataLoader for PyTorch:
        >>> from torchvision import transforms
        >>> dataset = Subjects200K()
        >>> transform = transforms.Compose([
        ...     transforms.Resize((512, 512)),
        ...     transforms.ToTensor(),
        ... ])
        >>> dataloader = dataset.get_dataloader(
        ...     split='train',
        ...     batch_size=8,
        ...     transform=transform,
        ...     collection='collection_2',
        ...     filter_high_quality=True
        ... )
        >>> for batch in dataloader:
        ...     images = batch['image']  # [batch_size, 3, H, W]
        ...     # Process batch...
"""

from pathlib import Path
from typing import Optional, Dict, Any, List, Callable, Union
import numpy as np
from PIL import Image
import torch
from torch.utils.data import Dataset as PyTorchDataset, DataLoader

from .base import Dataset

try:
    from datasets import load_dataset, Dataset as HFDataset
    HF_DATASETS_AVAILABLE = True
except ImportError:
    HF_DATASETS_AVAILABLE = False
    HFDataset = None


class Subjects200KPyTorchDataset(PyTorchDataset):
    """
    PyTorch Dataset wrapper for Subjects200K.
    
    This class provides a PyTorch-compatible interface for Subjects200K,
    allowing lazy loading of individual samples.
    
    Args:
        hf_dataset: HuggingFace dataset instance
        transform: Optional transform to apply to images
        collection: Optional collection filter ('collection_1', 'collection_2', 'collection_3')
        filter_high_quality: If True, filter samples with quality scores >= 5
    """
    
    def __init__(
        self,
        hf_dataset: Any,
        transform: Optional[Callable] = None,
        collection: Optional[str] = None,
        filter_high_quality: bool = False
    ):
        self.hf_dataset = hf_dataset
        self.transform = transform
        self.collection = collection
        self.filter_high_quality = filter_high_quality
        
        # Filter dataset if needed
        if collection or filter_high_quality:
            self.indices = self._filter_indices()
        else:
            self.indices = list(range(len(hf_dataset)))
    
    def _filter_indices(self) -> List[int]:
        """Filter indices based on collection and quality criteria."""
        indices = []
        for idx in range(len(self.hf_dataset)):
            sample = self.hf_dataset[idx]
            
            # Filter by collection
            if self.collection and sample.get('collection') != self.collection:
                continue
            
            # Filter by quality
            if self.filter_high_quality:
                quality = sample.get('quality_assessment')
                if not quality:
                    continue
                if not all(
                    quality.get(key, 0) >= 5
                    for key in ['compositeStructure', 'objectConsistency', 'imageQuality']
                ):
                    continue
            
            indices.append(idx)
        
        return indices
    
    def __len__(self) -> int:
        """Return the number of samples."""
        return len(self.indices)
    
    def __getitem__(self, idx: int) -> Dict[str, Any]:
        """Get a sample by index."""
        actual_idx = self.indices[idx]
        sample = self.hf_dataset[actual_idx]
        
        # Get image
        image = sample['image']
        if not isinstance(image, Image.Image):
            image = Image.fromarray(image) if isinstance(image, np.ndarray) else image
        
        # Apply transform if provided
        if self.transform:
            image = self.transform(image)
        
        # Build return dictionary
        result = {
            'image': image,
            'index': actual_idx,
        }
        
        # Add metadata if available
        if 'collection' in sample:
            result['collection'] = sample['collection']
        if 'quality_assessment' in sample:
            result['quality_assessment'] = sample['quality_assessment']
        if 'description' in sample:
            result['description'] = sample['description']
        
        return result


class Subjects200K(Dataset):
    """
    Subjects200K Dataset Adapter
    
    A class-based interface for loading the Subjects200K dataset from HuggingFace.
    
    This adapter provides access to 200,000 paired images across three collections,
    with support for quality filtering and PyTorch DataLoader integration.
    
    Example:
        >>> from tryon.datasets import Subjects200K
        >>> dataset = Subjects200K()
        >>> hf_dataset = dataset.get_hf_dataset()
        >>> print(f"Total samples: {len(hf_dataset['train'])}")
    """
    
    HF_DATASET_NAME = 'Yuanshi/Subjects200K'
    
    def __init__(
        self,
        data_dir: Optional[str] = None,
        download: bool = True,
        cache_dir: Optional[str] = None
    ):
        """
        Initialize Subjects200K dataset.
        
        Args:
            data_dir: Directory to store the dataset cache. If None, uses default location.
                     Note: This dataset is loaded from HuggingFace, so this is just for caching.
            download: If True, download the dataset if it doesn't exist (always True for HuggingFace)
            cache_dir: Optional cache directory for HuggingFace datasets.
                      If None, uses ~/.cache/huggingface/datasets
        """
        if not HF_DATASETS_AVAILABLE:
            raise ImportError(
                "HuggingFace datasets library is required for Subjects200K. "
                "Install it with: pip install datasets"
            )
        
        super().__init__(data_dir=data_dir, download=download)
        self.cache_dir = cache_dir
        self._hf_dataset: Optional[Any] = None
        self._loaded = False
    
    def _get_default_data_dir(self) -> Path:
        """Get the default data directory for Subjects200K."""
        data_dir = Path.home() / '.opentryon' / 'datasets' / 'subjects200k'
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir
    
    def _ensure_downloaded(self) -> None:
        """Ensure the dataset is loaded from HuggingFace."""
        if self._hf_dataset is None:
            try:
                print(f"Loading Subjects200K dataset from HuggingFace ({self.HF_DATASET_NAME})...")
                self._hf_dataset = load_dataset(
                    self.HF_DATASET_NAME,
                    cache_dir=self.cache_dir or str(self.data_dir / 'hf_cache')
                )
                print("✓ Dataset loaded successfully")
                self._loaded = True
            except Exception as e:
                raise RuntimeError(
                    f"Failed to load Subjects200K dataset from HuggingFace: {e}. "
                    f"Make sure you have internet connection and the dataset is available."
                )
    
    def get_hf_dataset(self) -> Any:
        """
        Get the HuggingFace dataset instance.
        
        Returns:
            HuggingFace dataset instance with 'train' split
            
        Example:
            >>> dataset = Subjects200K()
            >>> hf_dataset = dataset.get_hf_dataset()
            >>> sample = hf_dataset['train'][0]
            >>> print(sample['collection'])
        """
        if self._hf_dataset is None:
            self._ensure_downloaded()
        return self._hf_dataset
    
    def filter_high_quality(
        self,
        collection: Optional[str] = None,
        min_quality_score: int = 5,
        num_proc: Optional[int] = None,
        cache_file_name: Optional[str] = None
    ) -> Any:
        """
        Filter high-quality image pairs from the dataset.
        
        Filters samples where all quality assessment dimensions (compositeStructure,
        objectConsistency, imageQuality) are >= min_quality_score.
        
        Args:
            collection: Optional collection filter ('collection_1', 'collection_2', 'collection_3').
                       If None, filters across all collections.
            min_quality_score: Minimum quality score threshold (default: 5).
            num_proc: Number of processes for filtering (default: None, uses all available).
            cache_file_name: Optional cache file path for filtered dataset.
            
        Returns:
            Filtered HuggingFace dataset
            
        Example:
            >>> dataset = Subjects200K()
            >>> filtered = dataset.filter_high_quality(
            ...     collection='collection_2',
            ...     min_quality_score=5
            ... )
            >>> print(f"High-quality pairs: {len(filtered)}")
        """
        hf_dataset = self.get_hf_dataset()
        
        def filter_func(item):
            # Filter by collection if specified
            if collection and item.get('collection') != collection:
                return False
            
            # Filter by quality
            quality = item.get('quality_assessment')
            if not quality:
                return False
            
            return all(
                quality.get(key, 0) >= min_quality_score
                for key in ['compositeStructure', 'objectConsistency', 'imageQuality']
            )
        
        filtered = hf_dataset['train'].filter(
            filter_func,
            num_proc=num_proc,
            cache_file_name=cache_file_name
        )
        
        return filtered
    
    def get_pytorch_dataset(
        self,
        split: str = 'train',
        transform: Optional[Callable] = None,
        collection: Optional[str] = None,
        filter_high_quality: bool = False
    ) -> Subjects200KPyTorchDataset:
        """
        Get a PyTorch Dataset instance for Subjects200K.
        
        Args:
            split: Dataset split ('train' or 'test'). Default: 'train'
            transform: Optional transform to apply to images
            collection: Optional collection filter ('collection_1', 'collection_2', 'collection_3')
            filter_high_quality: If True, filter samples with quality scores >= 5
            
        Returns:
            Subjects200KPyTorchDataset instance
            
        Example:
            >>> from torchvision import transforms
            >>> dataset = Subjects200K()
            >>> transform = transforms.Compose([
            ...     transforms.Resize((512, 512)),
            ...     transforms.ToTensor(),
            ... ])
            >>> pytorch_dataset = dataset.get_pytorch_dataset(
            ...     transform=transform,
            ...     collection='collection_2',
            ...     filter_high_quality=True
            ... )
        """
        hf_dataset = self.get_hf_dataset()
        
        if split not in hf_dataset:
            raise ValueError(f"Split '{split}' not found. Available splits: {list(hf_dataset.keys())}")
        
        return Subjects200KPyTorchDataset(
            hf_dataset=hf_dataset[split],
            transform=transform,
            collection=collection,
            filter_high_quality=filter_high_quality
        )
    
    def get_dataloader(
        self,
        split: str = 'train',
        batch_size: int = 8,
        shuffle: bool = True,
        num_workers: int = 0,
        transform: Optional[Callable] = None,
        collection: Optional[str] = None,
        filter_high_quality: bool = False,
        **dataloader_kwargs
    ) -> DataLoader:
        """
        Get a PyTorch DataLoader for Subjects200K.
        
        Args:
            split: Dataset split ('train' or 'test'). Default: 'train'
            batch_size: Batch size for DataLoader. Default: 8
            shuffle: Whether to shuffle the dataset. Default: True
            num_workers: Number of worker processes for data loading. Default: 0
            transform: Optional transform to apply to images
            collection: Optional collection filter ('collection_1', 'collection_2', 'collection_3')
            filter_high_quality: If True, filter samples with quality scores >= 5
            **dataloader_kwargs: Additional arguments for DataLoader
            
        Returns:
            PyTorch DataLoader instance
            
        Example:
            >>> from torchvision import transforms
            >>> dataset = Subjects200K()
            >>> transform = transforms.Compose([
            ...     transforms.Resize((512, 512)),
            ...     transforms.ToTensor(),
            ... ])
            >>> dataloader = dataset.get_dataloader(
            ...     batch_size=16,
            ...     transform=transform,
            ...     collection='collection_2',
            ...     filter_high_quality=True
            ... )
            >>> for batch in dataloader:
            ...     images = batch['image']  # [batch_size, 3, H, W]
            ...     collections = batch['collection']
        """
        pytorch_dataset = self.get_pytorch_dataset(
            split=split,
            transform=transform,
            collection=collection,
            filter_high_quality=filter_high_quality
        )
        
        return DataLoader(
            pytorch_dataset,
            batch_size=batch_size,
            shuffle=shuffle,
            num_workers=num_workers,
            **dataloader_kwargs
        )
    
    def get_sample(
        self,
        index: int,
        split: str = 'train',
        return_numpy: bool = False
    ) -> Dict[str, Any]:
        """
        Get a single sample from the dataset.
        
        Args:
            index: Sample index
            split: Dataset split ('train' or 'test'). Default: 'train'
            return_numpy: If True, return image as numpy array instead of PIL Image
            
        Returns:
            Dictionary containing sample data
            
        Example:
            >>> dataset = Subjects200K()
            >>> sample = dataset.get_sample(0)
            >>> image = sample['image']  # PIL Image
            >>> collection = sample['collection']
            >>> quality = sample['quality_assessment']
        """
        hf_dataset = self.get_hf_dataset()
        
        if split not in hf_dataset:
            raise ValueError(f"Split '{split}' not found. Available splits: {list(hf_dataset.keys())}")
        
        if index >= len(hf_dataset[split]):
            raise IndexError(f"Index {index} out of range for split '{split}' (size: {len(hf_dataset[split])})")
        
        sample = hf_dataset[split][index]
        
        result = {
            'index': index,
        }
        
        # Handle image
        image = sample['image']
        if return_numpy:
            if isinstance(image, Image.Image):
                image = np.array(image)
            result['image'] = image
        else:
            if isinstance(image, np.ndarray):
                image = Image.fromarray(image)
            result['image'] = image
        
        # Add metadata
        if 'collection' in sample:
            result['collection'] = sample['collection']
        if 'quality_assessment' in sample:
            result['quality_assessment'] = sample['quality_assessment']
        if 'description' in sample:
            result['description'] = sample['description']
        
        return result
    
    def load(
        self,
        normalize: bool = False,
        flatten: bool = False,
        **kwargs
    ) -> tuple:
        """
        Load Subjects200K dataset.
        
        Note: This method is provided for compatibility with the base Dataset interface,
        but Subjects200K is too large to load entirely into memory. It's recommended
        to use get_hf_dataset(), get_pytorch_dataset(), or get_dataloader() instead.
        
        Args:
            normalize: Not applicable for this dataset (images are already in [0, 255])
            flatten: Not applicable for this dataset
            **kwargs: Additional arguments (ignored)
            
        Returns:
            Tuple containing (train_data, test_data) where each is (images, metadata)
            
        Warning:
            This method loads the entire dataset into memory, which may not be feasible
            for large collections. Use get_dataloader() for efficient batch processing.
        """
        hf_dataset = self.get_hf_dataset()
        
        # Load train split
        train_split = hf_dataset['train']
        train_images = []
        train_metadata = []
        
        print("Loading train split into memory (this may take a while)...")
        for idx in range(len(train_split)):
            sample = train_split[idx]
            image = sample['image']
            if isinstance(image, np.ndarray):
                image = Image.fromarray(image)
            train_images.append(np.array(image))
            train_metadata.append({
                'collection': sample.get('collection'),
                'quality_assessment': sample.get('quality_assessment'),
                'description': sample.get('description'),
            })
        
        train_images = np.array(train_images)
        
        # Load test split if available
        if 'test' in hf_dataset:
            test_split = hf_dataset['test']
            test_images = []
            test_metadata = []
            
            print("Loading test split into memory...")
            for idx in range(len(test_split)):
                sample = test_split[idx]
                image = sample['image']
                if isinstance(image, np.ndarray):
                    image = Image.fromarray(image)
                test_images.append(np.array(image))
                test_metadata.append({
                    'collection': sample.get('collection'),
                    'quality_assessment': sample.get('quality_assessment'),
                    'description': sample.get('description'),
                })
            
            test_images = np.array(test_images)
        else:
            test_images = np.array([])
            test_metadata = []
        
        self._train_data = (train_images, train_metadata)
        self._test_data = (test_images, test_metadata)
        self._loaded = True
        
        return self._train_data, self._test_data
    
    def get_class_names(self) -> list:
        """
        Get collection names for Subjects200K.
        
        Returns:
            List of collection names: ['collection_1', 'collection_2', 'collection_3']
        """
        return ['collection_1', 'collection_2', 'collection_3']
    
    def get_info(self) -> dict:
        """Get Subjects200K dataset information."""
        info = super().get_info()
        info.update({
            'hf_dataset_name': self.HF_DATASET_NAME,
            'collections': self.get_class_names(),
            'total_samples': None,
        })
        
        if self._loaded and self._hf_dataset is not None:
            try:
                info['total_samples'] = len(self._hf_dataset['train'])
                if 'test' in self._hf_dataset:
                    info['test_samples'] = len(self._hf_dataset['test'])
            except:
                pass
        
        return info


# Convenience function for backward compatibility
def load_subjects200k(
    data_dir: Optional[str] = None,
    download: bool = True,
    cache_dir: Optional[str] = None
) -> Any:
    """
    Load Subjects200K dataset from HuggingFace (convenience function).
    
    This is a convenience function that creates a Subjects200K instance and returns
    the HuggingFace dataset. For more control, use the Subjects200K class directly.
    
    Args:
        data_dir: Directory to store the dataset cache. If None, uses default location.
        download: If True, download the dataset if it doesn't exist (always True for HuggingFace)
        cache_dir: Optional cache directory for HuggingFace datasets.
        
    Returns:
        HuggingFace dataset instance
        
    Example:
        >>> from tryon.datasets import load_subjects200k
        >>> hf_dataset = load_subjects200k()
        >>> sample = hf_dataset['train'][0]
    """
    dataset = Subjects200K(data_dir=data_dir, download=download, cache_dir=cache_dir)
    return dataset.get_hf_dataset()

