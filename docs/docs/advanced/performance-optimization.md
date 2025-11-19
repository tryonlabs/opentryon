# Performance Optimization

Tips for optimizing OpenTryOn performance.

## GPU Optimization

1. Use GPU for inference:

```python
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
```

2. Pre-load models:

```python
net = load_cloth_segm_model(device, checkpoint_path)
# Reuse model for multiple images
```

3. Batch processing:

```python
# Process multiple images in batches
for batch in batches:
    results = process_batch(batch)
```

## Memory Optimization

1. Reduce image resolution
2. Process in smaller batches
3. Use CPU offloading for large models

## Speed Optimization

1. Use smaller UNet dimensions (64 vs 128)
2. Reduce number of diffusion steps
3. Use quantization for inference

See [Troubleshooting](troubleshooting.md) for more tips.

