---
slug: /
title: OpenTryOn
description: OpenTryOn is an open-source AI toolkit for fashion technology and virtual try-on. v0.0.4 adds LTX-2.5, Hailuo 2.3, MiniMax H3 (API + local), Wan dual-path, Runway Gen-4.5, and Qwen3.8 understand (API + local) on top of the v0.0.3 CLI/MCP media surface.
keywords:
  - virtual try-on
  - fashion AI
  - AI toolkit
  - virtual try-on API
  - fashion technology
  - garment segmentation
  - TryOnDiffusion
  - open source AI
  - fashion tech
  - virtual fitting
  - AI fashion
  - computer vision
  - diffusion models
  - fashion datasets
  - VITON-HD
  - Fashion-MNIST
  - Subjects200K
  - Amazon Nova Canvas
  - Kling AI
  - Segmind
  - Nano Banana
  - Gemini Image Generation
  - FLUX.2
  - GPT-Image-1
  - OpenAI
  - Sora 2
  - video generation
  - AI video
  - Kimi K2.6
  - Kimi K2.7 Code
  - Kimi K3
  - Moonshot AI
  - MiniMax H3
  - MiniMax H3 Max
  - Muse Image
  - Hailuo
  - multimodal understanding
  - opentryon CLI
  - MCP
  - Model Context Protocol
  - TryOn Studio
  - FastMCP
  - Pruna
  - Seedance
  - Seedream
  - Ideogram
  - Grok Imagine
  - FASHN
  - OpenAPI
  - Swagger
image: /img/opentryon-social-card.jpg
---

# Welcome to OpenTryOn

