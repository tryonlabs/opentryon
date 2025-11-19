# TryOnDiffusion Inference

Guide to running inference with TryOnDiffusion.

## Sampling

```python
from tryondiffusion.diffusion import Diffusion

diffusion = Diffusion(...)
# Load checkpoint
# ...

# Generate image
result = diffusion.sample(
    use_ema=True,
    conditional_inputs=(ic, jp, jg, ia)
)
```

See [TryOnDiffusion README](https://github.com/tryonlabs/opentryon/tree/main/tryondiffusion/README.md) for complete inference guide.

