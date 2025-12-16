# OpenTryOn MCP Server

An MCP (Model Context Protocol) server that exposes OpenTryOn's AI-powered fashion tech capabilities to AI agents and applications.

## Overview

The OpenTryOn MCP Server provides a standardized interface for AI agents to access:
- **Virtual Try-On** (3 providers): Amazon Nova Canvas, Kling AI, Segmind
- **Image Generation** (6 models): Gemini, FLUX.2, Luma AI
- **Video Generation**: Luma AI Ray models
- **Preprocessing Tools**: Garment segmentation, extraction, human parsing
- **Datasets**: Fashion-MNIST, VITON-HD

**Total**: 17 tools across 5 categories

## Quick Start

### Prerequisites
- Python 3.10+
- OpenTryOn installed
- At least one API key configured

### Installation

```bash
# 1. Install OpenTryOn core library
cd /path/to/opentryon
pip install -e .

# 2. Install MCP server dependencies
cd mcp-server
pip install -r requirements.txt

# 3. Configure API keys
cp ../env.template ../.env
# Edit .env with your API keys

# 4. Test installation
python test_server.py

# 5. Start server
python server.py
```

### Minimum Configuration

You don't need all API keys. Start with just these:

```env
# In .env file:
KLING_AI_API_KEY=your_key
KLING_AI_SECRET_KEY=your_secret
GEMINI_API_KEY=your_key
```

This gives you:
- ✓ Virtual try-on (Kling AI)
- ✓ Image generation (Gemini)
- ✓ All preprocessing and dataset tools

## Configuration

### Configuration Status

When you start the MCP server, it shows which services are configured:

```
OpenTryOn MCP Server Configuration Status:
  Amazon Nova Canvas: ✗ Not configured (optional - requires AWS)
  Kling AI: ✓ Configured
  Segmind: ✓ Configured
  Gemini (Nano Banana): ✓ Configured
  FLUX.2: ✓ Configured
  Luma AI: ✗ Not configured (optional - for video)
  U2Net (Preprocessing): ✗ Not configured (optional - for local segmentation)

✅ Ready! At least one service from each category is configured.
```

### Required vs Optional Services

**Minimum Required** (choose at least ONE from each):
- **Virtual Try-On**: Kling AI OR Segmind (recommended)
- **Image Generation**: Gemini OR FLUX.2 (recommended)

**Optional Services**:
- **Amazon Nova Canvas**: Only if you want AWS Bedrock (requires AWS account)
- **Luma AI**: Only for video generation and Luma image models
- **U2Net**: Only for local garment preprocessing

### Getting API Keys

