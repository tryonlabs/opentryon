# OpenTryOn MCP Server - Quick Start Guide

Get started with the OpenTryOn MCP Server in minutes!

## Prerequisites

1. **Python 3.10+** installed
2. **OpenTryOn** installed and configured (see main [README.md](../README.md))
3. **API Keys** configured in `.env` file (in the parent directory)

## Installation

### Step 1: Install OpenTryOn

If you haven't already, install OpenTryOn:

```bash
cd /path/to/opentryon
pip install -e .
```

### Step 2: Install MCP Server Dependencies

```bash
cd mcp-server
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables

Ensure your `.env` file in the OpenTryOn root directory contains the necessary API keys:

```env
# AWS Credentials (for Amazon Nova Canvas)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# Kling AI
KLING_AI_API_KEY=your_kling_api_key
KLING_AI_SECRET_KEY=your_kling_secret_key

# Segmind
SEGMIND_API_KEY=your_segmind_api_key

# Google Gemini (Nano Banana)
GEMINI_API_KEY=your_gemini_api_key

# BFL API (FLUX.2)
BFL_API_KEY=your_bfl_api_key

# Luma AI
LUMA_AI_API_KEY=your_luma_ai_api_key

# U2Net Checkpoint
U2NET_CLOTH_SEG_CHECKPOINT_PATH=cloth_segm.pth
```

## Usage

### Option 1: Use with Claude Desktop

1. **Locate your Claude Desktop config file:**
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

2. **Add OpenTryOn MCP Server:**

```json
{
  "mcpServers": {
    "opentryon": {
      "command": "python",
      "args": [
        "/absolute/path/to/opentryon/mcp-server/server.py"
      ],
      "env": {
        "PYTHONPATH": "/absolute/path/to/opentryon"
      }
    }
  }
}
```

3. **Restart Claude Desktop**

4. **Start using OpenTryOn tools in Claude!**

Example prompts:
- "Generate a virtual try-on using Amazon Nova Canvas with this person image and garment image"
- "Create a 4K fashion image using Nano Banana Pro"
- "Generate a video of a model walking on a runway"

### Option 2: Run Standalone

You can also run the server directly:

```bash
cd mcp-server
python server.py
```

The server will start and listen for MCP protocol messages via stdio.

### Option 3: Use Programmatically

Import and use the tools directly in your Python code:

```python
from tools import virtual_tryon_nova, generate_image_nano_banana

# Virtual try-on
result = virtual_tryon_nova(
    source_image="person.jpg",
    reference_image="garment.jpg",
    garment_class="UPPER_BODY",
    output_dir="outputs"
)
print(result)

# Image generation
result = generate_image_nano_banana(
    prompt="A fashion model in elegant evening wear",
    aspect_ratio="16:9",
    output_dir="outputs"
)
print(result)
```

## Available Tools

The MCP server exposes 17 tools across 5 categories:

### 1. Virtual Try-On (3 tools)
- `virtual_tryon_nova` - Amazon Nova Canvas
- `virtual_tryon_kling` - Kling AI
- `virtual_tryon_segmind` - Segmind Try-On Diffusion

### 2. Image Generation (6 tools)
- `generate_image_nano_banana` - Gemini 2.5 Flash (1024px)
- `generate_image_nano_banana_pro` - Gemini 3 Pro (up to 4K)
- `generate_image_flux2_pro` - FLUX.2 PRO
- `generate_image_flux2_flex` - FLUX.2 FLEX
- `generate_image_luma_photon_flash` - Luma AI Photon-Flash-1
- `generate_image_luma_photon` - Luma AI Photon-1

### 3. Video Generation (1 tool)
- `generate_video_luma_ray` - Luma AI Ray models

### 4. Preprocessing (3 tools)
- `segment_garment` - Segment garments using U2Net
- `extract_garment` - Extract and preprocess garments
- `segment_human` - Segment human subjects

### 5. Datasets (2 tools)
- `load_fashion_mnist` - Load Fashion-MNIST dataset
- `load_viton_hd` - Load VITON-HD dataset

## Example Usage

### Virtual Try-On with Amazon Nova Canvas

```python
from tools import virtual_tryon_nova

result = virtual_tryon_nova(
    source_image="data/person.jpg",
    reference_image="data/garment.jpg",
    mask_type="GARMENT",
    garment_class="UPPER_BODY",
    output_dir="outputs/nova"
)

if result["success"]:
    print(f"Generated {result['num_images']} images")
    print(f"Saved to: {result['output_paths']}")
else:
    print(f"Error: {result['error']}")
```

### Image Generation with FLUX.2 PRO

```python
from tools import generate_image_flux2_pro

result = generate_image_flux2_pro(
    prompt="A professional fashion model wearing elegant evening wear",
    width=1024,
    height=1024,
    seed=42,
    output_dir="outputs/flux2"
)

if result["success"]:
    print(f"Generated {result['num_images']} images")
    print(f"Saved to: {result['output_paths']}")
```

### Video Generation with Luma AI

```python
from tools import generate_video_luma_ray

result = generate_video_luma_ray(
    prompt="A fashion model walking on a runway",
    model="ray-2",
    mode="text_video",
    resolution="720p",
    duration="5s",
    aspect_ratio="16:9",
    output_dir="outputs/videos"
)

if result["success"]:
    print(f"Video saved to: {result['output_path']}")
```

## Troubleshooting

### Server won't start

**Problem**: `ModuleNotFoundError: No module named 'mcp'`

**Solution**: Install MCP server dependencies:
```bash
pip install -r requirements.txt
```

### API errors

**Problem**: `Error: API key not configured`

**Solution**: Check your `.env` file and ensure API keys are set correctly.

### Import errors

**Problem**: `ModuleNotFoundError: No module named 'tryon'`

**Solution**: Ensure OpenTryOn is installed and PYTHONPATH is set:
```bash
cd /path/to/opentryon
pip install -e .
```

### Tool execution fails

**Problem**: Tool returns error with specific API

**Solution**: 
1. Verify API key is valid and has sufficient credits
2. Check network connectivity
3. Verify input file paths exist
4. Check API service status

## Next Steps

- Read the full [README.md](../README.md) for detailed documentation
- Explore [examples/example_usage.py](../examples/example_usage.py) for more examples
- Check the main [OpenTryOn documentation](https://tryonlabs.github.io/opentryon/)
- Join the [Discord community](https://discord.gg/T5mPpZHxkY) for support

## Support

- **Issues**: [GitHub Issues](https://github.com/tryonlabs/opentryon/issues)
- **Discord**: [Join our Discord](https://discord.gg/T5mPpZHxkY)
- **Documentation**: [OpenTryOn Docs](https://tryonlabs.github.io/opentryon/)

---

Made with ❤️ by [TryOn Labs](https://www.tryonlabs.ai)

