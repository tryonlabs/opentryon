# OpenTryOn Tools Module

This module provides a comprehensive set of LangChain-compatible tools for building AI agents that can perform various fashion tech and virtual try-on tasks.

## Overview

The tools are organized by category:
- **Virtual Try-On**: Tools for trying on garments on models
- **Image Generation**: Tools for generating fashion images
- **Video Generation**: Tools for generating fashion videos
- **Model Swap**: Tools for swapping models while preserving outfits
- **Image Editing**: Tools for editing and composing images
- **Fashion**: Tools for fashion-specific preprocessing and analysis

## Architecture

All tools follow a consistent pattern:
- Use LangChain's `@tool` decorator
- Include Pydantic schemas for input validation
- Store full outputs in a global cache to avoid token limits
- Return JSON strings with metadata and cache keys

## Usage

### Basic Usage

```python
from tryon.tools import get_all_tools, get_virtual_tryon_tools

# Get all tools
all_tools = get_all_tools()

# Get tools by category
vton_tools = get_virtual_tryon_tools()
image_tools = get_image_generation_tools()
video_tools = get_video_generation_tools()
model_swap_tools = get_model_swap_tools()
editing_tools = get_image_editing_tools()
fashion_tools = get_fashion_tools()
```

### Using Tools with an Agent

```python
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_openai import ChatOpenAI
from tryon.tools import get_all_tools

# Get all tools
tools = get_all_tools()

# Create agent
llm = ChatOpenAI(model="gpt-4", temperature=0)
agent = create_openai_functions_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# Run agent
result = executor.invoke({
    "input": "Generate a virtual try-on of this shirt on this model"
})
```

### Retrieving Cached Results

Tools store full outputs in a cache to avoid token limits. To retrieve cached results:

```python
from tryon.tools import get_tool_output_cache

cache = get_tool_output_cache()
result = cache.get(cache_key)  # cache_key from tool output

# Access images/videos
if result:
    images = result["images"]  # List of PIL Images or bytes
    provider = result["provider"]
```

## Tool Categories

### Virtual Try-On Tools

Tools for trying on garments on models:

- **kling_ai_virtual_tryon**: Kling AI's Kolors Virtual Try-On
- **nova_canvas_virtual_tryon**: Amazon Nova Canvas (AWS Bedrock)
- **segmind_virtual_tryon**: Segmind Try-On Diffusion

### Image Generation Tools

Tools for generating fashion images:

- **nano_banana_text_to_image**: Google Nano Banana (Gemini 2.5 Flash)
- **nano_banana_pro_text_to_image**: Google Nano Banana Pro (Gemini 3 Pro)
- **flux2_pro_text_to_image**: FLUX 2 Pro
- **flux2_flex_text_to_image**: FLUX 2 Flex
- **gpt_image_text_to_image**: OpenAI GPT-Image (1 & 1.5)
- **luma_ai_text_to_image**: Luma AI

### Video Generation Tools

Tools for generating fashion videos:

- **sora_text_to_video**: OpenAI Sora 2 & Sora 2 Pro (text-to-video)
- **sora_image_to_video**: OpenAI Sora 2 & Sora 2 Pro (image-to-video)
- **veo_text_to_video**: Google Veo 3 (text-to-video)
- **veo_image_to_video**: Google Veo 3 (image-to-video)
- **luma_ai_text_to_video**: Luma AI Dream Machine (text-to-video)
- **luma_ai_image_to_video**: Luma AI Dream Machine (image-to-video)

### Model Swap Tools

Tools for swapping models while preserving outfits:

- **nano_banana_pro_model_swap**: Nano Banana Pro model swap
- **flux2_pro_model_swap**: FLUX 2 Pro model swap
- **flux2_flex_model_swap**: FLUX 2 Flex model swap

### Image Editing Tools

Tools for editing and composing images:

- **gpt_image_edit**: Basic image editing with GPT-Image
- **gpt_image_mask_edit**: Mask-based editing with GPT-Image
- **gpt_image_multi_edit**: Multi-image composition with GPT-Image

### Fashion Tools

Tools for fashion-specific preprocessing (to be implemented):

- Garment preprocessing and segmentation
- Pose estimation
- Fashion dataset utilities

## Tool Output Format

All tools return JSON strings with the following structure:

```json
{
    "status": "success" | "error",
    "provider": "provider_name",
    "cache_key": "hash_key_for_cache",
    "image_count": 1,
    "message": "Status message"
}
```

On error:
```json
{
    "status": "error",
    "provider": "provider_name",
    "error": "Error message",
    "message": "Error description"
}
```

## Cache Management

The global cache stores full outputs (images, videos) to avoid token limits. Cache keys are returned in tool outputs.

```python
from tryon.tools import get_tool_output_cache, clear_tool_output_cache

# Get cache
cache = get_tool_output_cache()

# Clear cache
clear_tool_output_cache()
```

## Examples

### Virtual Try-On Example

```python
from tryon.tools import kling_ai_virtual_tryon

result = kling_ai_virtual_tryon.invoke({
    "person_image": "model.jpg",
    "garment_image": "shirt.jpg"
})

# Parse result
import json
data = json.loads(result)
if data["status"] == "success":
    cache_key = data["cache_key"]
    # Retrieve images from cache
    from tryon.tools import get_tool_output_cache
    cache = get_tool_output_cache()
    images = cache[cache_key]["images"]
```

### Image Generation Example

```python
from tryon.tools import nano_banana_pro_text_to_image

result = nano_banana_pro_text_to_image.invoke({
    "prompt": "A professional fashion model wearing an elegant evening gown",
    "resolution": "4K"
})
```

### Model Swap Example

```python
from tryon.tools import nano_banana_pro_model_swap

result = nano_banana_pro_model_swap.invoke({
    "image": "person_wearing_outfit.jpg",
    "model_description": "Professional fashion photography showing an athletic Asian woman in her 30s wearing the exact same outfit with all clothing details preserved"
})
```

## Adding New Tools

To add a new tool:

1. Create a Pydantic schema for input validation
2. Use the `@tool` decorator from LangChain
3. Store outputs in `_tool_output_cache`
4. Return JSON string with status and cache_key
5. Add tool to the appropriate category's `get_*_tools()` function
6. Export in `__init__.py`

Example:

```python
from pydantic import BaseModel, Field
from langchain.tools import tool

class MyToolInput(BaseModel):
    input_param: str = Field(description="Description")

@tool("my_tool", args_schema=MyToolInput)
def my_tool(input_param: str) -> str:
    try:
        # Do work
        result = do_something(input_param)
        
        # Store in cache
        cache_key = hashlib.md5(f"my_tool_{input_param}".encode()).hexdigest()
        _tool_output_cache[cache_key] = {"result": result}
        
        return json.dumps({
            "status": "success",
            "cache_key": cache_key,
            "message": "Success"
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e)
        })
```

## Requirements

- langchain >= 1.0.0
- pydantic >= 2.0.0
- All OpenTryOn API adapters

## Notes

- Tools are designed to work with LangChain agents
- Full outputs are cached to avoid token limits
- All tools return JSON strings for consistency
- Error handling is built into each tool
- Tools can be used standalone or with agents

