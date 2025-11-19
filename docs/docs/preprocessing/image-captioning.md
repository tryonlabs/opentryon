# Image Captioning

Generate captions from fashion images using LLaVA-NeXT.

## Usage

```python
from tryon.preprocessing.captioning import caption_image
from PIL import Image

image = Image.open("fashion_image.jpg")
question = "Extract outfit details as JSON"

json_data, caption = caption_image(
    image=image,
    question=question,
    json_only=False
)
```

See [Preprocessing Overview](overview.md) for details.

