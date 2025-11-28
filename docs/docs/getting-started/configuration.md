# Configuration

Learn how to configure OpenTryOn for your specific needs. OpenTryOn supports three main categories: **Preprocessing**, **API Integrations**, and **Datasets**.

## Environment Variables

OpenTryOn uses environment variables for configuration. Create a `.env` file in your project root:

### Preprocessing (Required for Local Preprocessing)

```env
# U2Net Model Checkpoints (Required for garment/human segmentation)
U2NET_CLOTH_SEG_CHECKPOINT_PATH=path/to/cloth_segm.pth
U2NET_SEGM_CHECKPOINT_PATH=path/to/u2net.pth

# Optional: GPU Configuration
CUDA_VISIBLE_DEVICES=0

# Optional: Logging
LOG_LEVEL=INFO
```

### API Integrations (Optional - Only configure APIs you plan to use)

```env
# Segmind Try-On Diffusion API
SEGMIND_API_KEY=your_segmind_api_key

# Kling AI Virtual Try-On API
KLING_AI_API_KEY=your_kling_api_key
KLING_AI_SECRET_KEY=your_kling_secret_key
KLING_AI_BASE_URL=https://api-singapore.klingai.com  # Optional

# Amazon Nova Canvas (AWS Bedrock)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AMAZON_NOVA_REGION=us-east-1  # Options: us-east-1, ap-northeast-1, eu-west-1
AMAZON_NOVA_MODEL_ID=amazon.nova-canvas-v1:0  # Optional

# Google Gemini (Nano Banana Image Generation)
GEMINI_API_KEY=your_gemini_api_key
```

### Datasets (Optional - Only if using HuggingFace datasets)

```env
# HuggingFace datasets cache (for Subjects200K)
# Defaults to ~/.cache/huggingface/datasets if not set
HF_DATASETS_CACHE=path/to/cache
```

**Note**: You only need to configure the APIs and features you plan to use. For example:
- **Preprocessing only**: Only U2Net checkpoints required
- **API integrations only**: Only API keys required (no local models needed)
- **Datasets only**: No configuration needed (automatic download/caching)

## Loading Environment Variables

Always load environment variables before using OpenTryOn:

```python
from dotenv import load_dotenv
load_dotenv()

# Now import and use OpenTryOn modules
from tryon.preprocessing import segment_garment
from tryon.api import SegmindVTONAdapter
from tryon.datasets import FashionMNIST
```

## Getting API Keys

### Segmind Try-On Diffusion

1. Sign up at [Segmind API Portal](https://www.segmind.com/models/try-on-diffusion/api)
2. Obtain your API key from the dashboard
3. Add to `.env`: `SEGMIND_API_KEY=your_key`

### Kling AI Virtual Try-On

1. Sign up at [Kling AI Developer Portal](https://app.klingai.com/)
2. Obtain API key (access key) and secret key
3. Add to `.env`:
   ```env
   KLING_AI_API_KEY=your_api_key
   KLING_AI_SECRET_KEY=your_secret_key
   ```

### Amazon Nova Canvas

1. Set up AWS account with Bedrock access
2. Enable Nova Canvas in AWS Bedrock console (Model access section)
3. Configure AWS credentials (via `.env` or AWS CLI):
   ```env
   AWS_ACCESS_KEY_ID=your_access_key
   AWS_SECRET_ACCESS_KEY=your_secret_key
   AMAZON_NOVA_REGION=us-east-1
   ```

### Google Gemini (Nano Banana)

1. Sign up at [Google AI Studio](https://aistudio.google.com/)
2. Obtain API key from [API Keys page](https://aistudio.google.com/app/apikey)
3. Add to `.env`: `GEMINI_API_KEY=your_key`

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

## Quick Configuration Examples

### Preprocessing Only

```env
U2NET_CLOTH_SEG_CHECKPOINT_PATH=./models/cloth_segm.pth
U2NET_SEGM_CHECKPOINT_PATH=./models/u2net.pth
```

### API Integrations Only (No Local Models)

```env
SEGMIND_API_KEY=your_segmind_key
GEMINI_API_KEY=your_gemini_key
```

### Full Setup (Preprocessing + APIs + Datasets)

```env
# Preprocessing
U2NET_CLOTH_SEG_CHECKPOINT_PATH=./models/cloth_segm.pth
U2NET_SEGM_CHECKPOINT_PATH=./models/u2net.pth

# APIs
SEGMIND_API_KEY=your_segmind_key
KLING_AI_API_KEY=your_kling_key
KLING_AI_SECRET_KEY=your_kling_secret
GEMINI_API_KEY=your_gemini_key
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AMAZON_NOVA_REGION=us-east-1
```

## Best Practices

1. **Always use `.env` file**: Never commit API keys or paths to version control
2. **Load environment variables first**: Before importing any OpenTryOn modules
3. **Use absolute paths**: For checkpoint paths to avoid issues
4. **Check GPU availability**: Verify CUDA before running intensive operations
5. **Only configure what you need**: Don't add API keys for services you won't use
6. **Keep `.env` in `.gitignore`**: Protect your credentials

## Next Steps

- **[Quick Start Guide](quickstart.md)**: See examples of using APIs, datasets, and preprocessing
- **[API Reference](../api-reference/overview)**: Complete API documentation
- **[Datasets Module](../datasets/overview)**: Learn about available datasets
- **[Preprocessing](../preprocessing/overview)**: Preprocessing documentation

