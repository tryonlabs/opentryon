# Garment Segmentation

Detailed guide to garment segmentation using U2Net.

## Overview

Garment segmentation identifies and separates different garment types from images.

## Usage

```python
from tryon.preprocessing import segment_garment

segment_garment(
    inputs_dir="data/original_cloth",
    outputs_dir="data/garment_segmented",
    cls="upper"
)
```

## Parameters

- `inputs_dir`: Directory containing input images
- `outputs_dir`: Directory to save segmentation masks
- `cls`: Garment class - "upper", "lower", "dress", or "all"

## Output

Segmentation masks saved as JPG files with format: `{image_name}_{class_id}.jpg`

See [Preprocessing Overview](overview.md) for more details.

