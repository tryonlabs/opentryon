# Preprocessing Overview

The preprocessing module provides comprehensive utilities for preparing images for virtual try-on applications.

## Features

- **Garment Segmentation**: Segment garments into categories (upper, lower, dress)
- **Garment Extraction**: Extract and preprocess garments
- **Human Segmentation**: Isolate human subjects from images
- **Pose Estimation**: Extract pose keypoints using OpenPose
- **Image Captioning**: Generate captions from fashion images

## Module Structure

```
tryon/preprocessing/
├── preprocess_garment.py      # Batch garment processing
├── extract_garment_new.py      # Single image garment extraction
├── preprocess_human.py         # Human segmentation
├── captioning/                 # Image captioning
├── u2net/                      # U2Net segmentation models
└── utils.py                    # Utility functions
```

## Quick Reference

### Garment Segmentation

```python
from tryon.preprocessing import segment_garment

segment_garment(
    inputs_dir="path/to/input",
    outputs_dir="path/to/output",
    cls="upper"  # "upper", "lower", "dress", or "all"
)
```

### Garment Extraction

```python
from tryon.preprocessing import extract_garment

extract_garment(
    inputs_dir="path/to/input",
    outputs_dir="path/to/output",
    cls="upper",
    resize_to_width=400  # Optional
)
```

### Human Segmentation

```python
from tryon.preprocessing import segment_human

segment_human(
    image_path="path/to/image.jpg",
    output_dir="path/to/output"
)
```

## Supported Garment Categories

- **upper**: Upper body garments (tops, shirts, jackets)
- **lower**: Lower body garments (pants, skirts)
- **dress**: Full-body dresses
- **all**: Automatically detect and process all categories

## Next Steps

- Learn about [Garment Segmentation](garment-segmentation.md)
- Explore [Human Segmentation](human-segmentation.md)
- Check out [Pose Estimation](pose-estimation.md)

