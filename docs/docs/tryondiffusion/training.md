# Training TryOnDiffusion

Guide to training the TryOnDiffusion model.

## Preparation

1. Prepare your dataset
2. Run preprocessing pipeline
3. Configure training parameters

## Basic Training

```python
from tryondiffusion.diffusion import Diffusion

diffusion = Diffusion(
    device="cuda",
    pose_embed_dim=8,
    time_steps=256,
    unet_dim=64
)

# Prepare data
diffusion.prepare(args)

# Start training
diffusion.fit(args)
```

See [TryOnDiffusion README](https://github.com/tryonlabs/opentryon/tree/main/tryondiffusion/README.md) for detailed training guide.