OpenTryOn is an open-source AI toolkit for fashion technology and virtual try-on. **Current release: [v0.0.4](https://pypi.org/project/opentryon/0.0.4/)** on PyPI.

## 🎯 What is OpenTryOn?

OpenTryOn gives you four ways to run fashion AI models:

1. **CLI** — `opentryon <service> --model <model> …`
2. **MCP server** — tools for Cursor, Claude, and any MCP client ([guide](getting-started/mcp), [in-repo README](https://github.com/tryonlabs/opentryon/blob/main/mcp-server/README.md))
3. **TryOn Studio** — Next.js playground that talks to the MCP server ([setup and screens](getting-started/tryon-studio))
4. **Python APIs** — `tryon.api` adapters + `invoke_model()`

Plus preprocessing, datasets, Gradio demos, and TryOnDiffusion research code.

## 🚀 Key Features (v0.0.4)

### Developer surfaces
- Unified **registry-driven CLI** with `--dry-run`
- **FastMCP** server — every registry model is a tool ([MCP Server](getting-started/mcp))
- **TryOn Studio** — Agent chat, Connect, and capability screens over MCP HTTP ([setup](getting-started/tryon-studio))
- **OpenAPI / Swagger** + **Postman** snapshots for upstream media APIs ([guide](getting-started/openapi-swagger))
- **Model integration guidelines** for Path A (API) vs Path B (local)

### Virtual try-on
Cloud adapters including FLUX VTO, **Google Vertex Virtual Try-On**, **OutfitAnyone-Plus**, **Photoroom** (try-on + virtual model), Nova Canvas, Kling AI, Segmind, **Pruna P-Image-Try-On**, **FASHN**, Nano Banana 2 Lite composition, **Qwen-Image** (API + local), **Leffa** and **CatVTON** (local weights), and **Muse Image** composition.

### Image generate / edit
Nano Banana family, FLUX.2, GPT Image, Luma Photon, **Seedream 5.0 Pro**, **Ideogram 4.0**, **Grok Imagine Image**, **Pruna P-Image / P-Image-Ideogram / Edit / Upscale**, **Qwen-Image** (DashScope 3.0 + local 2512/Edit-2511), **Muse Image**, plus local FLUX.2-dev Turbo.

### Video
Veo, Sora, Luma Ray 2 + **Ray 3.2**, **Seedance 2.5**, **Kling 3.0 / Omni / Turbo**, **Grok Imagine Video**, Gemini Omni Flash, **Pruna P-Video / Replace / Avatar / Animate**, plus **LTX-2.5** (API + local), **Hailuo 2.3**, **MiniMax H3 / H3 Max** (API + local H3 + **Fal H3 Max**), **Wan** (2.x API + **Wan 3.0** API + local 2.2), **Runway Gen-4.5**.

### Understanding & other
**Kimi K2.6 / K2.7 Code / K3** (API), Kimi-VL & LLaVA-NeXT (local), **Qwen3.8-Max** (API) + **Qwen3.8-27B** (local), **Hy4 preview** (TokenHub + local vLLM/SGLang), BEN2 bg-remove, fashion datasets, garment/pose preprocessing.

### Interactive playground
**[TryOn Studio](getting-started/tryon-studio)** is the Next.js UI: Agent chat (`planner_agent`), Connect (MCP status + key passthrough), and capability screens (Image, VTON, Understand, Video, BG Remove). In-repo **Gradio** apps remain for extract-garment / model-swap / outfit-generator.

## 📚 What You'll Learn

In this documentation, you'll find:

- **[Installation Guide](getting-started/installation)**: Get OpenTryOn up and running (`pip install opentryon`)
- **[Quick Start](getting-started/quickstart)**: First successful runs
- **[Configuration](getting-started/configuration)**: API keys and `.env`
- **[Unified CLI](getting-started/cli)**: Service → model → params
- **[MCP Server](getting-started/mcp)**: Agent / IDE tool surface, plus the [`mcp-server` README](https://github.com/tryonlabs/opentryon/blob/main/mcp-server/README.md)
- **[TryOn Studio](getting-started/tryon-studio)**: Web UI setup, Agent, Connect, and capability screens
- **[OpenAPI & Postman](getting-started/openapi-swagger)**: Swagger for upstream media APIs
- **[Fashion ML Engineer Path](getting-started/fashion-ml)**: Train → eval → invoke → workflow (toward v0.1.0)
- **[Datasets Module](datasets/overview)**: Fashion-MNIST, VITON-HD, Subjects200K
- **[API Reference](api-reference/overview)**: Adapters and provider docs
- **[Examples](examples/basic-usage)**: Real-world usage examples
- **[Advanced Guides](advanced/training-guide)**: Training and customization
- **[Roadmap](community/roadmap)**: Shipped vs remaining work

## 🎓 Prerequisites

Before you begin, you should have:

- Python 3.10 or higher
- Basic knowledge of Python programming
- Familiarity with computer vision concepts (helpful but not required)
- CUDA-capable GPU (recommended for best performance)

## 💡 Quick Examples

Here are some simple examples to get you started:

### Virtual Try-On with Segmind

```python
from dotenv import load_dotenv
load_dotenv()

from tryon.api import SegmindVTONAdapter

# Initialize adapter
adapter = SegmindVTONAdapter()

# Generate virtual try-on
images = adapter.generate_and_decode(
    model_image="person.jpg",
    cloth_image="shirt.jpg",
    category="Upper body"
)

# Save result
images[0].save("result.png")
```

### Using Fashion-MNIST Dataset

```python
from tryon.datasets import FashionMNIST

# Create dataset instance (downloads automatically)
dataset = FashionMNIST(download=True)

# Load the dataset
(train_images, train_labels), (test_images, test_labels) = dataset.load(
    normalize=True,
    flatten=False
)

print(f"Training set: {train_images.shape}")  # (60000, 28, 28)
print(f"Class 0: {dataset.get_class_name(0)}")  # 'T-shirt/top'
```

### Garment Preprocessing

```python
from dotenv import load_dotenv
load_dotenv()

from tryon.preprocessing import segment_garment, extract_garment

# Segment garment
segment_garment(
    inputs_dir="data/original_cloth",
    outputs_dir="data/garment_segmented",
    cls="upper"
)

# Extract garment
extract_garment(
    inputs_dir="data/original_cloth",
    outputs_dir="data/cloth",
    cls="upper",
    resize_to_width=400
)
```

## 🤝 Get Involved

OpenTryOn is an open-source project, and we welcome contributions!

- **GitHub**: [github.com/tryonlabs/opentryon](https://github.com/tryonlabs/opentryon)
- **Discord**: [Join our community](https://discord.gg/T5mPpZHxkY)
- **Contributing**: See our [Contributing Guide](community/contributing)

## 📄 License

All material is made available under [Creative Commons BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/). You can use the material for non-commercial purposes, as long as you give appropriate credit and indicate any changes.

## 🗺️ Roadmap

Check out our [Roadmap](community/roadmap) to see what's coming next!

## 🆘 Need Help?

- Check our [Troubleshooting Guide](advanced/troubleshooting)
- Join our [Discord community](https://discord.gg/T5mPpZHxkY)
- Open an issue on [GitHub](https://github.com/tryonlabs/opentryon/issues)

---

Ready to get started? Head over to the [Installation Guide](getting-started/installation)!

