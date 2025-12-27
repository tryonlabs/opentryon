# OpenTryOn v0.0.2 Release Notes

## 🚀 OpenAI Integration & AI Agents - Enhanced Capabilities for Fashion AI

**Release Date**: 27 December 2025

We're excited to announce the release of OpenTryOn v0.0.2! This release introduces significant new features including OpenAI integrations for image and video generation, Google Veo 3 video generation, and two powerful AI agents for virtual try-on and model swapping.

## 🎉 What's New

### OpenAI Integration

#### Image Generation - GPT-Image Models
We've added full support for OpenAI's GPT-Image models, bringing professional-grade image generation capabilities to OpenTryOn:

- **GPT-Image-1.5** (Default): The latest model with enhanced quality, better prompt understanding, and improved consistency
- **GPT-Image-1**: High-quality image generation and editing

**Features:**
- Text-to-image generation
- Image-to-image editing
- Multi-image composition
- Mask-based editing with precise region control
- Background control and quality settings
- Multiple output images support

**Example Usage:**
```python
from tryon.api.openAI import GPTImageAdapter

# Initialize adapter (defaults to GPT-Image-1.5)
adapter = GPTImageAdapter()

# Generate image from text
images = adapter.generate_text_to_image(
    prompt="A fashion model wearing an elegant evening gown",
    size="1024x1024",
    quality="high"
)

# Edit existing image
images = adapter.generate_image_edit(
    images="person.jpg",
    prompt="Change the dress color to midnight blue"
)
```

**Documentation**: [GPT-Image API Reference](https://tryonlabs.github.io/opentryon/api-reference/gpt-image)

#### Video Generation - Sora Models
OpenTryOn now supports OpenAI's Sora video generation models for creating high-quality videos:

- **Sora 2** (Default): Fast, high-quality video generation
- **Sora 2 Pro**: Enhanced quality with superior temporal consistency

**Features:**
- Text-to-video generation
- Image-to-video generation (animate static images)
- Support for 4, 8, and 12-second videos
- Multiple resolutions (720p to Full HD)
- Two wait modes: synchronous (blocking) and asynchronous (callback-based)
- Progress tracking and status monitoring

**Example Usage:**
```python
from tryon.api.openAI import SoraVideoAdapter

# Initialize adapter
adapter = SoraVideoAdapter()

# Generate video from text
video_bytes = adapter.generate_text_to_video(
    prompt="A fashion model walking on a runway, elegant movements",
    duration=8,
    resolution="1280x768"
)

# Animate an image
video_bytes = adapter.generate_image_to_video(
    image="model.jpg",
    prompt="The model gracefully walking",
    duration=12
)
```

**Documentation**: [Sora Video API Reference](https://tryonlabs.github.io/opentryon/api-reference/sora-video)

### Google Veo 3 Video Generation

We've integrated Google's Veo 3 video generation model, providing another powerful option for creating cinematic videos:

**Features:**
- High-quality, cinematic video generation
- Text-to-video and image-to-video support
- Realistic motion and temporal consistency
- Fine-grained control over style and camera dynamics

**Example Usage:**
```python
from tryon.api import VeoAdapter

adapter = VeoAdapter()
video_bytes = adapter.generate_text_to_video(
    prompt="A fashion show with models showcasing elegant designs"
)
```

**Documentation**: [Veo Video Documentation](https://tryonlabs.github.io/opentryon/api-reference/veo-video)

### AI Agents

#### Virtual Try-On Agent (VTOnAgent)
A new intelligent agent that automates virtual try-on operations using LangChain:

**Features:**
- Automatically analyzes prompts and selects appropriate models
- Support for multiple virtual try-on providers (Kling AI, Segmind, Nova Canvas)
- Tool-based architecture for flexible model selection
- Intelligent decision-making for optimal results

**Example Usage:**
```python
from tryon.agents import VTOnAgent

# Initialize the agent
agent = VTOnAgent(llm_provider="openai")

# Generate virtual try-on
result = agent.generate(
    person_image="person.jpg",
    garment_image="shirt.jpg",
    prompt="Use Kling AI to create a virtual try-on of this shirt"
)
```

**Documentation**: [VTOn Agent Documentation](https://tryonlabs.github.io/opentryon/agents/vton-agent)

#### Model Swap Agent (ModelSwapAgent)
An AI agent that replaces models in images while preserving outfit consistency:

**Features:**
- Automatically swaps models while maintaining outfit consistency
- Support for multiple image generation models (Nano Banana, Nano Banana Pro, FLUX 2 Pro, FLUX 2 Flex)
- Intelligent prompt engineering for model swapping
- Preserves outfit details and styling

**Example Usage:**
```python
from tryon.agents import ModelSwapAgent

# Initialize agent with default Nano Banana Pro
agent = ModelSwapAgent(llm_provider="openai")

# Generate model swap
result = agent.generate(
    image="person_wearing_outfit.jpg",
    prompt="Replace with a professional Asian female model in her 30s, athletic build"
)
```

**Documentation**: [Model Swap Agent Documentation](https://tryonlabs.github.io/opentryon/agents/model-swap-agent)

## 📦 Installation

Upgrade to v0.0.2 using pip:

```bash
pip install --upgrade opentryon
```

Or install from source:

```bash
git clone https://github.com/tryonlabs/opentryon.git
cd opentryon
git checkout v0.0.2
pip install -e .
```

## 🔧 Configuration

### OpenAI API Key
For GPT-Image and Sora features, set your OpenAI API key:

```bash
export OPENAI_API_KEY="your-openai-api-key"
```

Or add to your `.env` file:
```
OPENAI_API_KEY=your-openai-api-key
```

### Google Veo API Key
For Veo video generation, set your Gemini API key:

```bash
export GEMINI_API_KEY="your-gemini-api-key"
```

## 📚 Documentation Updates

- Added comprehensive API reference for GPT-Image models
- Added comprehensive API reference for Sora video models
- Added documentation for VTOn Agent
- Added documentation for Model Swap Agent
- Added Veo 3 video generation documentation
- Updated quickstart guides with new features
- Enhanced examples and use cases

## 🔄 Migration Guide

### From v0.0.1 to v0.0.2

No breaking changes! All existing code should continue to work. The new features are additive:

- Existing virtual try-on adapters remain unchanged
- Existing image generation adapters remain unchanged
- New OpenAI and agent modules are additional features
- No changes required to existing code

## 🐛 Bug Fixes

- Fixed broken link in fashion-prompt-builder documentation

## 🙏 Acknowledgments

Thank you to all contributors who made this release possible! Special thanks to:
- Contributors who added OpenAI integration
- Contributors who implemented the AI agents
- Community members who provided feedback and testing

## 📝 Full Changelog

For a complete list of changes, see [CHANGELOG.md](CHANGELOG.md).

## 🔗 Links

- **Documentation**: https://tryonlabs.github.io/opentryon/
- **GitHub Repository**: https://github.com/tryonlabs/opentryon
- **Discord Community**: https://discord.gg/T5mPpZHxkY
- **Issues**: https://github.com/tryonlabs/opentryon/issues

## 📄 License

This release is licensed under CC BY-NC 4.0. See [LICENSE](LICENSE) for details.

---

**Note**: This is an alpha release. We welcome feedback and contributions from the community!

