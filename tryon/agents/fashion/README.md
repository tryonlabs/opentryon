# Fashion Agent

The Fashion Agent is a comprehensive LangChain-based AI agent that can perform various fashion-related tasks including virtual try-on, image generation, video generation, image editing, model swapping, and fashion preprocessing.

## Overview

The Fashion Agent intelligently analyzes user requests and selects the appropriate tools from OpenTryOn's comprehensive toolset to accomplish the requested tasks. It provides a unified interface for all fashion-related operations.

## Capabilities

The Fashion Agent has access to 20+ tools organized into the following categories:

### 1. Virtual Try-On
- Kling AI Virtual Try-On (high-quality, high-resolution)
- Amazon Nova Canvas (AWS Bedrock integration)
- Segmind Try-On Diffusion (fast and efficient)

### 2. Image Generation
- Nano Banana (Google Gemini 2.5 Flash)
- Nano Banana Pro (Google Gemini 3 Pro, 4K support)
- FLUX 2 Pro (professional quality)
- FLUX 2 Flex (fast and flexible)
- GPT-Image (OpenAI, excellent prompt understanding)
- Luma AI (various styles)

### 3. Video Generation
- OpenAI Sora 2 & Sora 2 Pro (text-to-video, image-to-video)
- Google Veo 3 (text-to-video, image-to-video)
- Luma AI Dream Machine (text-to-video, image-to-video)

### 4. Model Swapping
- Nano Banana Pro (best outfit preservation, 4K quality)
- FLUX 2 Pro (high-quality model swapping)
- FLUX 2 Flex (fast model swapping)

### 5. Image Editing
- GPT-Image editing (general image edits)
- Mask-based editing (precise region edits)
- Multi-image composition (combine multiple images)

### 6. Fashion Preprocessing
- Garment preprocessing and segmentation (coming soon)
- Pose estimation (coming soon)

## Installation

```bash
pip install opentryon
```

## Usage

### Basic Usage

```python
from tryon.agents.fashion import FashionAgent

# Initialize the agent
agent = FashionAgent(llm_provider="openai")

# Generate virtual try-on
result = agent.generate(
    prompt="Generate a virtual try-on of this shirt on this model using Kling AI",
    person_image="person.jpg",
    garment_image="shirt.jpg"
)

print(f"Status: {result['status']}")
print(f"Tool used: {result['tool']}")
print(f"Cache key: {result['cache_key']}")
```

### Virtual Try-On

```python
agent = FashionAgent(llm_provider="openai")

# Virtual try-on with Kling AI
result = agent.generate(
    prompt="Create a virtual try-on using Kling AI",
    person_image="model.jpg",
    garment_image="dress.jpg"
)

# Retrieve cached images
if result['status'] == 'success':
    cached_data = agent.get_cached_output(result['cache_key'])
    images = cached_data['images']
    # Process images...
```

### Image Generation

```python
agent = FashionAgent(llm_provider="openai")

# Generate fashion image
result = agent.generate(
    prompt="Generate a professional fashion photo of a model wearing an elegant evening gown, high quality"
)

# The agent will automatically select the best tool (e.g., Nano Banana Pro for high quality)
```

### Video Generation

```python
agent = FashionAgent(llm_provider="openai")

# Generate fashion video
result = agent.generate(
    prompt="Generate a video of a fashion model walking on a runway wearing elegant attire",
    image="model.jpg"  # Optional: for image-to-video
)
```

### Model Swapping

```python
agent = FashionAgent(llm_provider="openai")

# Swap model while preserving outfit
result = agent.generate(
    prompt="Replace the model with a professional Asian female model in her 30s, athletic build",
    image="person_wearing_outfit.jpg"
)
```

### Image Editing

```python
agent = FashionAgent(llm_provider="openai")

# Edit image
result = agent.generate(
    prompt="Change the dress color to midnight blue",
    image="fashion_photo.jpg"
)

# Mask-based editing
result = agent.generate(
    prompt="Replace the background with a studio backdrop",
    image="fashion_photo.jpg",
    # mask would be passed if mask editing tool is used
)
```

### Multi-Image Composition

```python
agent = FashionAgent(llm_provider="openai")

# Compose multiple images
result = agent.generate(
    prompt="Combine these outfit images into a fashion collage",
    images=["outfit1.jpg", "outfit2.jpg", "outfit3.jpg"]
)
```

## Configuration

### LLM Provider Options

The Fashion Agent supports multiple LLM providers:

```python
# OpenAI (default)
agent = FashionAgent(llm_provider="openai", llm_model="gpt-4o")

# Anthropic Claude
agent = FashionAgent(llm_provider="anthropic", llm_model="claude-sonnet-4-20250514")

# Google Gemini
agent = FashionAgent(llm_provider="google", llm_model="gemini-2.0-flash-exp")
```

### API Keys

