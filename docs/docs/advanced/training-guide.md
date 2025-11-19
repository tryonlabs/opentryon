# Training Guide

Comprehensive guide to training models with OpenTryOn.

See [TryOnDiffusion Training](../tryondiffusion/training.md) for detailed training instructions.

## Quick Start

```python
from tryondiffusion.diffusion import Diffusion

diffusion = Diffusion(device="cuda", pose_embed_dim=8)
diffusion.prepare(args)
diffusion.fit(args)
```

