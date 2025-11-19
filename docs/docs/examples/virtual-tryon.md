# Virtual Try-On Examples

Examples demonstrating virtual try-on capabilities using various APIs and methods.

## Kling AI API Example

Generate realistic virtual try-on images using Kling AI's Kolors Virtual Try-On API with automatic task polling.

```python
from dotenv import load_dotenv
load_dotenv()

from tryon.api import KlingAIVTONAdapter
from PIL import Image

# Initialize adapter
adapter = KlingAIVTONAdapter()

# Generate virtual try-on images (automatically polls until completion)
images = adapter.generate_and_decode(
    source_image="data/person.jpg",
    reference_image="data/shirt.jpg",
    model="kolors-virtual-try-on-v1-5"
)

# Save results
for idx, image in enumerate(images):
    image.save(f"outputs/vton_result_{idx}.png")
    print(f"Saved result {idx}: {image.size}")
```

### Custom Polling

```python
from tryon.api import KlingAIVTONAdapter

adapter = KlingAIVTONAdapter()

# Submit task and get task ID
image_urls = adapter.generate(
    source_image="person.jpg",
    reference_image="garment.jpg"
)

# Or poll manually with custom settings
task_id = "your_task_id"
image_urls = adapter.poll_task_until_complete(
    task_id=task_id,
    poll_interval=3,  # Check every 3 seconds
    max_wait_time=600  # Maximum 10 minutes
)
```

## Amazon Nova Canvas API Example

Generate realistic virtual try-on images using Amazon Nova Canvas through AWS Bedrock.

```python
from tryon.api import AmazonNovaCanvasVTONAdapter
from PIL import Image

# Initialize adapter
adapter = AmazonNovaCanvasVTONAdapter(region="us-east-1")

# Generate virtual try-on images with GARMENT mask
images = adapter.generate_and_decode(
    source_image="data/person.jpg",
    reference_image="data/shirt.jpg",
    mask_type="GARMENT",
    garment_class="UPPER_BODY"
)

# Save results
for idx, image in enumerate(images):
    image.save(f"outputs/vton_result_{idx}.png")
```

### Different Garment Classes

```python
from tryon.api import AmazonNovaCanvasVTONAdapter

adapter = AmazonNovaCanvasVTONAdapter()

# Upper body garments
images = adapter.generate_and_decode(
    source_image="person.jpg",
    reference_image="shirt.jpg",
    mask_type="GARMENT",
    garment_class="UPPER_BODY"
)

# Lower body garments
images = adapter.generate_and_decode(
    source_image="person.jpg",
    reference_image="pants.jpg",
    mask_type="GARMENT",
    garment_class="LOWER_BODY"
)

# Full body garments
images = adapter.generate_and_decode(
    source_image="person.jpg",
    reference_image="dress.jpg",
    mask_type="GARMENT",
    garment_class="FULL_BODY"
)
```

### Custom Mask Image

```python
from tryon.api import AmazonNovaCanvasVTONAdapter

adapter = AmazonNovaCanvasVTONAdapter()

# Use custom black-and-white mask image
images = adapter.generate_and_decode(
    source_image="person.jpg",
    reference_image="garment.jpg",
    mask_type="IMAGE",
    mask_image="custom_mask.png"
)
```

## Segmind API Example

Generate realistic virtual try-on images using Segmind's Try-On Diffusion API.

```python
from dotenv import load_dotenv
load_dotenv()

from tryon.api import SegmindVTONAdapter
from PIL import Image

# Initialize adapter
adapter = SegmindVTONAdapter()

# Generate virtual try-on images
images = adapter.generate_and_decode(
    model_image="data/person.jpg",
    cloth_image="data/shirt.jpg",
    category="Upper body",
    num_inference_steps=35,
    guidance_scale=2.5,
    seed=42
)

# Save results
for idx, image in enumerate(images):
    image.save(f"outputs/vton_result_{idx}.png")
    print(f"Saved result {idx}: {image.size}")
```

### Using URLs

```python
from tryon.api import SegmindVTONAdapter

adapter = SegmindVTONAdapter()

# Use image URLs directly
images = adapter.generate_and_decode(
    model_image="https://example.com/person.jpg",
    cloth_image="https://example.com/garment.jpg",
    category="Lower body"
)

images[0].save("result.png")
```

### Different Garment Categories

```python
from tryon.api import SegmindVTONAdapter

adapter = SegmindVTONAdapter()

# Upper body garments
images = adapter.generate_and_decode(
    model_image="person.jpg",
    cloth_image="shirt.jpg",
    category="Upper body"
)

# Lower body garments
images = adapter.generate_and_decode(
    model_image="person.jpg",
    cloth_image="pants.jpg",
    category="Lower body"
)

# Dresses
images = adapter.generate_and_decode(
    model_image="person.jpg",
    cloth_image="dress.jpg",
    category="Dress"
)
```

### Batch Processing

```python
from tryon.api import SegmindVTONAdapter
import os

adapter = SegmindVTONAdapter()

# Process multiple garment images
garments = ["shirt1.jpg", "shirt2.jpg", "shirt3.jpg"]
person_image = "person.jpg"

for idx, garment in enumerate(garments):
    images = adapter.generate_and_decode(
        model_image=person_image,
        cloth_image=garment,
        category="Upper body"
    )
    images[0].save(f"outputs/result_{idx}.png")
```

## Combining with Datasets

Use VITON-HD dataset samples with virtual try-on APIs:

```python
from tryon.datasets import VITONHD
from tryon.api import SegmindVTONAdapter
from dotenv import load_dotenv
load_dotenv()

# Load dataset
dataset = VITONHD(data_dir="./datasets/viton_hd")

# Get a sample
sample = dataset.get_sample(0, split='test')
person_img = sample['person']
clothing_img = sample['clothing']

# Save temporary images
person_img.save("temp_person.jpg")
clothing_img.save("temp_clothing.jpg")

# Generate virtual try-on
adapter = SegmindVTONAdapter()
result_images = adapter.generate_and_decode(
    model_image="temp_person.jpg",
    cloth_image="temp_clothing.jpg",
    category="Upper body"
)

# Save result
result_images[0].save("vton_result.jpg")
```

## TryOnDiffusion Example

Example of using TryOnDiffusion for virtual try-on.

See [TryOnDiffusion Documentation](../tryondiffusion/overview.md) for complete examples.

## See Also

- [Segmind API Documentation](../api-reference/segmind) - Complete Segmind API reference
- [Datasets Examples](datasets) - Dataset usage examples
- [API Reference](../api-reference/overview) - Complete API documentation

