# Configuration

Learn how to configure OpenTryOn for your specific needs.

## Environment Variables

OpenTryOn uses environment variables for configuration. Create a `.env` file in your project root:

```env
# U2Net Model Checkpoints
U2NET_CLOTH_SEG_CHECKPOINT_PATH=path/to/cloth_segm.pth
U2NET_SEGM_CHECKPOINT_PATH=path/to/u2net.pth

# Optional: GPU Configuration
CUDA_VISIBLE_DEVICES=0

# Optional: Logging
LOG_LEVEL=INFO
```

## Loading Environment Variables

Always load environment variables before using OpenTryOn:

```python
from dotenv import load_dotenv
load_dotenv()

# Now import and use OpenTryOn
from tryon.preprocessing import segment_garment
```

## Configuration Options

### GPU Configuration

Specify which GPU to use:

```python
import os
os.environ["CUDA_VISIBLE_DEVICES"] = "0"  # Use first GPU
```

### Model Checkpoint Paths

Set custom checkpoint paths:

```python
import os
os.environ["U2NET_CLOTH_SEG_CHECKPOINT_PATH"] = "/custom/path/cloth_segm.pth"
os.environ["U2NET_SEGM_CHECKPOINT_PATH"] = "/custom/path/u2net.pth"
```

### Logging Configuration

Configure logging level:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

## Default Settings

OpenTryOn uses sensible defaults:

- **Image Size**: Automatically resized based on model requirements
- **Batch Size**: 1 (can be adjusted for batch processing)
- **Device**: Auto-detects CUDA if available, falls back to CPU
- **Normalization**: Images normalized to [-1, 1] range

## Custom Configuration

You can override defaults when calling functions:

```python
from tryon.preprocessing.extract_garment_new import extract_garment
from PIL import Image
import torch

# Use specific device
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

# Load model once for efficiency
net = load_cloth_segm_model(device, os.environ.get("U2NET_CLOTH_SEGM_CHECKPOINT_PATH"))

# Use pre-loaded model
image = Image.open("garment.jpg")
garments = extract_garment(
    image=image,
    cls="upper",
    resize_to_width=400,
    net=net,  # Reuse model
    device=device
)
```

## Best Practices

1. **Always use `.env` file**: Never commit API keys or paths to version control
2. **Load environment variables first**: Before importing any OpenTryOn modules
3. **Use absolute paths**: For checkpoint paths to avoid issues
4. **Check GPU availability**: Verify CUDA before running intensive operations

