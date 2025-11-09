"""
Base Dataset Interface

This module defines the base class for all dataset adapters in the tryon.datasets module.
"""

from abc import ABC, abstractmethod
from typing import Tuple, Optional, Dict, Any
from pathlib import Path
import numpy as np


class Dataset(ABC):
    """
    Base class for all dataset adapters.
    
    This class defines the interface that all dataset implementations must follow,
    ensuring consistency across different datasets.
    """
    
    def __init__(
        self,
        data_dir: Optional[str] = None,
        download: bool = True,
        **kwargs
    ):
        """
        Initialize the dataset.
        
        Args:
            data_dir: Directory to store the dataset. If None, uses default location
            download: If True, download the dataset if it doesn't exist
            **kwargs: Additional dataset-specific parameters
        """
        if data_dir is None:
            self.data_dir = self._get_default_data_dir()
        else:
            self.data_dir = Path(data_dir)
        
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.download = download
        self._train_data: Optional[Tuple[np.ndarray, np.ndarray]] = None
        self._test_data: Optional[Tuple[np.ndarray, np.ndarray]] = None
        self._loaded = False
        
        # Download if needed
        if download:
            self._ensure_downloaded()
    
    @abstractmethod
    def _get_default_data_dir(self) -> Path:
        """
        Get the default data directory for this dataset.
        
        Returns:
            Path to the default data directory
        """
        pass
    
    @abstractmethod
    def _ensure_downloaded(self) -> None:
        """
        Ensure the dataset files are downloaded.
        Should check if files exist and download if needed.
        """
        pass
    
    @abstractmethod
    def load(
        self,
        normalize: bool = False,
        flatten: bool = False,
        **kwargs
    ) -> Tuple[Tuple[np.ndarray, np.ndarray], Tuple[np.ndarray, np.ndarray]]:
        """
        Load the dataset.
        
        Args:
            normalize: If True, normalize pixel values to [0, 1] range
            flatten: If True, flatten images to 1D arrays
            **kwargs: Additional dataset-specific parameters
            
        Returns:
            Tuple of (train_data, test_data) where each is (images, labels)
        """
        pass
    
    @abstractmethod
    def get_class_names(self) -> list:
        """
        Get all class names for this dataset.
        
        Returns:
            List of class name strings
        """
        pass
    
    def get_class_name(self, label: int) -> str:
        """
        Get the class name for a given label.
        
        Args:
            label: Integer label
            
        Returns:
            Class name string
        """
        class_names = self.get_class_names()
        if not 0 <= label < len(class_names):
            raise ValueError(
                f"Label must be between 0 and {len(class_names) - 1}, got {label}"
            )
        return class_names[label]
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get dataset information.
        
        Returns:
            Dictionary with dataset metadata
        """
        return {
            'name': self.__class__.__name__,
            'data_dir': str(self.data_dir),
            'loaded': self._loaded,
        }
    
    def __repr__(self) -> str:
        """String representation of the dataset."""
        info = self.get_info()
        return f"{info['name']}(data_dir='{info['data_dir']}', loaded={info['loaded']})"

