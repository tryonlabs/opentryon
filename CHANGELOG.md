# Changelog

All notable changes to OpenTryOn will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.2] - 27 December 2025

### Added

#### 🎨 Image Generation
- **OpenAI GPT-Image Integration**: Added support for OpenAI's GPT-Image models
  - GPT-Image-1: High-quality image generation and editing
  - GPT-Image-1.5: Enhanced version with improved quality, better prompt understanding, and improved consistency
  - Support for text-to-image, image-to-image editing, multi-image composition, and mask-based editing
  - Background control, quality settings, and multiple output images
  - Full documentation and examples

#### 🎬 Video Generation
- **OpenAI Sora Video Generation**: Added support for OpenAI's Sora video models
  - Sora 2: Fast, high-quality video generation
  - Sora 2 Pro: Enhanced quality with superior temporal consistency
  - Text-to-video and image-to-video generation
  - Support for 4, 8, and 12-second videos with multiple resolutions (720p to Full HD)
  - Synchronous (blocking) and asynchronous (callback-based) wait modes
  - Progress tracking and status monitoring
  - Comprehensive documentation

- **Google Veo 3 Video Generation**: Added support for Google's Veo 3 video generation model
  - Generate high-quality, cinematic videos from text or images
  - Realistic motion and temporal consistency
  - Fine-grained control over style and camera dynamics
  - Full API integration with detailed documentation

#### 🤖 AI Agents
- **Virtual Try-On Agent (VTOnAgent)**: New LangChain-based AI agent for intelligent virtual try-on operations
  - Intelligent agent that can analyze prompts and automatically select appropriate models
  - Support for multiple virtual try-on providers (Kling AI, Segmind, Nova Canvas)
  - Tool-based architecture for flexible model selection
  - Comprehensive documentation and usage examples

- **Model Swap Agent (ModelSwapAgent)**: New AI agent for replacing models while preserving outfits
  - Automatically swaps models in images while maintaining outfit consistency
  - Support for multiple image generation models (Nano Banana, Nano Banana Pro, FLUX 2 Pro, FLUX 2 Flex)
  - Intelligent prompt engineering for model swapping
  - Full documentation with examples

#### 📚 Documentation & Infrastructure
- Added comprehensive documentation for all new features
- Created issue and PR templates for better contribution workflow
- Added security policy (SECURITY.md)
- Enhanced documentation with detailed API references
- Added quickstart guides for new features

### Changed
- Updated README.md with information about new features
- Enhanced project structure to accommodate new modules
- Improved code organization with new API adapters and agents

### Fixed
- Fixed broken link in fashion-prompt-builder documentation

## [0.0.1] - 16 December 2025

### Added
- Initial release of OpenTryOn
- Virtual Try-On support (Amazon Nova Canvas, Kling AI, Segmind)
- Image Generation (Nano Banana, FLUX.2, Luma AI)
- Video Generation (Luma AI Dream Machine)
- Datasets module (Fashion-MNIST, VITON-HD)
- Garment preprocessing and segmentation
- Pose estimation
- Interactive demos
- Complete documentation

[0.0.2]: https://github.com/tryonlabs/opentryon/releases/tag/v0.0.2
[0.0.1]: https://github.com/tryonlabs/opentryon/releases/tag/v0.0.1

