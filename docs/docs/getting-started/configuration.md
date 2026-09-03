# Configuration

Learn how to configure OpenTryOn for your specific needs. The same `opentryon/.env` file is read by the **CLI**, the **[MCP server](mcp)**, and **[TryOn Studio](tryon-studio)** Connect (Studio never stores keys itself).

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

# Google Vertex Virtual Try-On (virtual-try-on-001) — not GEMINI_API_KEY
GOOGLE_CLOUD_PROJECT=your_gcp_project_id
# GOOGLE_CLOUD_LOCATION=global

# BFL AI (FLUX.2 Image Generation)
BFL_API_KEY=your_bfl_api_key

# Moonshot AI (Kimi K2.6 / K2.7 Code multimodal understanding)
MOONSHOT_API_KEY=your_moonshot_api_key

# Tencent TokenHub (Hy4 preview LLM) — not Moonshot / DashScope
TOKENHUB_API_KEY=your_tokenhub_api_key
# TOKENHUB_BASE_URL=https://tokenhub-intl.tencentcloudmaas.com/v1

# Alibaba DashScope (Wan, Qwen3.8-Max, Qwen-Image, OutfitAnyone-Plus)
DASHSCOPE_API_KEY=your_dashscope_api_key

# Photoroom Virtual Try-On + Virtual Model
PHOTOROOM_API_KEY=your_photoroom_api_key

# MiniMax Hailuo 2.3 + MiniMax H3 / H3 Max video (same key; H3 uses V2)
MINIMAX_API_KEY=your_minimax_api_key

# Fal (third-party MiniMax H3 Max — T2V / I2V / R2V)
FAL_KEY=your_fal_key

# NVIDIA NIM (Nemotron Omni understand, Cosmos 3 Reasoner, Cosmos 3 Generator)
NVIDIA_API_KEY=your_nvidia_api_key

# Meta Model API (Muse Image generate/edit/vton)
MODEL_API_KEY=your_meta_model_api_key

# Pruna AI (P-Image, P-Image-Ideogram, P-Image-Edit, try-on, P-Video family)
PRUNA_API_KEY=your_pruna_api_key
```

### Datasets (Optional - Only if using HuggingFace datasets)

```env
# HuggingFace datasets cache (for Subjects200K)
# Defaults to ~/.cache/huggingface/datasets if not set
HF_DATASETS_CACHE=path/to/cache
```

### Planner / Studio chat (optional — only if you use `planner_agent`)

The cheap intent model is separate from image/VTON/video keys. Studio Agent chat calls MCP `planner_agent`; set these on the MCP host and restart the server. See [Planner Agent](../agents/planner-agent.md) and [TryOn Studio](tryon-studio).

```env
OPENTRYON_AGENT_LLM_PROVIDER=openai
OPENTRYON_PLANNER_LLM_MODEL=gpt-4o-mini
# OPENAI_API_KEY=...   # or ANTHROPIC_API_KEY / GEMINI_API_KEY
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

### BFL AI (FLUX.2)

