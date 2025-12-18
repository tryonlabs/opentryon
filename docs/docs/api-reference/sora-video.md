---
sidebar_position: 8
title: Sora (OpenAI Video Generation)
description: Generate high-quality videos using OpenAI's Sora models (Sora 2 and Sora 2 Pro) with text-to-video and image-to-video capabilities.
keywords:
  - Sora 2
  - Sora 2 Pro
  - OpenAI video generation
  - video generation
  - text to video
  - image to video
  - video AI
  - fashion video
---

# Sora (OpenAI Video Generation)

Generate high-quality videos using OpenAI's **Sora 2** and **Sora 2 Pro** models. This adapter provides a unified interface for text-to-video and image-to-video generation with both synchronous (polling) and asynchronous (callback-based) wait mechanisms.

## Models Available

OpenAI provides two Sora model variants:

### **Sora 2** (Default)
- **Model ID**: `sora-2`
- **Best for**: Fast, high-quality video generation
- **Use cases**: Standard video generation, rapid prototyping, preview generation
- **Speed**: Faster generation times
- **Quality**: High quality suitable for most applications

### **Sora 2 Pro**
- **Model ID**: `sora-2-pro`
- **Best for**: Premium quality with enhanced temporal consistency
- **Use cases**: Professional video content, marketing materials, high-fidelity animations
- **Speed**: Slower than Sora 2
- **Quality**: Superior quality with better prompt understanding and frame consistency

## Features

- ✅ **Text-to-Video**: Generate videos from text descriptions
- ✅ **Image-to-Video**: Animate static images with text prompts
- ✅ **Flexible Durations**: Support for 4, 8, and 12-second videos
- ✅ **Multiple Resolutions**: From 720p to Full HD in various aspect ratios
- ✅ **Two Wait Modes**: Synchronous (blocking) and asynchronous (callbacks)
- ✅ **Progress Tracking**: Monitor video generation status
- ✅ **Simple Python API**: Easy-to-use interface
- ✅ **CLI Support**: Command-line interface for quick generation

## Installation

```bash
pip install openai
```

## Configuration

Set your OpenAI API key as an environment variable:

```bash
export OPENAI_API_KEY='your-api-key-here'
```

Or pass it directly when initializing the adapter.

## Basic Usage

### Text-to-Video Generation

```python
from tryon.api.openAI import SoraVideoAdapter

# Initialize adapter (uses Sora 2 by default)
adapter = SoraVideoAdapter()

# Generate a video from text prompt (synchronous)
video_bytes = adapter.generate_text_to_video(
    prompt="A fashion model walking down a runway wearing an elegant evening gown",
    duration=8,  # seconds
    resolution="1920x1080"  # Full HD
)

# Save the video
with open("runway_walk.mp4", "wb") as f:
    f.write(video_bytes)
```

### Using Sora 2 Pro

```python
# Initialize with Sora 2 Pro for higher quality
adapter = SoraVideoAdapter(model_version="sora-2-pro")

video_bytes = adapter.generate_text_to_video(
    prompt="Cinematic slow-motion shot of fabric flowing in the wind",
    duration=12,
    resolution="1920x1080"
)

with open("fabric_flow.mp4", "wb") as f:
    f.write(video_bytes)
```

### Image-to-Video Generation

```python
# Animate a static image
adapter = SoraVideoAdapter()

video_bytes = adapter.generate_image_to_video(
    image="model_photo.jpg",
    prompt="The model turns around and smiles at the camera",
    duration=4,
    resolution="1280x720"
)

with open("animated_model.mp4", "wb") as f:
    f.write(video_bytes)
```

## Advanced Usage

### Asynchronous Generation with Callbacks

```python
adapter = SoraVideoAdapter()

# Define callback functions
def on_complete(video_bytes):
    with open("output.mp4", "wb") as f:
        f.write(video_bytes)
    print("✅ Video generation complete!")

def on_error(error):
    print(f"❌ Error: {error}")

def on_progress(status):
    print(f"Status: {status['status']}, Progress: {status.get('progress', 'N/A')}")

# Start async generation
video_id = adapter.generate_text_to_video_async(
    prompt="A person trying on different outfits in a fashion boutique",
    duration=8,
    resolution="1920x1080",
    on_complete=on_complete,
    on_error=on_error,
    on_progress=on_progress
)

print(f"Video generation started with ID: {video_id}")
# Script continues immediately, callbacks will be invoked when ready
```

