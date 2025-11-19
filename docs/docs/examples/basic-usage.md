# Examples

## Basic Usage

Simple example of using OpenTryOn for garment preprocessing.

```python
from dotenv import load_dotenv
load_dotenv()

from tryon.preprocessing import segment_garment, extract_garment

# Segment garment
segment_garment(
    inputs_dir="data/original_cloth",
    outputs_dir="data/garment_segmented",
    cls="upper"
)

# Extract garment
extract_garment(
    inputs_dir="data/original_cloth",
    outputs_dir="data/cloth",
    cls="upper",
    resize_to_width=400
)
```

## Complete Pipeline

End-to-end virtual try-on preprocessing pipeline.

```python
from dotenv import load_dotenv
load_dotenv()

from tryon.preprocessing import (
    segment_garment,
    extract_garment,
    segment_human
)

# 1. Segment garments
segment_garment(
    inputs_dir="data/original_cloth",
    outputs_dir="data/garment_segmented",
    cls="all"
)

# 2. Extract garments
extract_garment(
    inputs_dir="data/original_cloth",
    outputs_dir="data/cloth",
    cls="all",
    resize_to_width=400
)

# 3. Segment human
segment_human(
    image_path="data/original_human/model.jpg",
    output_dir="data/human_segmented"
)
```

## Single Image Processing

Process a single image object.

```python
from PIL import Image
from tryon.preprocessing.extract_garment_new import extract_garment

# Load image
image = Image.open("garment.jpg").convert("RGB")

# Extract garment
garments = extract_garment(image, cls="upper", resize_to_width=400)

# Access extracted garment
if "upper" in garments:
    garments["upper"].save("extracted_upper.jpg")
```

