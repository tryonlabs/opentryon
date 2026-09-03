# Installation

This guide will help you install OpenTryOn on your system.

## Prerequisites

Before installing OpenTryOn, ensure you have:

- **Python 3.10** or higher
- **CUDA-capable GPU** (recommended for best performance)
- **Conda** or **Miniconda** (recommended)
- **Git** (for cloning the repository)

## Installation Methods

### Method 1: Using Conda (Recommended)

Conda is the recommended installation method as it handles all dependencies including CUDA libraries.

#### Step 1: Clone the Repository

```bash
git clone https://github.com/tryonlabs/opentryon.git
cd opentryon
```

#### Step 2: Create Conda Environment

```bash
conda env create -f environment.yml
conda activate opentryon
```

This will create a new conda environment named `opentryon` with all required dependencies.

#### Step 3: Install Package

```bash
pip install -e .
```

### Method 2: Using pip

If you prefer using pip, you can install dependencies directly:

#### Step 1: Clone the Repository

```bash
git clone https://github.com/tryonlabs/opentryon.git
cd opentryon
```

#### Step 2: Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
pip install -e .
```

### Method 3: Install from PyPI (recommended for app use)

```bash
pip install -U opentryon
# optional local/GPU models:
pip install -U "opentryon[local]"
```

Verify the version (current stable: **0.0.4**):

```bash
python -c "import tryon; print(tryon.__version__)"
opentryon --help
```

## Verify Installation

After installation, verify that OpenTryOn is correctly installed:

```python
python -c "import tryon; print('OpenTryOn', tryon.__version__, 'installed successfully')"
```

## MCP server and TryOn Studio

The same install is what the MCP server and Studio talk to.

- **MCP:** `cd mcp-server && pip install -r requirements.txt && python server.py` (stdio) or `python server.py --transport http --host 127.0.0.1 --port 8000` (Studio). Guide: [MCP Server](mcp). Full tool table: [`mcp-server/README.md`](https://github.com/tryonlabs/opentryon/blob/main/mcp-server/README.md).
- **Studio:** clone [tryon-studio](https://github.com/tryonlabs/tryon-studio), point `OPENTRYON_MCP_URL` at that HTTP endpoint, `npm run dev`. Guide: [TryOn Studio](tryon-studio).

## Configuration

### Environment Variables

Create a `.env` file in the project root with the following variables:

#### Preprocessing (Required for local preprocessing)

```env
U2NET_CLOTH_SEG_CHECKPOINT_PATH=path/to/cloth_segm.pth
U2NET_SEGM_CHECKPOINT_PATH=path/to/u2net.pth
```

#### API Integrations (Optional, for cloud-based services)

```env
# Segmind Try-On Diffusion API
SEGMIND_API_KEY=your_segmind_api_key

# Kling AI Virtual Try-On API
KLING_AI_API_KEY=your_kling_api_key
KLING_AI_SECRET_KEY=your_kling_secret_key

# Amazon Nova Canvas (AWS Bedrock)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AMAZON_NOVA_REGION=us-east-1

# Google Gemini (Nano Banana Image Generation)
GEMINI_API_KEY=your_gemini_api_key

# Google Vertex Virtual Try-On (not GEMINI_API_KEY)
GOOGLE_CLOUD_PROJECT=your_gcp_project_id

# BFL AI (FLUX.2 Image Generation)
BFL_API_KEY=your_bfl_api_key
```

**Note**: You only need to configure the APIs you plan to use. For preprocessing-only workflows, only the U2Net checkpoints are required.

### Download Model Checkpoints

#### U2Net Cloth Segmentation

Download the checkpoint from the [huggingface-cloth-segmentation repository](https://github.com/wildoctopus/huggingface-cloth-segmentation):

```bash
# Example: Download and place in project root
wget https://huggingface.co/levihsu/OOTDiffusion/resolve/main/cloth_segm.pth
```

#### U2Net Human Segmentation

Download U2Net weights for human segmentation:

```bash
# Download from official U2Net repository
# Place in appropriate location and update U2NET_SEGM_CHECKPOINT_PATH
```

## GPU Setup (Optional but Recommended)

For optimal performance, ensure CUDA is properly configured:

### Check CUDA Installation

```python
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"CUDA version: {torch.version.cuda}")
print(f"GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'None'}")
```

### Install CUDA-Compatible PyTorch

If CUDA is not detected, install the appropriate PyTorch version:

```bash
# For CUDA 11.8
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# For CUDA 12.1
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

## Troubleshooting

### Common Issues

#### Issue: Import Errors

**Solution**: Ensure all dependencies are installed:

```bash
pip install -r requirements.txt
```

#### Issue: CUDA Out of Memory

**Solution**: Reduce batch size or image resolution in your code.

#### Issue: Model Checkpoint Not Found

**Solution**: Ensure checkpoint paths in `.env` are correct and files exist.

#### Issue: Dependency Conflicts

**Solution**: Use conda environment to isolate dependencies:

```bash
conda env create -f environment.yml
conda activate opentryon
```

### Getting Help

If you encounter issues:

1. Check the [Troubleshooting Guide](../advanced/troubleshooting.md)
2. Search [GitHub Issues](https://github.com/tryonlabs/opentryon/issues)
3. Ask on [Discord](https://discord.gg/T5mPpZHxkY)

## Next Steps

Once installed:

1. **[Quick Start Guide](quickstart.md)**: First CLI / Python runs
2. **[MCP Server](mcp)**: Expose every registry model as tools for Cursor, Claude, or Studio
3. **[TryOn Studio](tryon-studio)**: Next.js UI — Agent chat, Connect, Image, VTON, Understand, Video, BG Remove
4. **[Configuration Guide](configuration.md)**: Set up environment variables and API keys
5. **[Unified CLI](cli)**: `opentryon <service> --model <model>`
6. **[API Reference](../api-reference/overview)**: Cloud adapters
7. **[Datasets Module](../datasets/overview)**: Fashion-MNIST, VITON-HD, Subjects200K
8. **[Preprocessing](../preprocessing/overview)**: Garments, models, and images for virtual try-on

### Key Features to Explore

- **🔌 API Integrations**: Use cloud-based services without local model setup
  - Segmind Try-On Diffusion
  - Kling AI Virtual Try-On
  - Amazon Nova Canvas
  - Nano Banana Image Generation (Google Gemini)
  - FLUX.2 Image Generation (BFL AI)

- **📊 Datasets**: Load and work with fashion datasets
  - Fashion-MNIST (60K examples)
  - VITON-HD (11K+ pairs)
  - Subjects200K (200K paired images)

- **🛠️ Preprocessing**: Process images for virtual try-on
  - Garment segmentation and extraction
  - Human segmentation
  - Pose estimation

