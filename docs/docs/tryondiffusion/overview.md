# TryOnDiffusion Overview

TryOnDiffusion is a diffusion-based virtual try-on model using a dual UNet architecture.

## Key Features

- Dual UNet architecture (Person UNet + Garment UNet)
- Pose-conditioned generation
- Cross-attention between person and garment features
- Support for 64x64 and 128x128 resolutions

## Architecture

The model consists of two parallel UNets:

1. **Person UNet**: Generates the final output image
2. **Garment UNet**: Processes segmented garment information

## Quick Start

```python
from tryondiffusion.diffusion import Diffusion

diffusion = Diffusion(
    device="cuda",
    pose_embed_dim=8,
    time_steps=256,
    unet_dim=64
)
```

See [Training Guide](training.md) and [Inference Guide](inference.md) for details.

