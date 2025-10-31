# TryOnDiffusion: A Tale of Two UNets

This directory contains an open-source PyTorch implementation of **TryOnDiffusion**, based on the paper ["TryOnDiffusion: A Tale Of Two UNets"](https://arxiv.org/abs/2306.08276) by Google Research.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Key Components](#key-components)
- [Directory Structure](#directory-structure)
- [Prerequisites](#prerequisites)
- [Data Format](#data-format)
- [Training](#training)
- [Inference](#inference)
- [Configuration](#configuration)
- [Implementation Details](#implementation-details)

## 🎯 Overview

TryOnDiffusion is a diffusion-based virtual try-on model that uses a dual UNet architecture to generate realistic images of people wearing different garments. The model consists of two parallel UNets:

1. **Person UNet**: Generates the final output image of the person wearing the garment
2. **Garment UNet**: Processes the segmented garment information

The model uses pose embeddings for both the person and garment to condition the generation process, enabling accurate garment placement and realistic results.

## 🏗️ Architecture

### Dual UNet Structure

The implementation features two interconnected UNets:

- **Person UNet**: Takes noisy person image concatenated with cloth-agnostic RGB (`zt`) and generates the final try-on result
- **Garment UNet**: Processes segmented garment (`ic`) to provide features for cross-attention in the Person UNet

### Key Architectural Features

1. **Cross-Attention Mechanism**: Person UNet attends to garment features at multiple scales
2. **Self-Attention with Pose Conditioning**: Pose embeddings are integrated via attention mechanisms
3. **FiLM (Feature-wise Linear Modulation)**: CLIP-like pooled embeddings modulate features using FiLM layers
4. **Attention Pooling**: 1D attention pooling reduces pose keypoints to compact embeddings

## 📦 Key Components

### 1. `diffusion.py` - Diffusion Model

The main diffusion model class that handles:

- **Noise Scheduling**: Linear beta scheduler for diffusion process
- **Training**: Forward diffusion, noise prediction, and loss computation
- **Sampling**: DDPM-based sampling with EMA model support
- **Noise Augmentation**: Gaussian smoothing during training and inference (σ ∈ [0.4, 0.6])

**Key Methods:**
- `add_noise_to_img()`: Adds noise to images based on timestep
- `sample()`: Generates images via reverse diffusion process
- `single_epoch()`: Training/validation loop
- `fit()`: Main training function

### 2. `network.py` - Dual UNet Architecture

Contains the neural network architecture:

#### Core Components:

- **`UNet64`**: 64×64 input resolution variant
- **`UNet128`**: 128×128 input resolution variant

#### Building Blocks:

- **`DownSample`**: Channel-preserving downsampling (rearranges 2×2 patches)
- **`UpSample`**: Nearest-neighbor upsampling with convolution
- **`AttentionPool1d`**: CLIP-inspired 1D attention pooling for pose embeddings
- **`FiLM`**: Feature-wise Linear Modulation for conditioning
- **`SelfAttention`**: Self-attention with pose conditioning
- **`CrossAttention`**: Cross-attention between person and garment features
- **`ResBlockNoAttention`**: Residual blocks without attention
- **`ResBlockAttention`**: Residual blocks with self and cross-attention

#### Architecture Flow:

```
Input (zt, ic) → Initial Convolutions
    ↓
Encoder Blocks (Downsampling)
    ↓
Bottleneck Blocks (with Attention)
    ↓
Decoder Blocks (Upsampling with Skip Connections)
    ↓
Final Convolution → Output
```

### 3. `ema.py` - Exponential Moving Average

Exponential Moving Average (EMA) for model weights:

- Improves training stability and inference quality
- Starts updating after `step_start_ema` steps (default: 2000)
- Uses beta decay (default: 0.995)

### 4. `trainer.py` - Training Configuration

Example training script with `ArgParser` class for configuration:

- Dataset paths for training and validation
- Hyperparameters (learning rate, batch size, etc.)
- Training frequencies (loss calculation, image logging, model saving)

### 5. `utils/` - Utility Functions

- **`dataloader_train.py`**: `UNetDataset` class for loading preprocessed data
- **`utils.py`**: Helper functions (Gaussian smoothing, image I/O, folder creation)

### 6. `pre_processing/` - Data Preprocessing

Preprocessing utilities for preparing training data:

- **Pose Estimation**: OpenPose-based keypoint extraction
- **Pose Embeddings**: Autoencoder networks for human and garment pose embeddings
- **Garment Segmentation**: U2Net-based cloth segmentation
- **Cloth-Agnostic RGB**: Generation of person images without clothing

See `pre_processing/README.md` for detailed preprocessing instructions.

## 📁 Directory Structure

```
tryondiffusion/
├── __init__.py
├── diffusion.py          # Main diffusion model class
├── network.py            # Dual UNet architecture
├── ema.py                # Exponential Moving Average
├── trainer.py            # Training configuration example
├── utils/                # Utility functions
│   ├── dataloader_train.py  # Dataset class for training
│   └── utils.py          # Helper functions
└── pre_processing/       # Data preprocessing modules
    ├── openpose_pytorch/      # OpenPose implementation
    ├── garment_pose_embedding/ # Garment pose embedding network
    ├── human_pose_embedding/  # Human pose embedding network
    ├── u2net_cloth_seg/       # U2Net cloth segmentation
    └── ...
```

## 🔧 Prerequisites

### Required Dependencies

```python
torch >= 2.0.0
torchvision
einops
numpy
opencv-python
scikit-image
```

### Data Requirements

Before training, you need to prepare:

1. **Pose Embeddings**: Pre-computed pose embeddings for both person (`jp`) and garment (`jg`)
2. **Segmented Garments**: U2Net-segmented garment images (`ic`)
3. **Cloth-Agnostic RGB**: Person images without clothing (`ia`)
4. **Ground Truth**: Target person images with source clothing (`ip`)

## 📊 Data Format

### Directory Structure

```
data/
├── train/
│   ├── ip/  # Target person images (ground truth)
│   ├── jp/  # Person pose embeddings (.pt files)
│   ├── jg/  # Garment pose embeddings (.pt files)
│   ├── ia/  # Cloth-agnostic RGB images
│   └── ic/  # Segmented garment images
└── validation/
    ├── ip/
    ├── jp/
    ├── jg/
    ├── ia/
    └── ic/
```

### Data Specifications

- **Images**: RGB images in common formats (JPG, PNG)
- **Pose Embeddings**: PyTorch tensor files (`.pt`) with shape `[pose_embed_dim]`
- **Image Size**: Automatically resized to UNet input size (64×64 or 128×128)
- **Normalization**: Images normalized to [-1, 1] range

## 🚀 Training

### Basic Training Setup

```python
from tryondiffusion.diffusion import Diffusion
from tryondiffusion.trainer import ArgParser

# Configure training parameters
args = ArgParser()
args.run_name = "tryon_experiment_1"
args.train_ip_folder = "data/train/ip"
args.train_jp_folder = "data/train/jp"
args.train_jg_folder = "data/train/jg"
args.train_ia_folder = "data/train/ia"
args.train_ic_folder = "data/train/ic"

args.validation_ip_folder = "data/validation/ip"
args.validation_jp_folder = "data/validation/jp"
args.validation_jg_folder = "data/validation/jg"
args.validation_ia_folder = "data/validation/ia"
args.validation_ic_folder = "data/validation/ic"

args.batch_size_train = 4
args.batch_size_validation = 1
args.total_steps = 100000
args.lr = 0.0  # Will be scheduled
args.start_lr = 0.0
args.stop_lr = 0.0001
args.pct_increasing_lr = 0.02

# Initialize diffusion model
diffusion = Diffusion(
    device="cuda",
    pose_embed_dim=8,  # Dimension of pose embeddings
    time_steps=256,
    beta_start=1e-4,
    beta_end=0.02,
    unet_dim=64,  # or 128 for higher resolution
    noise_input_channel=3,
    beta_ema=0.995
)

# Prepare data and optimizer
diffusion.prepare(args)

# Start training
diffusion.fit(args)
```

### Training Parameters

#### Diffusion Parameters

- `pose_embed_dim`: Dimension of pose embeddings (typically 8)
- `time_steps`: Number of diffusion timesteps (256)
- `beta_start`: Starting noise level (1e-4)
- `beta_end`: Ending noise level (0.02)
- `unet_dim`: UNet input resolution (64 or 128)
- `noise_input_channel`: Channels in noise input (3)
- `beta_ema`: EMA decay rate (0.995)

#### Training Parameters

- `batch_size_train`: Training batch size
- `batch_size_validation`: Validation batch size
- `total_steps`: Total training steps
- `start_lr`: Initial learning rate (for warmup)
- `stop_lr`: Final learning rate
- `pct_increasing_lr`: Percentage of steps for learning rate warmup (0.02 = 2%)

#### Frequency Parameters

- `calculate_loss_frequency`: Epochs between validation loss calculation
- `image_logging_frequency`: Epochs between saving sample images
- `model_saving_frequency`: Epochs between model checkpoint saves

### Training Output

Training creates:
- `models/{run_name}/`: Model checkpoints
  - `ckpt_{epoch}.pt`: Main model weights
  - `ema_ckpt_{epoch}.pt`: EMA model weights
  - `optim_{epoch}.pt`: Optimizer state
- `results/{run_name}/images/`: Generated samples during training

## 🔮 Inference

### Sampling from Trained Model

```python
from tryon.preprocessing import load_pose_embed, read_img
from tryondiffusion.diffusion import Diffusion
import torch

# Load trained model
diffusion = Diffusion(
    device="cuda",
    pose_embed_dim=8,
    time_steps=256,
    beta_start=1e-4,
    beta_end=0.02,
    unet_dim=64,
    noise_input_channel=3,
    beta_ema=0.995
)

# Load checkpoint
checkpoint = torch.load("models/run_name/ema_ckpt_100.pt")
diffusion.ema_net.load_state_dict(checkpoint)

# Prepare conditional inputs
# ic: segmented garment [B, 3, H, W]
# jp: person pose embedding [B, pose_embed_dim]
# jg: garment pose embedding [B, pose_embed_dim]
# ia: cloth-agnostic RGB [B, 3, H, W]

ic = read_img("garment_segmented.jpg")  # Preprocess to tensor
jp = load_pose_embed("person_pose.pt")
jg = load_pose_embed("garment_pose.pt")
ia = read_img("cloth_agnostic.jpg")  # Preprocess to tensor

# Generate image
conditional_inputs = (ic, jp, jg, ia)
generated_image = diffusion.sample(
    use_ema=True,  # Use EMA model for better quality
    conditional_inputs=conditional_inputs
)

# Save result
cv2.imwrite("output.jpg", generated_image[0].permute(1, 2, 0).cpu().numpy())
```

## ⚙️ Configuration

### Learning Rate Schedule

The implementation uses a warmup learning rate schedule:

```python
def schedule_lr(total_steps, start_lr=0.0, stop_lr=0.0001, pct_increasing_lr=0.02):
    # Warmup phase: linearly increase from start_lr to stop_lr
    # Constant phase: maintain stop_lr
```

### Noise Augmentation

During training and inference:
- Gaussian smoothing with σ sampled uniformly from [0.4, 0.6]
- Applied to cloth-agnostic RGB (`ia`) and segmented garment (`ic`)
- Applied to input noise during inference

## 🔬 Implementation Details

### Dual UNet Interaction

1. **Encoder Path**: Both UNets encode their respective inputs independently
2. **Bottleneck**: Person UNet uses cross-attention to attend to garment features
3. **Decoder Path**: Person UNet decodes with skip connections from its encoder
4. **Feature Fusion**: Garment features are fused at multiple scales via cross-attention

### Attention Mechanisms

#### Self-Attention
- Processes person features with pose conditioning
- Pose embeddings concatenated to key/value
- Enables spatial reasoning with pose information

#### Cross-Attention
- Person UNet queries garment features
- Enables garment-aware person generation
- Applied at bottleneck layers (16×16 and 32×32 resolutions)

### Pose Embedding Processing

1. **Concatenation**: Person and garment pose embeddings concatenated
2. **Attention Pooling**: 1D attention reduces to single embedding vector
3. **Time Conditioning**: Sinusoidal positional encoding for timestep
4. **Noise Injection**: Gaussian smoothing adds stochasticity
5. **FiLM Modulation**: Embedding modulates features via FiLM layers

### Training Process

1. **Forward Diffusion**: Add noise to ground truth image `ip`
2. **Concatenation**: Concatenate noisy image with cloth-agnostic RGB
3. **Prediction**: Network predicts noise given timestep and conditions
4. **Loss**: MSE between predicted and actual noise
5. **EMA Update**: Update EMA model weights after each step

### Sampling Process

1. **Initialize**: Random noise + cloth-agnostic RGB
2. **Iterative Denoising**: For each timestep t from T to 1:
   - Predict noise using network
   - Update image using DDPM formula
   - Add noise if t > 1
3. **Post-processing**: Clamp to [0, 1] and convert to uint8

## 📝 Notes

### Future Enhancements (TODOs in code)

1. **Classifier-Free Guidance**: Conditional dropout during training (10% of time)
2. **Guidance Weight**: Apply guidance weight of 2.0 during inference
3. **TensorBoard Logging**: Add logging for training metrics

### Performance Considerations

- **GPU Memory**: UNet128 requires more memory than UNet64
- **Batch Size**: Adjust based on GPU memory availability
- **Mixed Precision**: Uses `torch.cuda.amp` for faster training

## 📚 References

- **Paper**: [TryOnDiffusion: A Tale Of Two UNets](https://arxiv.org/abs/2306.08276)

## 🤝 Contributing

This is an open-source implementation. Contributions are welcome! Please ensure:

1. Code follows the existing style
2. Add tests for new features
3. Update documentation as needed
4. Follow the paper's methodology

## 📄 License

See the main repository LICENSE file for license information.