Set API keys via environment variables or constructor:

```python
import os

# Set environment variables
os.environ["OPENAI_API_KEY"] = "your-key"
os.environ["GEMINI_API_KEY"] = "your-key"
os.environ["ANTHROPIC_API_KEY"] = "your-key"

# Or pass directly
agent = FashionAgent(
    llm_provider="openai",
    api_key="your-openai-api-key"
)
```

### Temperature

Control randomness (default: 0.0 for deterministic behavior):

```python
agent = FashionAgent(
    llm_provider="openai",
    temperature=0.7  # More creative responses
)
```

## Response Format

The `generate()` method returns a dictionary with the following structure:

```python
{
    "status": "success" | "error",
    "tool": "tool_name",
    "provider": "provider_name",
    "cache_key": "cache_key_string",
    "image_count": 1,  # Number of images generated
    "result": "agent_response_text",
    "tool_output": {
        # Tool-specific output
    },
    "messages": [...],  # Full conversation history
    "error": "error_message"  # Only if status is "error"
}
```

## Retrieving Cached Outputs

Tools store full outputs (images, videos) in a cache to avoid token limits. Retrieve them using the cache key:

```python
result = agent.generate(...)

if result['status'] == 'success':
    cache_key = result['cache_key']
    cached_data = agent.get_cached_output(cache_key)
    
    # Access cached data
    images = cached_data['images']  # List of PIL Images or bytes
    provider = cached_data['provider']
    
    # Save images
    for i, img in enumerate(images):
        if isinstance(img, Image.Image):
            img.save(f"result_{i}.png")
        elif isinstance(img, bytes):
            with open(f"result_{i}.mp4", "wb") as f:
                f.write(img)
```

## Verbose Mode

Enable verbose output to see tool selection and execution:

```python
result = agent.generate(
    prompt="Generate a virtual try-on",
    person_image="person.jpg",
    garment_image="shirt.jpg",
    verbose=True  # Shows tool selection and execution steps
)
```

## Examples

### Complete Virtual Try-On Workflow

```python
from tryon.agents.fashion import FashionAgent
from PIL import Image

# Initialize agent
agent = FashionAgent(llm_provider="openai")

# Generate virtual try-on
result = agent.generate(
    prompt="Use Kling AI to create a high-quality virtual try-on",
    person_image="model.jpg",
    garment_image="dress.jpg",
    verbose=True
)

# Check status
if result['status'] == 'success':
    print(f"✅ Success! Used tool: {result['tool']}")
    
    # Retrieve cached images
    cached_data = agent.get_cached_output(result['cache_key'])
    images = cached_data['images']
    
    # Save results
    for i, img in enumerate(images):
        if isinstance(img, Image.Image):
            img.save(f"vton_result_{i}.png")
            print(f"Saved image {i+1}: vton_result_{i}.png")
else:
    print(f"❌ Error: {result.get('error', 'Unknown error')}")
```

### Multi-Step Fashion Workflow

```python
agent = FashionAgent(llm_provider="openai")

# Step 1: Generate fashion image
image_result = agent.generate(
    prompt="Generate a professional fashion photo of a model wearing a red evening gown"
)

# Step 2: Generate video from the image
if image_result['status'] == 'success':
    cached_image = agent.get_cached_output(image_result['cache_key'])
    # Save the generated image first
    image_path = "generated_image.png"
    cached_image['images'][0].save(image_path)
    
    # Generate video
    video_result = agent.generate(
        prompt="Animate this image with the model walking gracefully",
        image=image_path
    )
```

## Best Practices

1. **Be Specific**: Provide clear, detailed prompts for better results
2. **Specify Providers**: Mention preferred providers/models if you have preferences
3. **Handle Errors**: Always check the `status` field before processing results
4. **Cache Management**: Retrieve cached outputs immediately after generation
5. **Resource Management**: For production, consider implementing cache cleanup
6. **Verbose Mode**: Use verbose mode during development for debugging

## Limitations

- Fashion preprocessing tools (garment segmentation, pose estimation) are coming soon
- Some tools may have rate limits or cost considerations
- Video generation can take several minutes
- Large images may require significant memory

## Troubleshooting

### Import Errors

```python
# Make sure OpenTryOn is installed
pip install --upgrade opentryon
```

### API Key Errors

```python
# Verify environment variables are set
import os
print(os.getenv("OPENAI_API_KEY"))  # Should not be None
```

### Tool Selection Issues

```python
# Be more specific in your prompt
# Instead of: "Generate an image"
# Use: "Generate a high-quality fashion image using Nano Banana Pro"
```

## See Also

- [OpenTryOn Documentation](https://tryonlabs.github.io/opentryon/)
- [Tools Module Documentation](../tools/README.md)
- [Virtual Try-On Agent](../vton/README.md)
- [Model Swap Agent](../model_swap/README.md)

