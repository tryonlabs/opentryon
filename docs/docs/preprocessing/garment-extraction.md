# Garment Extraction

Extract and preprocess garments from images.

## Usage

```python
from tryon.preprocessing import extract_garment

extract_garment(
    inputs_dir="data/original_cloth",
    outputs_dir="data/cloth",
    cls="upper",
    resize_to_width=400
)
```

See [Preprocessing Overview](overview.md) for details.

