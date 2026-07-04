# Local Models Overview

OpenTryOn provides adapters for local inference models that run directly on your hardware. Unlike the cloud API adapters in `tryon.api`, these models require local GPU resources but offer several advantages:

- **No API costs**: Run unlimited inferences without per-request charges
- **Privacy**: Your data never leaves your machine
- **Customization**: Fine-tune models for your specific use case
- **Offline capability**: Work without internet connectivity

## Available Models

| Model | Type | VRAM Required | Speed | Use Case |
|-------|------|--------------|-------|----------|
| [FLUX.2-dev Turbo](./flux2-turbo) | Image Generation | 12GB+ | 6x faster | Fast text-to-image, image-to-image |
| [Kimi-VL](./kimi-vl) | Image/Video Understanding | 24GB+ | - | Open-weight counterpart to the Kimi K2.6/K2.7 Code APIs |

## Requirements

All local models require:

- **CUDA-capable GPU** (NVIDIA recommended)
- **PyTorch 2.1+** with CUDA support
- **diffusers >= 0.29.0**
- **transformers**
- **accelerate**

### VRAM Considerations

Local models are memory-intensive. FLUX.2-dev Turbo supports automatic model selection based on available VRAM:

| Available VRAM | Model Selection |
|----------------|-----------------|
| ≥64GB | Full precision model |
| ≥48GB | 8-bit quantized |
| ≥38GB | 4-bit quantized |
| &lt;38GB | 4-bit quantized (with warnings) |

## Quick Start

```python
from tryon.models import Flux2TurboAdapter

# Initialize (auto-selects model based on VRAM)
adapter = Flux2TurboAdapter()

# Generate image
images = adapter.generate_text_to_image(
    prompt="A fashion model wearing an elegant dress",
    width=1024,
    height=1024
)
images[0].save("output.png")
```

## Installation

Install the required dependencies:

```bash
pip install diffusers>=0.29.0 transformers accelerate torch

# For quantized models (lower VRAM requirements)
pip install bitsandbytes
```

## Memory Optimization Tips

1. **Enable CPU Offloading**: For GPUs with limited VRAM
   ```python
   adapter = Flux2TurboAdapter(enable_cpu_offload=True)
   ```

2. **Use Attention Slicing**: Reduces peak memory at slight speed cost
   ```python
   adapter = Flux2TurboAdapter(enable_attention_slicing=True)
   ```

3. **Lower Resolution**: Start with smaller images for testing
   ```python
   images = adapter.generate_text_to_image(prompt="...", width=512, height=512)
   ```

4. **Clear CUDA Cache**: Between generations
   ```python
   import torch
   torch.cuda.empty_cache()
   ```