### Manual Status Tracking

```python
# Start generation without waiting
video_id = adapter.generate_text_to_video(
    prompt="Fashion runway show with multiple models",
    duration=12,
    resolution="1920x1080",
    wait=False  # Return immediately
)

# Check status manually
import time
while True:
    status = adapter.get_video_status(video_id)
    print(f"Status: {status['status']}")
    
    if status['status'] == 'completed':
        video_bytes = adapter.download_video(video_id)
        with open("runway_show.mp4", "wb") as f:
            f.write(video_bytes)
        break
    elif status['status'] == 'failed':
        print(f"Failed: {status.get('error')}")
        break
    
    time.sleep(5)
```

## CLI Usage

The package includes a command-line interface for easy video generation:

### Basic Text-to-Video

```bash
python sora_video.py --prompt "A fashion model walking in the rain" \
                     --output walk.mp4
```

### High-Quality with Sora 2 Pro

```bash
python sora_video.py --prompt "Cinematic fashion runway show" \
                     --model sora-2-pro \
                     --duration 12 \
                     --resolution 1920x1080 \
                     --output runway.mp4
```

### Image-to-Video

```bash
python sora_video.py --image model_photo.jpg \
                     --prompt "The model waves and smiles" \
                     --duration 4 \
                     --output animated.mp4
```

### Asynchronous Mode

```bash
python sora_video.py --prompt "Fabric flowing in slow motion" \
                     --duration 8 \
                     --async \
                     --output fabric.mp4
```

## API Reference

### SoraVideoAdapter

#### Constructor

```python
SoraVideoAdapter(
    api_key: Optional[str] = None,
    model_version: str = "sora-2",
    polling_interval: int = 5,
    max_polling_time: int = 300
)
```

**Parameters:**
- `api_key` (str, optional): OpenAI API key. Defaults to `OPENAI_API_KEY` environment variable.
- `model_version` (str, optional): Model to use. Options: `"sora-2"`, `"sora-2-pro"`. Default: `"sora-2"`.
- `polling_interval` (int, optional): Seconds between status checks. Default: 5.
- `max_polling_time` (int, optional): Maximum wait time in seconds. Default: 300 (5 minutes).

#### generate_text_to_video()

```python
generate_text_to_video(
    prompt: str,
    duration: int = 4,
    resolution: str = "1280x720",
    wait: bool = True
) -> Union[bytes, str]
```

Generate a video from a text prompt.

