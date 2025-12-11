# OpenTryOn MCP Server

An MCP (Model Context Protocol) server that exposes OpenTryOn's AI-powered fashion tech capabilities to AI agents and applications.

## Overview

This MCP server provides a standardized interface for AI agents to access OpenTryOn's comprehensive suite of virtual try-on, image generation, video generation, and preprocessing tools. It enables seamless integration of fashion tech capabilities into agent workflows.

## Features

The MCP server exposes the following capabilities:

### Virtual Try-On Tools
- **Amazon Nova Canvas**: High-quality virtual try-on using AWS Bedrock
- **Kling AI**: Kolors-based virtual try-on with async processing
- **Segmind**: Try-On Diffusion API integration

### Image Generation Tools
- **Nano Banana**: Fast image generation using Gemini 2.5 Flash (1024px)
- **Nano Banana Pro**: Advanced 4K image generation with Gemini 3 Pro
- **FLUX.2 PRO**: High-quality image generation with standard controls
- **FLUX.2 FLEX**: Flexible generation with advanced controls
- **Luma AI Photon-Flash-1**: Fast and cost-efficient image generation
- **Luma AI Photon-1**: High-fidelity professional-grade image generation

### Video Generation Tools
- **Luma AI Ray 1.6**: Balanced quality video generation
- **Luma AI Ray 2**: High-quality flagship video model
- **Luma AI Ray Flash 2**: Fast, low-latency video generation

### Preprocessing Tools
- **Garment Segmentation**: U2Net-based garment segmentation
- **Garment Extraction**: Extract and preprocess garments
- **Human Segmentation**: Segment human subjects from images

### Dataset Tools
- **Fashion-MNIST**: Load and work with Fashion-MNIST dataset
- **VITON-HD**: Access high-resolution virtual try-on dataset
- **Subjects200K**: Large-scale paired images dataset

## Installation

### Prerequisites

- Python 3.10+
- OpenTryOn installed and configured (see main README.md)
- Required API keys configured in `.env` file

### Install Dependencies

```bash
cd mcp-server
pip install -r requirements.txt
```

### Environment Variables

Ensure your `.env` file in the project root contains the necessary API keys:

```env
# AWS Credentials (for Amazon Nova Canvas)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AMAZON_NOVA_REGION=us-east-1

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

### Starting the MCP Server

```bash
# Start the server with default settings
python server.py

# Start with custom host and port
python server.py --host 0.0.0.0 --port 8080

# Enable debug mode
python server.py --debug
```

### Using with Claude Desktop

Add the following to your Claude Desktop configuration:

**MacOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

**Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "opentryon": {
      "command": "python",
      "args": ["/path/to/opentryon/mcp-server/server.py"],
      "env": {
        "PYTHONPATH": "/path/to/opentryon"
      }
    }
  }
}
```

### Using with Other MCP Clients

The server implements the standard MCP protocol and can be used with any MCP-compatible client. Connect to the server using stdio transport.

## Available Tools

### Virtual Try-On

#### `virtual_tryon_nova`
Generate virtual try-on using Amazon Nova Canvas.

**Parameters:**
- `source_image` (string): Path/URL to person image
- `reference_image` (string): Path/URL to garment image
- `mask_type` (string, optional): "GARMENT" or "IMAGE"
- `garment_class` (string, optional): "UPPER_BODY", "LOWER_BODY", "FULL_BODY", "FOOTWEAR"
- `region` (string, optional): AWS region

#### `virtual_tryon_kling`
Generate virtual try-on using Kling AI.

**Parameters:**
- `source_image` (string): Path/URL to person image
- `reference_image` (string): Path/URL to garment image
- `model` (string, optional): Model version

#### `virtual_tryon_segmind`
Generate virtual try-on using Segmind.

**Parameters:**
- `model_image` (string): Path/URL to person image
- `cloth_image` (string): Path/URL to garment image
- `category` (string): "Upper body", "Lower body", or "Dress"
- `num_inference_steps` (integer, optional): 20-100
- `guidance_scale` (number, optional): 1-25
- `seed` (integer, optional): Random seed

### Image Generation

#### `generate_image_nano_banana`
Generate images using Nano Banana (Gemini 2.5 Flash).

**Parameters:**
- `prompt` (string): Text description
- `aspect_ratio` (string, optional): e.g., "16:9", "1:1"
- `mode` (string, optional): "text_to_image", "edit", "compose"
- `image` (string, optional): Input image for edit mode
- `images` (array, optional): Input images for compose mode

#### `generate_image_nano_banana_pro`
Generate high-resolution images using Nano Banana Pro (Gemini 3 Pro).

**Parameters:**
- `prompt` (string): Text description
- `resolution` (string, optional): "1K", "2K", or "4K"
- `aspect_ratio` (string, optional): e.g., "16:9", "1:1"
- `use_search_grounding` (boolean, optional): Enable Google Search grounding

#### `generate_image_flux2_pro`
Generate images using FLUX.2 PRO.

**Parameters:**
- `prompt` (string): Text description
- `width` (integer, optional): Image width
- `height` (integer, optional): Image height
- `seed` (integer, optional): Random seed

#### `generate_image_flux2_flex`
Generate images using FLUX.2 FLEX with advanced controls.

**Parameters:**
- `prompt` (string): Text description
- `width` (integer, optional): Image width
- `height` (integer, optional): Image height
- `guidance` (number, optional): Guidance scale (1.5-10)
- `steps` (integer, optional): Number of steps
- `prompt_upsampling` (boolean, optional): Enable prompt enhancement

