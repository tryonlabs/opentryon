# Custom Models

Guide to using custom models with OpenTryOn.

## Loading Custom Models

You can use custom models by providing checkpoint paths:

```python
import os
os.environ["U2NET_CLOTH_SEG_CHECKPOINT_PATH"] = "/path/to/custom/model.pth"
```

## Model Compatibility

OpenTryOn supports models compatible with:
- U2Net architecture
- Standard PyTorch model formats

See [Preprocessing Documentation](../preprocessing/overview.md) for details.

