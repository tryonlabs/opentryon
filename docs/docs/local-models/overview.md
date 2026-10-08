# Local Models Overview

OpenTryOn provides adapters for local inference models that run directly on your hardware. Unlike the cloud API adapters in `tryon.api`, these models require local GPU resources but offer several advantages:

- **No API costs**: Run unlimited inferences without per-request charges
- **Privacy**: Your data never leaves your machine
- **Customization**: Fine-tune models for your specific use case
- **Offline capability**: Work without internet connectivity

Adding a new local or API model? Start with
[Model Integration Guidelines](../advanced/model-integration-guidelines.md).

## Available Models

| Model | Type | VRAM Required | Speed | Use Case |
|-------|------|--------------|-------|----------|
| [FLUX.2-dev Turbo](./flux2-turbo) | Image Generation | 12GB+ | 6x faster | Fast text-to-image, image-to-image |
| [Kimi-VL](./kimi-vl) | Image/Video Understanding | 24GB+ | - | Open-weight counterpart to the Kimi K2.6/K2.7 Code APIs |
| [Qwen3.8](./qwen3.8) | Image/Video Understanding | ~50GB+ (bf16) | - | Open Qwen3.8-27B: multimodal understand + thinking; counterpart to DashScope Max |
| [Hy4 preview](./hy4) | Text LLM (vLLM/SGLang) | Datacenter (FP8 ~770GB+, TP=8) | - | Open `tencent/Hy4-preview`; OpenTryOn calls localhost OpenAI API — not in-process |
| [Qwen-Image](./qwen-image) | Image Generation / Edit / VTON | ~40GB+ (bf16; offload default) | - | Open Qwen-Image-2512 T2I + Edit-2511 I2I; counterpart to DashScope qwen-image |
| [LTX-2.5](./ltx-2.5) | Video Generation | 16GB+ (24GB+ preferred) | Distilled few-step | Local T2V / I2V with synced audio |
| [Cosmos 3 Nano](./cosmos3) | Video Generation | Large (16B, BF16 only; offload optional) | Heavy | Local T2V / I2V; self-hosted twin of NIM `cosmos3` |
| [MiniMax H3](./minimax-h3) | Video Generation | 80GB+ preferred (offload; ~75GB host RAM if int8) | Heavy | Local T2V / I2V with stereo audio (768p base) |
| [Wan 2.2](./wan-2.2) | Video Generation | ~12GB+ (TI2V-5B) | Moderate | Local T2V / I2V open weights (Wan 3.0 is API-only) |
| [Leffa](./leffa) | Virtual Try-On | 12GB+ recommended | ~6s on A100 | Dedicated local VTON (CVPR 2025; MIT code) |
| [FASHN VTON v1.5](./fashn-vton) | Virtual Try-On | Consumer GPU (VRAM not published) | Moderate | Maskless pixel-space VTON, **Apache-2.0** code + weights; model-worn or flat-lay garments |
| [CatVTON](./catvton) | Virtual Try-On | &lt;8GB @ 1024×768 | Moderate | Concatenation VTON (ICLR 2025; **CC BY-NC-SA**) |
| [DeepSeek-VL2](./deepseek-vl2) | Image/Video Understanding | Single-GPU (tiny) to 40GB+ (small/base) | - | Open DeepSeek-VL2; no first-party hosted API exists. Needs DeepSeek's own `deepseek_vl2` package (not on PyPI) |
| [DeepSeek-OCR](./deepseek-ocr) | Document/Image OCR | Requires flash-attn + CUDA | - | "Contexts Optical Compression"; care labels, size tags, SKU sheets. No first-party hosted API exists |
| [Ternary Bonsai 2 27B](./ternary-bonsai) | Image/Text Understanding | 5.9-8.5GB on disk (ternary-quantized) | Fast (CPU/Metal-friendly) | OpenAI-compatible client for PrismML's own llama.cpp/MLX server — no torch needed on the OpenTryOn side |
| [Liquid d1](./liquid-d1) | Decision model (`decide`) | d1-3B ~3B / d1-omni-600M ~0.6B | Fast (1 forward pass) | Calibrated yes/no, choice, score answers about text, images (and speech for omni); needs transformers>=5.15 |
| [EmbeddingGemma 2](./embeddinggemma) | Multimodal embeddings (`embed`) | 270M-740M by modality | Fast | One 768-d space for text, code, image, video, audio; Apache-2.0 tag |
| [pplx-embed-v2-late](./pplx-embed) | Multi-vector retrieval (`embed`) | 0.6B (340M active) / 9B (7.4B active) | Moderate | ColBERT-style MaxSim over text, images and pages; MIT; no hosted API |
| [Limite 1B - Violetto](./limite) | Text Math Reasoning (out of fashion/media scope) | ~2.1GB | Fast | Text-only 1B math model; named-model-only, not a fashion/media fit — see the page for why it's here |

## Requirements

Most local models require:

- **CUDA-capable GPU** (NVIDIA recommended)
- **PyTorch 2.1+** with CUDA support
- **diffusers >= 0.29.0**
- **transformers**

Exception: [Ternary Bonsai 2 27B](./ternary-bonsai) and [Hy4 preview](./hy4)
are OpenAI-compatible HTTP clients for a server you run yourself (locally or
on your own cluster) — they need no `opentryon[local]` extra or GPU on the
machine running OpenTryOn itself.
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