#### `generate_image_luma_photon_flash`
Generate images using Luma AI Photon-Flash-1.

**Parameters:**
- `prompt` (string): Text description
- `aspect_ratio` (string, optional): e.g., "16:9", "1:1"
- `mode` (string, optional): "text_to_image", "img_ref", "style_ref", "char_ref", "modify"

#### `generate_image_luma_photon`
Generate images using Luma AI Photon-1.

**Parameters:**
- `prompt` (string): Text description
- `aspect_ratio` (string, optional): e.g., "16:9", "1:1"
- `mode` (string, optional): "text_to_image", "img_ref", "style_ref", "char_ref", "modify"

### Video Generation

#### `generate_video_luma_ray`
Generate videos using Luma AI Ray models.

**Parameters:**
- `prompt` (string): Text description
- `model` (string): "ray-1-6", "ray-2", or "ray-flash-2"
- `mode` (string): "text_video" or "image_video"
- `resolution` (string, optional): "540p", "720p", "1080p", or "4k"
- `duration` (string, optional): "5s", "9s", or "10s"
- `aspect_ratio` (string, optional): e.g., "16:9", "1:1"
- `start_image` (string, optional): Start keyframe for image_video mode
- `end_image` (string, optional): End keyframe for image_video mode
- `loop` (boolean, optional): Enable seamless looping

### Preprocessing

#### `segment_garment`
Segment garments from images using U2Net.

**Parameters:**
- `input_path` (string): Path to input image or directory
- `output_dir` (string): Output directory
- `garment_class` (string): "upper", "lower", or "all"

#### `extract_garment`
Extract and preprocess garments.

**Parameters:**
- `input_path` (string): Path to input image or directory
- `output_dir` (string): Output directory
- `garment_class` (string): "upper", "lower", or "all"
- `resize_width` (integer, optional): Target width

#### `segment_human`
Segment human subjects from images.

**Parameters:**
- `image_path` (string): Path to input image
- `output_dir` (string): Output directory

### Dataset Tools

#### `load_fashion_mnist`
Load Fashion-MNIST dataset.

**Parameters:**
- `download` (boolean, optional): Download if not present
- `normalize` (boolean, optional): Normalize images
- `flatten` (boolean, optional): Flatten images

#### `load_viton_hd`
Load VITON-HD dataset.

**Parameters:**
- `data_dir` (string): Dataset directory
- `split` (string): "train" or "test"
- `batch_size` (integer, optional): Batch size for DataLoader

## Architecture

```
mcp-server/
├── server.py              # Main MCP server implementation
├── tools/                 # Tool implementations
│   ├── __init__.py
│   ├── virtual_tryon.py   # Virtual try-on tools
│   ├── image_gen.py       # Image generation tools
│   ├── video_gen.py       # Video generation tools
│   ├── preprocessing.py   # Preprocessing tools
│   └── datasets.py        # Dataset tools
├── utils/                 # Utility functions
│   ├── __init__.py
│   ├── image_utils.py     # Image handling utilities
│   └── validation.py      # Input validation
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Development

### Adding New Tools

1. Create a new tool function in the appropriate module under `tools/`
2. Add the tool definition to `server.py`
3. Implement input validation and error handling
4. Update this README with tool documentation

### Testing

```bash
# Run tests
python -m pytest tests/

# Test individual tool
python -m pytest tests/test_virtual_tryon.py -v
```

## Error Handling

The server implements comprehensive error handling:
- Input validation errors return clear messages
- API errors are caught and reported
- File I/O errors are handled gracefully
- All errors include context for debugging

## Performance Considerations

- Image processing is done asynchronously when possible
- Large files are streamed rather than loaded into memory
- Results are cached when appropriate
- Connection pooling for API requests

## Security

- API keys are never exposed in responses
- Input paths are validated to prevent directory traversal
- File uploads are sanitized
- Rate limiting can be configured

## Troubleshooting

### Server won't start
- Check Python version (3.10+ required)
- Verify all dependencies are installed
- Ensure OpenTryOn is properly installed

### API errors
- Verify API keys in `.env` file
- Check network connectivity
- Ensure API quotas are not exceeded

### Image processing errors
- Verify input image formats (JPG, PNG)
- Check image size limits
- Ensure sufficient disk space

## Documentation

For more detailed information, see the documentation in the `docs/` folder:

- **[Quick Start Guide](docs/QUICKSTART.md)** - Get started in 5 minutes
- **[Installation Guide](docs/INSTALL.md)** - Detailed installation instructions
- **[Architecture](docs/ARCHITECTURE.md)** - Technical deep dive into the server architecture
- **[Project Summary](docs/SUMMARY.md)** - Comprehensive project overview
- **[Project Overview](docs/PROJECT_OVERVIEW.md)** - Visual overview with tables and statistics

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

This MCP server is part of OpenTryOn and follows the same license (CC BY-NC 4.0).

## Support

- GitHub Issues: [OpenTryOn Issues](https://github.com/tryonlabs/opentryon/issues)
- Discord: [Join our Discord](https://discord.gg/T5mPpZHxkY)
- Documentation: [OpenTryOn Docs](https://tryonlabs.github.io/opentryon/)

---

Made with ❤️ by [TryOn Labs](https://www.tryonlabs.ai)

