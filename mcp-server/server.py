#!/usr/bin/env python3
"""OpenTryOn MCP Server - Main server implementation."""

import asyncio
import json
import sys
from typing import Any, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

from config import config
from tools import (
    virtual_tryon_nova,
    virtual_tryon_kling,
    virtual_tryon_segmind,
    generate_image_nano_banana,
    generate_image_nano_banana_pro,
    generate_image_flux2_pro,
    generate_image_flux2_flex,
    generate_image_luma_photon_flash,
    generate_image_luma_photon,
    generate_video_luma_ray,
    segment_garment,
    extract_garment,
    segment_human,
    load_fashion_mnist,
    load_viton_hd,
)


# Initialize MCP server
app = Server("opentryon-mcp")


# Define available tools
TOOLS = [
    # Virtual Try-On Tools
    Tool(
        name="virtual_tryon_nova",
        description="Generate virtual try-on using Amazon Nova Canvas. Combines a person image with a garment image to create realistic try-on results.",
        inputSchema={
            "type": "object",
            "properties": {
                "source_image": {
                    "type": "string",
                    "description": "Path or URL to person/model image"
                },
                "reference_image": {
                    "type": "string",
                    "description": "Path or URL to garment/product image"
                },
                "mask_type": {
                    "type": "string",
                    "enum": ["GARMENT", "IMAGE"],
                    "description": "Type of mask to use",
                    "default": "GARMENT"
                },
                "garment_class": {
                    "type": "string",
                    "enum": ["UPPER_BODY", "LOWER_BODY", "FULL_BODY", "FOOTWEAR"],
                    "description": "Garment class for automatic masking",
                    "default": "UPPER_BODY"
                },
                "region": {
                    "type": "string",
                    "description": "AWS region (optional)",
                },
                "output_dir": {
                    "type": "string",
                    "description": "Directory to save results (optional)"
                }
            },
            "required": ["source_image", "reference_image"]
        }
    ),
    Tool(
        name="virtual_tryon_kling",
        description="Generate virtual try-on using Kling AI's Kolors API. Fast and high-quality virtual try-on with automatic task polling.",
        inputSchema={
            "type": "object",
            "properties": {
                "source_image": {
                    "type": "string",
                    "description": "Path or URL to person/model image"
                },
                "reference_image": {
                    "type": "string",
                    "description": "Path or URL to garment/product image"
                },
                "model": {
                    "type": "string",
                    "description": "Model version (optional)"
                },
                "output_dir": {
                    "type": "string",
                    "description": "Directory to save results (optional)"
                }
            },
            "required": ["source_image", "reference_image"]
        }
    ),
    Tool(
        name="virtual_tryon_segmind",
        description="Generate virtual try-on using Segmind's Try-On Diffusion API. Supports upper body, lower body, and dress categories.",
        inputSchema={
            "type": "object",
            "properties": {
                "model_image": {
                    "type": "string",
                    "description": "Path or URL to person/model image"
                },
                "cloth_image": {
                    "type": "string",
                    "description": "Path or URL to garment/cloth image"
                },
                "category": {
                    "type": "string",
                    "enum": ["Upper body", "Lower body", "Dress"],
                    "description": "Garment category",
                    "default": "Upper body"
                },
                "num_inference_steps": {
                    "type": "integer",
                    "minimum": 20,
                    "maximum": 100,
                    "description": "Number of denoising steps",
                    "default": 25
                },
                "guidance_scale": {
                    "type": "number",
                    "minimum": 1,
                    "maximum": 25,
                    "description": "Classifier-free guidance scale",
                    "default": 2.0
                },
                "seed": {
                    "type": "integer",
                    "description": "Random seed (-1 for random)",
                    "default": -1
                },
                "output_dir": {
                    "type": "string",
                    "description": "Directory to save results (optional)"
                }
            },
            "required": ["model_image", "cloth_image"]
        }
    ),
    
    # Image Generation Tools
    Tool(
        name="generate_image_nano_banana",
        description="Generate images using Nano Banana (Gemini 2.5 Flash). Fast 1024px image generation with text-to-image, editing, and composition modes.",
        inputSchema={
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "Text description for image generation"
                },
                "aspect_ratio": {
                    "type": "string",
                    "enum": ["1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"],
                    "description": "Image aspect ratio",
                    "default": "1:1"
                },
                "mode": {
                    "type": "string",
                    "enum": ["text_to_image", "edit", "compose"],
                    "description": "Generation mode",
                    "default": "text_to_image"
                },
                "image": {
                    "type": "string",
                    "description": "Input image for edit mode (optional)"
                },
                "images": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Input images for compose mode (optional)"
                },
                "output_dir": {
                    "type": "string",
                    "description": "Directory to save results (optional)"
                }
            },
            "required": ["prompt"]
        }
    ),
    Tool(
        name="generate_image_nano_banana_pro",
        description="Generate high-resolution images using Nano Banana Pro (Gemini 3 Pro). Advanced 4K image generation with search grounding.",
        inputSchema={
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "Text description for image generation"
                },
                "resolution": {
                    "type": "string",
                    "enum": ["1K", "2K", "4K"],
                    "description": "Image resolution",
                    "default": "1K"
                },
                "aspect_ratio": {
                    "type": "string",
                    "enum": ["1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"],
                    "description": "Image aspect ratio",
                    "default": "1:1"
                },
                "use_search_grounding": {
                    "type": "boolean",
                    "description": "Enable Google Search grounding",
                    "default": False
                },
                "mode": {
                    "type": "string",
                    "enum": ["text_to_image", "edit"],
                    "description": "Generation mode",
                    "default": "text_to_image"
                },
                "image": {
                    "type": "string",
                    "description": "Input image for edit mode (optional)"
                },
                "output_dir": {
                    "type": "string",
                    "description": "Directory to save results (optional)"
                }
            },
            "required": ["prompt"]
        }
    ),
    Tool(
        name="generate_image_flux2_pro",
        description="Generate images using FLUX.2 PRO. High-quality image generation with text-to-image, editing, and multi-image composition.",
        inputSchema={
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "Text description for image generation"
                },
                "width": {
                    "type": "integer",
                    "minimum": 64,
                    "description": "Image width in pixels",
                    "default": 1024
                },
                "height": {
                    "type": "integer",
                    "minimum": 64,
                    "description": "Image height in pixels",
                    "default": 1024
                },
                "seed": {
                    "type": "integer",
                    "description": "Random seed for reproducibility (optional)"
                },
                "mode": {
                    "type": "string",
                    "enum": ["text_to_image", "edit", "compose"],
                    "description": "Generation mode",
                    "default": "text_to_image"
                },
                "input_image": {
                    "type": "string",
                    "description": "Input image for edit mode (optional)"
                },
                "images": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Input images for compose mode (optional)"
                },
                "output_dir": {
                    "type": "string",
                    "description": "Directory to save results (optional)"
                }
            },
            "required": ["prompt"]
        }
    ),
    Tool(
        name="generate_image_flux2_flex",
        description="Generate images using FLUX.2 FLEX. Flexible generation with advanced controls including guidance scale, steps, and prompt upsampling.",
        inputSchema={
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "Text description for image generation"
                },
                "width": {
                    "type": "integer",
                    "minimum": 64,
                    "description": "Image width in pixels",
                    "default": 1024
                },
                "height": {
                    "type": "integer",
                    "minimum": 64,
                    "description": "Image height in pixels",
                    "default": 1024
                },
                "guidance": {
                    "type": "number",
                    "minimum": 1.5,
                    "maximum": 10,
                    "description": "Guidance scale for prompt adherence",
                    "default": 7.5
                },
                "steps": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Number of inference steps",
                    "default": 28
                },
                "prompt_upsampling": {
                    "type": "boolean",
                    "description": "Enable prompt enhancement",
                    "default": False
                },
                "seed": {
                    "type": "integer",
                    "description": "Random seed for reproducibility (optional)"
                },
                "mode": {
                    "type": "string",
                    "enum": ["text_to_image", "edit"],
                    "description": "Generation mode",
                    "default": "text_to_image"
                },
                "input_image": {
                    "type": "string",
                    "description": "Input image for edit mode (optional)"
                },
                "output_dir": {
                    "type": "string",
                    "description": "Directory to save results (optional)"
                }
            },
            "required": ["prompt"]
        }
    ),
    Tool(
        name="generate_image_luma_photon_flash",
        description="Generate images using Luma AI Photon-Flash-1. Fast and cost-efficient image generation with multiple reference modes.",
        inputSchema={
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "Text description for image generation"
                },
                "aspect_ratio": {
                    "type": "string",
                    "enum": ["1:1", "3:4", "4:3", "9:16", "16:9", "21:9", "9:21"],
                    "description": "Image aspect ratio",
                    "default": "1:1"
                },
                "mode": {
                    "type": "string",
                    "enum": ["text_to_image", "img_ref", "style_ref", "char_ref", "modify"],
                    "description": "Generation mode",
                    "default": "text_to_image"
                },
                "images": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Input images for reference/modify modes (optional)"
                },
                "weights": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "Weights for reference images (optional)"
                },
                "char_id": {
                    "type": "string",
                    "description": "Character ID for character reference mode (optional)"
                },
                "char_images": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Character reference images (optional)"
                },
                "output_dir": {
                    "type": "string",
                    "description": "Directory to save results (optional)"
                }
            },
            "required": ["prompt"]
        }
    ),
    Tool(
        name="generate_image_luma_photon",
        description="Generate images using Luma AI Photon-1. High-fidelity professional-grade image generation with multiple reference modes.",
        inputSchema={
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "Text description for image generation"
                },
                "aspect_ratio": {
                    "type": "string",
                    "enum": ["1:1", "3:4", "4:3", "9:16", "16:9", "21:9", "9:21"],
                    "description": "Image aspect ratio",
                    "default": "1:1"
                },
                "mode": {
                    "type": "string",
                    "enum": ["text_to_image", "img_ref", "style_ref", "char_ref", "modify"],
                    "description": "Generation mode",
                    "default": "text_to_image"
                },
                "images": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Input images for reference/modify modes (optional)"
                },
                "weights": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "Weights for reference images (optional)"
                },
                "char_id": {
                    "type": "string",
                    "description": "Character ID for character reference mode (optional)"
                },
                "char_images": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Character reference images (optional)"
                },
                "output_dir": {
                    "type": "string",
                    "description": "Directory to save results (optional)"
                }
            },
            "required": ["prompt"]
        }
    ),
    
    # Video Generation Tools
    Tool(
        name="generate_video_luma_ray",
        description="Generate videos using Luma AI Ray models. Supports text-to-video and image-to-video with keyframe control.",
        inputSchema={
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "Text description for video generation"
                },
                "model": {
                    "type": "string",
                    "enum": ["ray-1-6", "ray-2", "ray-flash-2"],
                    "description": "Ray model version",
                    "default": "ray-2"
                },
                "mode": {
                    "type": "string",
                    "enum": ["text_video", "image_video"],
                    "description": "Generation mode",
                    "default": "text_video"
                },
                "resolution": {
                    "type": "string",
                    "enum": ["540p", "720p", "1080p", "4k"],
                    "description": "Video resolution",
                    "default": "720p"
                },
                "duration": {
                    "type": "string",
                    "enum": ["5s", "9s", "10s"],
                    "description": "Video duration",
                    "default": "5s"
                },
                "aspect_ratio": {
                    "type": "string",
                    "enum": ["1:1", "3:4", "4:3", "9:16", "16:9", "21:9", "9:21"],
                    "description": "Video aspect ratio",
                    "default": "16:9"
                },
                "start_image": {
                    "type": "string",
                    "description": "Start keyframe for image_video mode (optional)"
                },
                "end_image": {
                    "type": "string",
                    "description": "End keyframe for image_video mode (optional)"
                },
                "loop": {
                    "type": "boolean",
                    "description": "Enable seamless looping",
                    "default": False
                },
                "output_dir": {
                    "type": "string",
                    "description": "Directory to save results (optional)"
                }
            },
            "required": ["prompt"]
        }
    ),
    
    # Preprocessing Tools
    Tool(
        name="segment_garment",
        description="Segment garments from images using U2Net. Supports upper body, lower body, or all garments.",
        inputSchema={
            "type": "object",
            "properties": {
                "input_path": {
                    "type": "string",
                    "description": "Path to input image or directory"
                },
                "output_dir": {
                    "type": "string",
                    "description": "Output directory for segmented images"
                },
                "garment_class": {
                    "type": "string",
                    "enum": ["upper", "lower", "all"],
                    "description": "Garment class to segment",
                    "default": "upper"
                }
            },
            "required": ["input_path", "output_dir"]
        }
    ),
    Tool(
        name="extract_garment",
        description="Extract and preprocess garments from images. Includes segmentation and optional resizing.",
        inputSchema={
            "type": "object",
            "properties": {
                "input_path": {
                    "type": "string",
                    "description": "Path to input image or directory"
                },
                "output_dir": {
                    "type": "string",
                    "description": "Output directory for extracted garments"
                },
                "garment_class": {
                    "type": "string",
                    "enum": ["upper", "lower", "all"],
                    "description": "Garment class to extract",
                    "default": "upper"
                },
                "resize_width": {
                    "type": "integer",
                    "description": "Target width for resizing (optional)",
                    "default": 400
                }
            },
            "required": ["input_path", "output_dir"]
        }
    ),
    Tool(
        name="segment_human",
        description="Segment human subjects from images using advanced segmentation models.",
        inputSchema={
            "type": "object",
            "properties": {
                "image_path": {
                    "type": "string",
                    "description": "Path to input image"
                },
                "output_dir": {
                    "type": "string",
                    "description": "Output directory for segmented images"
                }
            },
            "required": ["image_path", "output_dir"]
        }
    ),
    
    # Dataset Tools
    Tool(
        name="load_fashion_mnist",
        description="Load Fashion-MNIST dataset. A dataset of Zalando's article images (60K training, 10K test, 10 classes).",
        inputSchema={
            "type": "object",
            "properties": {
                "download": {
                    "type": "boolean",
                    "description": "Download dataset if not present",
                    "default": True
                },
                "normalize": {
                    "type": "boolean",
                    "description": "Normalize images to [0, 1]",
                    "default": True
                },
                "flatten": {
                    "type": "boolean",
                    "description": "Flatten images to 1D arrays",
                    "default": False
                }
            },
            "required": []
        }
    ),
    Tool(
        name="load_viton_hd",
        description="Load VITON-HD dataset. High-resolution virtual try-on dataset (11,647 training pairs, 2,032 test pairs).",
        inputSchema={
            "type": "object",
            "properties": {
                "data_dir": {
                    "type": "string",
                    "description": "Path to VITON-HD dataset directory"
                },
                "split": {
                    "type": "string",
                    "enum": ["train", "test"],
                    "description": "Dataset split to load",
                    "default": "train"
                },
                "batch_size": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Batch size for DataLoader",
                    "default": 8
                }
            },
            "required": ["data_dir"]
        }
    ),
]


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available tools."""
    return TOOLS


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Execute a tool with given arguments."""
    try:
        # Route to appropriate tool function
        if name == "virtual_tryon_nova":
            result = virtual_tryon_nova(**arguments)
        elif name == "virtual_tryon_kling":
            result = virtual_tryon_kling(**arguments)
        elif name == "virtual_tryon_segmind":
            result = virtual_tryon_segmind(**arguments)
        elif name == "generate_image_nano_banana":
            result = generate_image_nano_banana(**arguments)
        elif name == "generate_image_nano_banana_pro":
            result = generate_image_nano_banana_pro(**arguments)
        elif name == "generate_image_flux2_pro":
            result = generate_image_flux2_pro(**arguments)
        elif name == "generate_image_flux2_flex":
            result = generate_image_flux2_flex(**arguments)
        elif name == "generate_image_luma_photon_flash":
            result = generate_image_luma_photon_flash(**arguments)
        elif name == "generate_image_luma_photon":
            result = generate_image_luma_photon(**arguments)
        elif name == "generate_video_luma_ray":
            result = generate_video_luma_ray(**arguments)
        elif name == "segment_garment":
            result = segment_garment(**arguments)
        elif name == "extract_garment":
            result = extract_garment(**arguments)
        elif name == "segment_human":
            result = segment_human(**arguments)
        elif name == "load_fashion_mnist":
            result = load_fashion_mnist(**arguments)
        elif name == "load_viton_hd":
            result = load_viton_hd(**arguments)
        else:
            result = {
                "success": False,
                "error": f"Unknown tool: {name}"
            }
        
        # Format result as text content
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
        
    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": f"Tool execution failed: {str(e)}"
            }, indent=2)
        )]


async def main():
    """Main entry point for the MCP server."""
    # Print configuration status
    print(config.get_status_message(), file=sys.stderr)
    print("\nStarting OpenTryOn MCP Server...", file=sys.stderr)
    
    # Run the server
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())

