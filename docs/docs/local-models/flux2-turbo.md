# FLUX.2-dev Turbo

FLUX.2-dev Turbo is a distilled LoRA adapter that enables high-quality image generation in just **8 inference steps**, making it **6x faster** than the base FLUX.2 [dev] model while preserving or surpassing its quality.

## Overview

| Feature | Value |
|---------|-------|
| **Model** | [fal/FLUX.2-dev-Turbo](https://huggingface.co/fal/FLUX.2-dev-Turbo) |
| **Base Model** | [black-forest-labs/FLUX.2-dev](https://huggingface.co/black-forest-labs/FLUX.2-dev) |
| **License** | FLUX [dev] Non-Commercial License |
| **Inference Steps** | 8 (vs 50 for base model) |
| **Speed** | 6x faster |
| **Min VRAM** | 12GB+ recommended |

## Key Features

- **8-step inference**: 6x faster than base model's typical 50 steps
- **Quality preserved**: Matches or surpasses original FLUX.2 [dev]
- **Text-to-image**: Generate images from text prompts
- **Image-to-image**: Transform existing images with text guidance
- **Auto VRAM selection**: Automatically selects quantized models for lower VRAM GPUs
- **Caption upsampling**: Enhance prompts for improved outputs

## Installation

```bash
pip install diffusers>=0.29.0 transformers accelerate torch

# For quantized models (GPUs with <64GB VRAM)
pip install bitsandbytes
```

## Quick Start

### Text-to-Image

```python
from tryon.models import Flux2TurboAdapter

# Initialize adapter (downloads model on first use)
adapter = Flux2TurboAdapter()

# Generate image
images = adapter.generate_text_to_image(
    prompt="A professional fashion model wearing an elegant red dress on a runway",
    width=1024,
    height=1024,
    seed=42
)
images[0].save("output.png")
```

### Image-to-Image

```python
from tryon.models import Flux2TurboAdapter

adapter = Flux2TurboAdapter()

# Transform an existing image
images = adapter.generate_image_to_image(
    image="input_model.jpg",
    prompt="A fashion model in an elegant blue evening gown",
    seed=42
)
images[0].save("transformed.png")
```

## API Reference

### Flux2TurboAdapter

```python
class Flux2TurboAdapter:
    def __init__(
        self,
        device: Optional[str] = None,           # "cuda" or "cpu", auto-detected
        torch_dtype: torch.dtype = torch.bfloat16,
        load_lora: bool = True,                 # Load Turbo LoRA weights
        enable_cpu_offload: bool = False,       # For low VRAM GPUs
        enable_attention_slicing: bool = False, # Reduce memory usage
        cache_dir: Optional[str] = None,        # Model cache directory
        model_id: Optional[str] = None,         # Explicit model ID
        auto_select_model: bool = True          # Auto-select based on VRAM
    )
```

### generate_text_to_image

```python
def generate_text_to_image(
    self,
    prompt: str,                              # Text description
    width: int = 1024,                        # Output width
    height: int = 1024,                       # Output height
    guidance_scale: float = 2.5,              # Prompt adherence (1-10)
    num_inference_steps: int = 8,             # Denoising steps
    num_images: int = 1,                      # Images to generate
    seed: Optional[int] = None,               # For reproducibility
    use_turbo_sigmas: bool = True,            # Optimized sigmas
    caption_upsample_temperature: Optional[float] = None  # Prompt enhancement
) -> List[Image.Image]
```

### generate_image_to_image

```python
def generate_image_to_image(
    self,
    image: Union[str, Image.Image],           # Input image path or PIL Image
    prompt: str,                              # Text description
    guidance_scale: float = 2.5,
    num_inference_steps: int = 8,
    seed: Optional[int] = None,
    use_turbo_sigmas: bool = True,
    caption_upsample_temperature: Optional[float] = None
) -> List[Image.Image]
```

## VRAM Management

### Automatic Model Selection

The adapter automatically selects the appropriate model based on your GPU's available VRAM:

```python
# Check your VRAM info
info = Flux2TurboAdapter.get_vram_info()
print(f"Available VRAM: {info['available_vram_gb']}GB")
print(f"Recommended model: {info['recommended_model']}")
```

| VRAM | Model |
|------|-------|
| ≥64GB | `black-forest-labs/FLUX.2-dev` (full) |
| ≥48GB | `diffusers/FLUX.2-dev-bnb-8bit` |
| ≥38GB | `diffusers/FLUX.2-dev-bnb-4bit` |
| &lt;38GB | `diffusers/FLUX.2-dev-bnb-4bit` (with warnings) |

### Memory Optimization

```python
# For GPUs with limited VRAM
adapter = Flux2TurboAdapter(
    enable_cpu_offload=True,       # Offload to CPU when not in use
    enable_attention_slicing=True  # Slice attention for lower peak memory
)
```

## Recommended Settings

```python
# Get recommended settings
settings = Flux2TurboAdapter.get_recommended_settings()
print(settings)
# {
#     'num_inference_steps': 8,
#     'guidance_scale': 2.5,
#     'sigmas': [1.0, 0.6509, 0.4374, 0.2932, 0.1893, 0.1108, 0.0495, 0.00031],
#     'recommended_resolutions': [(1024, 1024), (1024, 768), ...],
#     'torch_dtype': 'torch.bfloat16',
#     'min_vram_gb': 12
# }
```

## Recommended Resolutions

| Aspect Ratio | Resolution |
|--------------|------------|
| 1:1 (Square) | 1024×1024 |
| 4:3 (Landscape) | 1024×768 |
| 3:4 (Portrait) | 768×1024 |
| 16:9 (Landscape) | 1280×720 |
| 9:16 (Portrait) | 720×1280 |

## Advanced Usage

### Caption Upsampling

Enhance prompts for potentially improved outputs:

```python
images = adapter.generate_text_to_image(
    prompt="A fashion model",
    caption_upsample_temperature=0.15  # Recommended value
)
```

### Managing LoRA Weights

```python
# Unload Turbo LoRA to use base model
adapter.unload_lora()

# Reload Turbo LoRA
adapter.reload_lora()
```

### Reproducible Generation

```python
# Use seed for reproducible results
images = adapter.generate_text_to_image(
    prompt="A fashion model wearing elegant attire",
    seed=42
)
```

## Troubleshooting

### Out of Memory (OOM)

1. Enable CPU offloading:
   ```python
   adapter = Flux2TurboAdapter(enable_cpu_offload=True)
   ```

2. Use a quantized model:
   ```python
   adapter = Flux2TurboAdapter(model_id="diffusers/FLUX.2-dev-bnb-4bit")
   ```

3. Reduce resolution:
   ```python
   images = adapter.generate_text_to_image(prompt="...", width=512, height=512)
   ```

### Slow Generation

- Ensure CUDA is available: `torch.cuda.is_available()`
- Check that the model is on GPU, not CPU
- Use 8 inference steps (default for Turbo)

### Model Download Issues

Models are downloaded from HuggingFace on first use. Ensure:
- Stable internet connection
- Sufficient disk space (~20GB for full model)
- HuggingFace access for gated models

## References

- [FLUX.2-dev Turbo on HuggingFace](https://huggingface.co/fal/FLUX.2-dev-Turbo)
- [FLUX.2 Pipeline Documentation](https://huggingface.co/docs/diffusers/main/en/api/pipelines/flux2)
- [diffusers Library](https://huggingface.co/docs/diffusers)