**Parameters:**
- `prompt` (str): Text description of the video content. **Required**.
- `duration` (int, optional): Video length in seconds. Options: `4`, `8`, `12`. Default: `4`.
- `resolution` (str, optional): Output resolution. See [Supported Resolutions](#supported-resolutions). Default: `"1280x720"`.
- `wait` (bool, optional): If `True`, waits for completion and returns video bytes. If `False`, returns video ID immediately. Default: `True`.

**Returns:**
- `bytes`: Video data (if `wait=True`)
- `str`: Video generation ID (if `wait=False`)

**Raises:**
- `ValueError`: If parameters are invalid
- `TimeoutError`: If generation exceeds `max_polling_time`
- `RuntimeError`: If generation fails

#### generate_image_to_video()

```python
generate_image_to_video(
    image: Union[str, io.BytesIO, Image.Image],
    prompt: str,
    duration: int = 4,
    resolution: str = "1280x720",
    wait: bool = True
) -> Union[bytes, str]
```

Generate a video from an image and text prompt.

**Parameters:**
- `image` (Union[str, io.BytesIO, Image.Image]): Input image. Can be file path, BytesIO, or PIL Image. **Required**.
- `prompt` (str): Animation instructions. **Required**.
- `duration` (int, optional): Video length in seconds. Options: `4`, `8`, `12`. Default: `4`.
- `resolution` (str, optional): Output resolution. Default: `"1280x720"`.
- `wait` (bool, optional): Whether to wait for completion. Default: `True`.

**Returns:**
- `bytes`: Video data (if `wait=True`)
- `str`: Video generation ID (if `wait=False`)

#### generate_text_to_video_async()

```python
generate_text_to_video_async(
    prompt: str,
    duration: int = 4,
    resolution: str = "1280x720",
    on_complete: Optional[Callable[[bytes], None]] = None,
    on_error: Optional[Callable[[str], None]] = None,
    on_progress: Optional[Callable[[Dict[str, Any]], None]] = None
) -> str
```

Generate video asynchronously with callback functions.

**Parameters:**
- `prompt` (str): Text description. **Required**.
- `duration` (int, optional): Video length in seconds. Default: `4`.
- `resolution` (str, optional): Output resolution. Default: `"1280x720"`.
- `on_complete` (Callable, optional): Called with video bytes when complete.
- `on_error` (Callable, optional): Called with error message if generation fails.
- `on_progress` (Callable, optional): Called with status dict during generation.

**Returns:**
- `str`: Video generation ID

#### generate_image_to_video_async()

```python
generate_image_to_video_async(
    image: Union[str, io.BytesIO, Image.Image],
    prompt: str,
    duration: int = 4,
    resolution: str = "1280x720",
    on_complete: Optional[Callable[[bytes], None]] = None,
    on_error: Optional[Callable[[str], None]] = None,
    on_progress: Optional[Callable[[Dict[str, Any]], None]] = None
) -> str
```

Generate video from image asynchronously with callbacks.

#### get_video_status()

```python
get_video_status(video_id: str) -> Dict[str, Any]
```

Check the status of a video generation request.

**Returns:**
```python
{
    "status": "queued" | "in_progress" | "completed" | "failed",
    "id": "video_id",
    "progress": 0-100,  # Optional
    "url": "...",       # Only when completed
    "file_id": "...",   # Only when completed
    "error": "..."      # Only when failed
}
```

#### download_video()

```python
download_video(video_id: str) -> bytes
```

Download a completed video by its ID.

**Raises:**
- `RuntimeError`: If video is not yet completed

## Configuration Options

### Supported Resolutions

| Resolution | Aspect Ratio | Orientation | Use Case |
|-----------|--------------|-------------|----------|
| `720x1280` | 9:16 | Vertical | Mobile, Stories |
| `1280x720` | 16:9 | Horizontal | Standard HD |
| `1080x1920` | 9:16 | Vertical | Full HD Mobile |
| `1920x1080` | 16:9 | Horizontal | Full HD Desktop |
| `1024x1792` | ~9:16 | Tall Vertical | Special formats |
| `1792x1024` | ~16:9 | Wide Horizontal | Cinematic |

### Supported Durations

- **4 seconds**: Quick clips, previews, social media snippets
- **8 seconds**: Standard content, demonstrations, short narratives
- **12 seconds**: Extended content, detailed animations, storytelling

## Model Comparison

| Feature | Sora 2 | Sora 2 Pro |
|---------|--------|------------|
| **Speed** | Fast ⚡ | Slower 🐢 |
| **Quality** | High | Superior |
| **Temporal Consistency** | Good | Excellent |
| **Prompt Understanding** | Good | Superior |
| **Frame Coherence** | Good | Excellent |
| **Best For** | Rapid iteration, previews | Final production, marketing |
| **Cost** | Lower | Higher |

## Wait Mechanisms

### 1. Synchronous (Polling) - Default

**When to use:**
- Simple scripts
- One-off generations
- When you can block and wait

**How it works:**
```python
video_bytes = adapter.generate_text_to_video(
    prompt="...",
    wait=True  # Blocks until complete
)
```

### 2. Asynchronous (Callbacks)

**When to use:**
- Multiple concurrent generations
- Long-running applications
- When you need progress updates
- Non-blocking workflows

**How it works:**
```python
video_id = adapter.generate_text_to_video_async(
    prompt="...",
    on_complete=lambda bytes: save_video(bytes),
    on_progress=lambda status: print(status)
)
# Continues immediately
```

### 3. Manual Tracking

**When to use:**
- Custom control flow
- Integration with existing systems
- When you need fine-grained control

**How it works:**
```python
# Start without waiting
video_id = adapter.generate_text_to_video(prompt="...", wait=False)

# Check status anytime
status = adapter.get_video_status(video_id)

# Download when ready
if status['status'] == 'completed':
    video_bytes = adapter.download_video(video_id)
```

## Common Use Cases

### Fashion Runway Videos

```python
adapter = SoraVideoAdapter(model_version="sora-2-pro")

video_bytes = adapter.generate_text_to_video(
    prompt="Professional fashion runway show with model wearing elegant evening gown, "
           "cinematic lighting, slow motion walk, professional photography",
    duration=12,
    resolution="1920x1080"
)
```

### Product Animation

```python
adapter = SoraVideoAdapter()

video_bytes = adapter.generate_image_to_video(
    image="product_photo.jpg",
    prompt="360-degree rotation of the product, professional studio lighting",
    duration=4,
    resolution="1280x720"
)
```

### Fabric Visualization

```python
video_bytes = adapter.generate_text_to_video(
    prompt="Luxurious silk fabric flowing gracefully in slow motion, "
           "golden hour lighting, close-up macro shot",
    duration=8,
    resolution="1920x1080"
)
```

### Model Portfolio Animation

```python
adapter = SoraVideoAdapter()

video_bytes = adapter.generate_image_to_video(
    image="model_portrait.jpg",
    prompt="Model turns head towards camera with confident expression, "
           "professional studio lighting, fashion photography",
    duration=4,
    resolution="1080x1920"  # Vertical for mobile
)
```

## Error Handling

```python
from tryon.api.openAI import SoraVideoAdapter

adapter = SoraVideoAdapter()

try:
    video_bytes = adapter.generate_text_to_video(
        prompt="A fashion model walking",
        duration=8,
        resolution="1920x1080"
    )
    
    with open("output.mp4", "wb") as f:
        f.write(video_bytes)
    
except ValueError as e:
    print(f"Invalid parameters: {e}")
except TimeoutError as e:
    print(f"Generation timeout: {e}")
except RuntimeError as e:
    print(f"Generation failed: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Performance Tips

1. **Use Sora 2 for iteration**: Start with Sora 2 for rapid prototyping, then switch to Sora 2 Pro for final output.

2. **Optimize duration**: Longer videos take significantly more time. Use 4-second clips for testing.

3. **Async for batch processing**: When generating multiple videos, use async mode to parallelize:
   ```python
   for prompt in prompts:
       adapter.generate_text_to_video_async(
           prompt=prompt,
           on_complete=lambda b: save_video(b)
       )
   ```

4. **Monitor progress**: Use `on_progress` callbacks to track generation status.

5. **Handle timeouts gracefully**: Set appropriate `max_polling_time` based on your duration and model.

## Limitations

- Maximum video duration: 12 seconds
- Generation time varies by duration and model (typically 1-5 minutes)
- API rate limits apply (check OpenAI's documentation)
- Video format: MP4 (H.264)
- Frame rate: 24 FPS (default, may vary)

## Related Documentation

- [OpenAI Video Generation Guide](https://platform.openai.com/docs/guides/video-generation)
- [GPT-Image (OpenAI)](./gpt-image)
- [FLUX.2 Image Generation](./flux2)
- [API Reference Overview](./overview)

## Troubleshooting

### "Video generation timeout"
- Increase `max_polling_time` parameter
- Try a shorter duration (4s instead of 12s)
- Check OpenAI API status

### "Invalid resolution"
- Use one of the supported resolutions listed above
- Common safe choice: `"1280x720"`

### "API key not found"
- Set `OPENAI_API_KEY` environment variable
- Or pass `api_key` parameter explicitly

### Poor video quality
- Try using Sora 2 Pro instead of Sora 2
- Refine your prompt with more details
- Check resolution settings

## Support

For issues and questions:
- OpenAI API Support: [OpenAI Help Center](https://help.openai.com/)
- OpenTryOn Issues: [GitHub Issues](https://github.com/tryonlabs/opentryon/issues)