1. Sign up at [BFL AI](https://docs.bfl.ai/)
2. Obtain your API key from the BFL AI dashboard
3. Add to `.env`: `BFL_API_KEY=your_key`

### Moonshot AI (Kimi K2.6 / K2.7 Code)

1. Sign up at [platform.kimi.ai](https://platform.kimi.ai/)
2. Obtain your API key from the [API Keys console](https://platform.kimi.ai/console/api-keys)
3. Add to `.env`: `MOONSHOT_API_KEY=your_key`

### Tencent TokenHub (Hy4 preview)

1. Follow [TokenHub Chat Completions](https://www.tencentcloud.com/document/product/1300/80695) and create an API key
2. Add to `.env`: `TOKENHUB_API_KEY=your_key`
3. Optional: `TENCENT_TOKENHUB_API_KEY` (alias) or `TOKENHUB_BASE_URL` (default international endpoint)
4. Local weights twin (`hy4-preview-local`) does **not** use this key — serve vLLM/SGLang and set `HY4_BASE_URL`

See [Hy4 TokenHub](../api-reference/hy4.md) and [Hy4 local](../local-models/hy4.md).

### Alibaba DashScope (Qwen3.8, Qwen-Image, Wan)

1. Sign up at [Alibaba Cloud Model Studio](https://www.alibabacloud.com/help/en/model-studio/get-api-key)
2. Create an API key for your region
3. Add to `.env`:

   ```env
   DASHSCOPE_API_KEY=your_key
   # Optional: QWEN_BASE_URL for Qwen3.8-Max chat (OpenAI-compatible)
   # Optional: QWEN_IMAGE_BASE_URL for Qwen-Image T2I / I2I / VTON
   ```

   Same key covers `understand --model qwen3.8-max`, `generate|edit|vton --model qwen-image`, `video-generate --model wan-api` / `wan-3.0`, and **Beijing-region** `vton --model outfitanyone-plus` (`aitryon-plus`). International keys used for Qwen/Wan do not unlock OutfitAnyone-Plus.

   Local open-weight twin (`pip install opentryon[local]`, CUDA, recent Diffusers):

   ```env
   # Optional overrides; defaults are the official HF snapshots
   # QWEN_IMAGE_LOCAL_MODEL_ID=Qwen/Qwen-Image-2512
   # QWEN_IMAGE_EDIT_MODEL_ID=Qwen/Qwen-Image-Edit-2511
   # QWEN_IMAGE_LOCAL_PATH=/path/to/local/t2i-snapshot
   # QWEN_IMAGE_EDIT_PATH=/path/to/local/edit-snapshot
   ```

   CLI: `opentryon generate|edit|vton --model qwen-image-local`. See
   [Qwen-Image local](../local-models/qwen-image.md).

### Local dedicated VTON (Leffa / CatVTON)

No API key. Needs `pip install opentryon[local]` and a CUDA GPU.

- `vton --model leffa` — [Leffa](../local-models/leffa.md). Optional `LEFFA_HOME` / `LEFFA_CKPT`.
- `vton --model catvton` — [CatVTON](../local-models/catvton.md) (**CC BY-NC-SA 4.0**). Optional `CATVTON_BASE_MODEL` if the SD 1.5 inpainting repo is gated.

### Photoroom (Virtual Try-On / Virtual Model)

1. Activate the API at [app.photoroom.com/api](https://app.photoroom.com/api)
2. Add to `.env`: `PHOTOROOM_API_KEY=your_key`
3. Optional watermarked tests: prefix the key with `sandbox_` or set `PHOTOROOM_SANDBOX=1`

   Covers `vton --model photoroom-vton` (shopper photo + product) and
   `vton --model photoroom-virtual-model` (flat-lay → on-model). Plus / Enterprise
   Image Editing API. See [Photoroom](../api-reference/photoroom.md).

### MiniMax (Hailuo 2.3 + H3 + H3 Max)

1. Sign up at [MiniMax Open Platform](https://platform.minimax.io/)
2. Create an interface key from [API keys](https://platform.minimax.io/user-center/basic-information/interface-key)
3. Add to `.env`: `MINIMAX_API_KEY=your_key`

   Same key covers `video-generate --model hailuo-2.3` (V1), `video-generate --model minimax-h3` (V2 H3), and `video-generate --model minimax-h3-max` (V2 H3 Max, fast). H3 on the API is billed as pay-as-you-go video.

   Local open-weight twin (`pip install opentryon[local]`, CUDA, Diffusers from main): `--model minimax-h3-local`. The Community License for those weights excludes US/EU/UK/South Korea unless separately authorized. See [MiniMax H3 local](../local-models/minimax-h3.md).

### Fal (MiniMax H3 Max)

1. Create a key at [Fal API keys](https://fal.ai/dashboard/keys)
2. Add to `.env`: `FAL_KEY=your_key` (`FAL_API_KEY` is an alias)

   Covers `video-generate --model fal-h3-max` (T2V / I2V / **R2V**). This is a third-party hoster, not MiniMax’s V2 API. First-party Max remains `--model minimax-h3-max`. See [MiniMax H3 Max (Fal)](../api-reference/fal-h3-max.md).

### NVIDIA NIM (Nemotron / Cosmos)

1. Create a key at [build.nvidia.com](https://build.nvidia.com)
2. Add to `.env`: `NVIDIA_API_KEY=your_key`

   Same key covers `understand --model nemotron-omni`, `understand --model cosmos3-reasoner`, and `video-generate --model cosmos3`. Optional `COSMOS3_INFER_URL` points a self-hosted Generator NIM at `http://127.0.0.1:8000/v1/infer`. See [NVIDIA NIM](../api-reference/nvidia-nim.md).

### Meta Model API (Muse Image)

1. Create a key in the [Model API dashboard](https://dev.meta.ai/docs/authentication)
2. Add to `.env`: `MODEL_API_KEY=your_key` (aliases: `META_MODEL_API_KEY`, `MUSE_API_KEY`)

   Covers `generate|edit|vton --model muse-image`. **Muse Video has no developer API or open weights** yet.

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
BFL_API_KEY=your_bfl_key
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
BFL_API_KEY=your_bfl_key
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

