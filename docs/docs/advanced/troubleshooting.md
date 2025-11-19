# Troubleshooting

Common issues and solutions when using OpenTryOn.

## Import Errors

### Issue: ModuleNotFoundError

**Error:**
```
ModuleNotFoundError: No module named 'tryon'
```

**Solution:**
Ensure OpenTryOn is installed:

```bash
pip install -e .
```

Or install dependencies:

```bash
pip install -r requirements.txt
```

## CUDA Issues

### Issue: CUDA Out of Memory

**Error:**
```
RuntimeError: CUDA out of memory
```

**Solutions:**
1. Reduce batch size
2. Reduce image resolution
3. Use CPU instead of GPU:

```python
import os
os.environ["CUDA_VISIBLE_DEVICES"] = ""
```

### Issue: CUDA Not Available

**Error:**
```
CUDA not available, using CPU
```

**Solutions:**
1. Check CUDA installation:

```python
import torch
print(torch.cuda.is_available())
```

2. Install CUDA-compatible PyTorch:

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

## Model Checkpoint Issues

### Issue: Checkpoint Not Found

**Error:**
```
FileNotFoundError: Checkpoint not found
```

**Solution:**
1. Verify checkpoint path in `.env` file
2. Ensure checkpoint file exists at specified path
3. Download missing checkpoints:

```bash
# U2Net cloth segmentation
wget https://huggingface.co/levihsu/OOTDiffusion/resolve/main/cloth_segm.pth
```

## Environment Variable Issues

### Issue: Environment Variables Not Loaded

**Error:**
```
KeyError: 'U2NET_CLOTH_SEG_CHECKPOINT_PATH'
```

**Solution:**
Always load environment variables first:

```python
from dotenv import load_dotenv
load_dotenv()

# Then import OpenTryOn modules
from tryon.preprocessing import segment_garment
```

## Performance Issues

### Issue: Slow Processing

**Solutions:**
1. Use GPU if available
2. Reduce image resolution
3. Process in batches
4. Pre-load models for reuse

```python
# Pre-load model
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
net = load_cloth_segm_model(device, checkpoint_path)

# Reuse model for multiple images
for image in images:
    result = extract_garment(image, net=net, device=device)
```

## Dependency Conflicts

### Issue: Version Conflicts

**Solution:**
Use conda environment:

```bash
conda env create -f environment.yml
conda activate opentryon
```

## Still Having Issues?

1. Check [GitHub Issues](https://github.com/tryonlabs/opentryon/issues)
2. Join [Discord](https://discord.gg/T5mPpZHxkY)
3. Open a new issue with:
   - Error message
   - Python version
   - OpenTryOn version
   - Steps to reproduce

