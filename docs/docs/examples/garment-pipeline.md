# Garment Pipeline Example

Complete example of processing garments through the full pipeline.

```python
from dotenv import load_dotenv
load_dotenv()

from tryon.preprocessing import segment_garment, extract_garment

# Complete pipeline
segment_garment("data/cloth", "output/segmented", cls="all")
extract_garment("data/cloth", "output/extracted", cls="all", resize_to_width=400)
```

See [Basic Usage](basic-usage.md) for more examples.

