# Installation

This guide will help you install OpenTryOn on your system.

## Prerequisites

Before installing OpenTryOn, ensure you have:

- **Python 3.10** or higher
- **CUDA-capable GPU** (recommended for best performance)
- **Conda** or **Miniconda** (recommended)
- **Git** (for cloning the repository)

## Installation Methods

### Method 1: Using Conda (Recommended)

Conda is the recommended installation method as it handles all dependencies including CUDA libraries.

#### Step 1: Clone the Repository

```bash
git clone https://github.com/tryonlabs/opentryon.git
cd opentryon
```

#### Step 2: Create Conda Environment

```bash
conda env create -f environment.yml
conda activate opentryon
```

This will create a new conda environment named `opentryon` with all required dependencies.

#### Step 3: Install Package

```bash
pip install -e .
```

### Method 2: Using pip

If you prefer using pip, you can install dependencies directly:

#### Step 1: Clone the Repository

```bash
git clone https://github.com/tryonlabs/opentryon.git
cd opentryon
```

#### Step 2: Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
pip install -e .
```

### Method 3: Install from PyPI (Future)

Once published to PyPI, you'll be able to install directly:

```bash
pip install opentryon
```

## Verify Installation

After installation, verify that OpenTryOn is correctly installed:

```python
python -c "import tryon; print('OpenTryOn installed successfully!')"
```

## Configuration

### Environment Variables

Create a `.env` file in the project root with the following variables:

```env
U2NET_CLOTH_SEG_CHECKPOINT_PATH=path/to/cloth_segm.pth
U2NET_SEGM_CHECKPOINT_PATH=path/to/u2net.pth
```

### Download Model Checkpoints

#### U2Net Cloth Segmentation

Download the checkpoint from the [huggingface-cloth-segmentation repository](https://github.com/wildoctopus/huggingface-cloth-segmentation):

```bash
# Example: Download and place in project root
wget https://huggingface.co/levihsu/OOTDiffusion/resolve/main/cloth_segm.pth
```

#### U2Net Human Segmentation

Download U2Net weights for human segmentation:

```bash
# Download from official U2Net repository
# Place in appropriate location and update U2NET_SEGM_CHECKPOINT_PATH
```

## GPU Setup (Optional but Recommended)

For optimal performance, ensure CUDA is properly configured:

### Check CUDA Installation

```python
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"CUDA version: {torch.version.cuda}")
print(f"GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'None'}")
```

### Install CUDA-Compatible PyTorch

If CUDA is not detected, install the appropriate PyTorch version:

```bash
# For CUDA 11.8
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# For CUDA 12.1
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

## Troubleshooting

### Common Issues

#### Issue: Import Errors

**Solution**: Ensure all dependencies are installed:

```bash
pip install -r requirements.txt
```

#### Issue: CUDA Out of Memory

**Solution**: Reduce batch size or image resolution in your code.

#### Issue: Model Checkpoint Not Found

**Solution**: Ensure checkpoint paths in `.env` are correct and files exist.

#### Issue: Dependency Conflicts

**Solution**: Use conda environment to isolate dependencies:

```bash
conda env create -f environment.yml
conda activate opentryon
```

### Getting Help

If you encounter issues:

1. Check the [Troubleshooting Guide](../advanced/troubleshooting.md)
2. Search [GitHub Issues](https://github.com/tryonlabs/opentryon/issues)
3. Ask on [Discord](https://discord.gg/T5mPpZHxkY)

## Next Steps

Once installed, check out the [Quick Start Guide](quickstart.md) to begin using OpenTryOn!