| Service | URL | Cost | Notes |
|---------|-----|------|-------|
| **Kling AI** | [klingai.com](https://klingai.com/) | Pay-per-use | Best VTON quality |
| **Segmind** | [segmind.com](https://segmind.com/) | Pay-per-use | Fast VTON |
| **Gemini** | [ai.google.dev](https://ai.google.dev/) | Free tier | Good for testing |
| **FLUX.2** | [api.bfl.ml](https://api.bfl.ml/) | Pay-per-use | High quality |
| **Luma AI** | [lumalabs.ai](https://lumalabs.ai/) | Pay-per-use | For video |
| **AWS Bedrock** | [aws.amazon.com/bedrock](https://aws.amazon.com/bedrock/) | Pay-per-use | Requires AWS |

### Complete Configuration

For full functionality, add all services to `.env`:

```env
# Virtual Try-On
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AMAZON_NOVA_REGION=us-east-1

KLING_AI_API_KEY=your_key
KLING_AI_SECRET_KEY=your_secret
KLING_AI_BASE_URL=https://api-singapore.klingai.com

SEGMIND_API_KEY=your_key

# Image Generation
GEMINI_API_KEY=your_key
BFL_API_KEY=your_key
LUMA_AI_API_KEY=your_key

# Preprocessing (optional)
U2NET_CLOTH_SEG_CHECKPOINT_PATH=/path/to/cloth_segm_u2net_latest.pth
```

## Integration Options

### Option 1: Claude Desktop

Add to `claude_desktop_config.json`:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "opentryon": {
      "command": "python",
      "args": ["/absolute/path/to/opentryon/mcp-server/server.py"],
      "env": {
        "PYTHONPATH": "/absolute/path/to/opentryon"
      }
    }
  }
}
```

Then restart Claude Desktop and start using OpenTryOn tools!

### Option 2: Standalone Server

```bash
cd mcp-server
python server.py
```

The server listens for MCP protocol messages via stdio.

### Option 3: Programmatic Usage

```python
from tools import virtual_tryon_nova, generate_image_nano_banana

# Virtual try-on
result = virtual_tryon_nova(
    source_image="person.jpg",
    reference_image="garment.jpg",
    output_dir="outputs"
)

# Image generation
result = generate_image_nano_banana(
    prompt="A fashion model in elegant evening wear",
    aspect_ratio="16:9",
    output_dir="outputs"
)
```

## Available Tools

### Virtual Try-On (3 tools)

#### `virtual_tryon_nova`
Amazon Nova Canvas virtual try-on using AWS Bedrock.

```python
virtual_tryon_nova(
    source_image="person.jpg",        # Person/model image
    reference_image="garment.jpg",    # Garment image
    mask_type="GARMENT",              # GARMENT or IMAGE
    garment_class="UPPER_BODY",       # UPPER_BODY, LOWER_BODY, FULL_BODY, FOOTWEAR
    output_dir="outputs/nova"
)
```

#### `virtual_tryon_kling`
Kling AI Kolors-based virtual try-on.

```python
virtual_tryon_kling(
    source_image="person.jpg",
    reference_image="garment.jpg",
    output_dir="outputs/kling"
)
```

#### `virtual_tryon_segmind`
Segmind Try-On Diffusion.

```python
virtual_tryon_segmind(
    model_image="person.jpg",
    cloth_image="garment.jpg",
    category="Upper body",            # "Upper body", "Lower body", "Dress"
    num_inference_steps=25,           # 20-100
    guidance_scale=2.0,               # 1-25
    output_dir="outputs/segmind"
)
```

### Image Generation (6 tools)

#### `generate_image_nano_banana`
Fast 1024px image generation with Gemini 2.5 Flash.

```python
generate_image_nano_banana(
    prompt="A fashion model in elegant evening wear",
    aspect_ratio="16:9",              # 1:1, 2:3, 3:2, 4:3, 9:16, 16:9, etc.
    mode="text_to_image",             # text_to_image, edit, compose
    output_dir="outputs"
)
```

#### `generate_image_nano_banana_pro`
4K image generation with Gemini 3 Pro.

```python
generate_image_nano_banana_pro(
    prompt="Professional fashion photography",
    resolution="4K",                  # 1K, 2K, 4K
    aspect_ratio="16:9",
    use_search_grounding=True,        # Enable Google Search grounding
    output_dir="outputs"
)
```

#### `generate_image_flux2_pro`
High-quality image generation with FLUX.2 PRO.

```python
generate_image_flux2_pro(
    prompt="A stylish fashion model",
    width=1024,
    height=1024,
    seed=42,                          # Optional: for reproducibility
    mode="text_to_image",             # text_to_image, edit, compose
    output_dir="outputs"
)
```

#### `generate_image_flux2_flex`
Flexible generation with advanced controls.

```python
generate_image_flux2_flex(
    prompt="Fashion model in casual wear",
    width=1024,
    height=1024,
    guidance=7.5,                     # 1.5-10
    steps=28,                         # Number of inference steps
    prompt_upsampling=False,          # Enable prompt enhancement
    output_dir="outputs"
)
```

#### `generate_image_luma_photon_flash`
Fast and cost-efficient with Luma AI Photon-Flash-1.

```python
generate_image_luma_photon_flash(
    prompt="A model in a studio setting",
    aspect_ratio="16:9",
    mode="text_to_image",             # text_to_image, img_ref, style_ref, char_ref
    output_dir="outputs"
)
```

#### `generate_image_luma_photon`
High-fidelity professional-grade with Luma AI Photon-1.

```python
generate_image_luma_photon(
    prompt="Professional fashion shoot",
    aspect_ratio="16:9",
    mode="text_to_image",
    output_dir="outputs"
)
```

### Video Generation (1 tool)

#### `generate_video_luma_ray`
Video generation with Luma AI Ray models.

```python
generate_video_luma_ray(
    prompt="A model walking on a runway",
    model="ray-2",                    # ray-1-6, ray-2, ray-flash-2
    mode="text_video",                # text_video, image_video
    resolution="720p",                # 540p, 720p, 1080p, 4k
    duration="5s",                    # 5s, 9s, 10s
    aspect_ratio="16:9",
    output_dir="outputs/videos"
)
```

### Preprocessing (3 tools)

#### `segment_garment`
Segment garments using U2Net.

```python
segment_garment(
    input_path="garment_images/",
    output_dir="outputs/segmented",
    garment_class="upper"             # upper, lower, all
)
```

#### `extract_garment`
Extract and preprocess garments.

```python
extract_garment(
    input_path="garment_images/",
    output_dir="outputs/extracted",
    garment_class="upper",
    resize_width=400
)
```

#### `segment_human`
Segment human subjects from images.

```python
segment_human(
    image_path="person.jpg",
    output_dir="outputs/segmented"
)
```

### Datasets (2 tools)

#### `load_fashion_mnist`
Load Fashion-MNIST dataset (60K training, 10K test).

```python
load_fashion_mnist(
    download=True,
    normalize=True,
    flatten=False
)
```

#### `load_viton_hd`
Load VITON-HD dataset (11,647 training, 2,032 test).

```python
load_viton_hd(
    data_dir="/path/to/viton-hd",
    split="train",                    # train, test
    batch_size=8
)
```

## Architecture

```
┌─────────────────────────────────────────┐
│         MCP Clients (Claude, etc)       │
└──────────────┬──────────────────────────┘
               │ MCP Protocol (stdio)
┌──────────────▼──────────────────────────┐
│       OpenTryOn MCP Server              │
│  ┌───────────────────────────────────┐  │
│  │  Tool Router (server.py)          │  │
│  └──────┬─────────────┬──────────────┘  │
│         │             │                  │
│  ┌──────▼──────┐ ┌───▼───────┐         │
│  │   Tools     │ │  Config   │         │
│  │  - VTON     │ │  - API    │         │
│  │  - Image    │ │    Keys   │         │
│  │  - Video    │ │  - Env    │         │
│  │  - Process  │ │    Vars   │         │
│  │  - Dataset  │ └───────────┘         │
│  └─────────────┘                        │
└─────────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│     OpenTryOn Core Library              │
│  (tryon.api, tryon.preprocessing, etc)  │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  External APIs & Models                 │
│  AWS, Kling, Segmind, Gemini,          │
│  FLUX.2, Luma AI, U2Net                │
└─────────────────────────────────────────┘
```

### Key Components

1. **Server Core** (`server.py`): Implements MCP protocol, registers tools, routes requests
2. **Tools** (`tools/`): Implements tool logic for each feature
3. **Config** (`config.py`): Manages API keys and environment variables
4. **Utils** (`utils/`): Image handling and validation utilities

### Data Flow Example (Virtual Try-On)

```
1. Client sends request via MCP
2. Server validates request format
3. Router identifies tool (virtual_tryon_nova)
4. Tool validates inputs
5. Tool calls OpenTryOn API adapter
6. Adapter calls external API (AWS Bedrock)
7. API returns generated images
8. Tool saves images to disk
9. Tool returns structured response
10. Server formats and sends to client
```

## Troubleshooting

### Server won't start

**Problem**: `ModuleNotFoundError: No module named 'mcp'`

**Solution**:
```bash
pip install -r requirements.txt
```

### API errors

**Problem**: `Error: API key not configured`

**Solution**:
1. Check `.env` file exists in OpenTryOn root
2. Verify API keys are set correctly
3. Ensure no extra spaces or quotes
4. Restart server after updating `.env`

### Import errors

**Problem**: `ModuleNotFoundError: No module named 'tryon'`

**Solution**:
```bash
cd /path/to/opentryon
pip install -e .
```

### Tool execution fails

**Solutions**:
1. Verify API key is valid and has credits
2. Check network connectivity
3. Verify input file paths exist
4. Check API service status
5. Review server logs for errors

### Configuration validation

Run the test suite to check configuration:
```bash
python test_server.py
```

This validates:
- Directory structure
- Configuration loading
- Module imports
- OpenTryOn library
- Tool definitions

## Project Structure

```
mcp-server/
├── server.py                 # Main MCP server (700+ lines)
├── config.py                 # Configuration management
├── requirements.txt          # Dependencies
├── pyproject.toml           # Package config
├── test_server.py           # Test suite
│
├── tools/                   # Tool implementations
│   ├── virtual_tryon.py     # 3 virtual try-on tools
│   ├── image_gen.py         # 6 image generation tools
│   ├── video_gen.py         # 1 video generation tool
│   ├── preprocessing.py     # 3 preprocessing tools
│   └── datasets.py          # 2 dataset tools
│
├── utils/                   # Utilities
│   ├── image_utils.py       # Image handling
│   └── validation.py        # Input validation
│
└── examples/                # Usage examples
    ├── example_usage.py
    └── claude_desktop_config.json
```

## Security

The MCP server implements security best practices:

- ✅ **API Keys**: Stored in environment variables, never exposed
- ✅ **Path Validation**: Prevents directory traversal attacks
- ✅ **Input Sanitization**: Validates all inputs
- ✅ **File Size Limits**: Prevents resource exhaustion
- ✅ **Temp File Cleanup**: Automatic cleanup of temporary files

## Testing

Run the comprehensive test suite:

```bash
python test_server.py
```

Tests validate:
- Configuration loading
- Module imports
- Tool definitions
- Directory structure
- OpenTryOn library integration

## Examples

See `examples/example_usage.py` for complete examples of:
- Virtual try-on with all providers
- Image generation with all models
- Video generation
- Preprocessing tools
- Dataset loading

## Support

- **Issues**: [GitHub Issues](https://github.com/tryonlabs/opentryon/issues)
- **Discord**: [Join our Discord](https://discord.gg/T5mPpZHxkY)
- **Documentation**: [OpenTryOn Docs](https://tryonlabs.github.io/opentryon/)
- **Email**: contact@tryonlabs.ai

## Contributing

Contributions are welcome! Areas to contribute:
1. Add support for new API providers
2. Improve documentation
3. Add more test coverage
4. Fix bugs
5. Implement new features

## License

Part of OpenTryOn - Creative Commons BY-NC 4.0

See main [LICENSE](../LICENSE) file for details.

## Version

**v0.0.1** - First public release

---

Made with ❤️ by [TryOn Labs](https://www.tryonlabs.ai)
