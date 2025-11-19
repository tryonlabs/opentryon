# Roadmap

> **Last Updated**: November 18, 2025 | **Timeline**: November 2025 - April 2026

## Roadmap Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│ COMPLETED (Q4 2025 - November 2025)                                    │
├─────────────────────────────────────────────────────────────────────────┤
│ ✓ Repository rebranded: TryOnDiffusion → OpenTryOn                      │
│ ✓ Datasets module (Fashion-MNIST, VITON-HD) with class-based adapters   │
│ ✓ Virtual Try-On adapters: Amazon Nova Canvas, Kling AI, Segmind        │
│ ✓ Enhanced documentation                                                 │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ IN PROGRESS (November 17-30, 2025)                                      │
├─────────────────────────────────────────────────────────────────────────┤
│ • Dataset module testing and refinement                                 │
│ • API adapter pattern standardization                                   │
│ • Documentation improvements                                             │
│ • Image Generation model integrations                                   │
│    - Closed-source: Nano Banana, GPT-Image-1, FLUX Kontext Pro          │
│    - Open-source: FLUX.1-dev and other open-source models               │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ PLANNED (December 2025 - January 2026)                                  │
├─────────────────────────────────────────────────────────────────────────┤
│ Core API Infrastructure                                                 │
│    • Base provider classes/interfaces (BaseProvider, BaseVTONAdapter)    │
│    • Unified API response types (GenerationResponse, VTONResponse)      │
│    • Configuration management, error handling, retry logic               │
│    • VirtualTryOn unified interface                                     │
│    • Standardize existing adapters (Nova Canvas, Kling AI, Segmind)    │
│                                                                          │
│ Image Generation & Model Integration (December 2025)                   │
│    • ImageGenerator unified interface                                   │
│    • Model registry system                                              │
│    • Additional open-source image generation models                     │
│                                                                          │
│ Video Generation Capabilities                                          │
│    • VideoGenerator unified interface                                   │
│    • Closed-source providers: SORA2, Kling AI, LUMA Ray                │
│    • Open-source models from GitHub, HuggingFace                        │
│                                                                          │
│ Open-Source Virtual Try-On Models                                       │
│    • Image VTON: Leffa, DreamO, Voost, IDM-VTON, CatVTON               │
│    • Video VTON: Video VTON models                                     │
│    • 3D VTON: Open-source 3D virtual try-on models                     │
│    • Integration with HuggingFace and GitHub models                    │
│                                                                          │
│ Agentic AI System for PDP Optimization                                 │
│    • Multi-agent system for product detail page evaluation             │
│    • LLM and VLM integration for analysis and optimization             │
│    • Automated PDP content analysis and recommendations                │
│                                                                          │
│ Testing & Quality                                                       │
│    • Unit/integration tests, >85% coverage                              │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ EXPLORING (February - April 2026)                                       │
├─────────────────────────────────────────────────────────────────────────┤
│ • Additional providers: Fashn AI, TryOnLabs, Qwen-Image                │
│ • HuggingFace model loading utilities                                   │
│ • CLI improvements (`ot generate`, `ot tryon`, `ot video`, `ot agent`) │
│ • Additional datasets (DeepFashion, FashionGen)                        │
│ • Enhanced agentic AI capabilities                                      │
│ • Advanced features: async/await, caching, batch processing (if time)  │
└─────────────────────────────────────────────────────────────────────────┘
```

## Detailed Breakdown

### Completed (Q4 2025 - November 2025)

- Repository rebranding, documentation updates
- **Datasets Module**: Fashion-MNIST, VITON-HD with class-based adapter pattern
- **Virtual Try-On Adapters**: Amazon Nova Canvas, Kling AI, Segmind

### In Progress (November 17-30, 2025)

- [ ] Dataset module testing and refinement
- [ ] API adapter pattern standardization
- [ ] Documentation improvements
- [ ] **Image Generation Model Integrations**:
- [ ] Nano Banana image generation adapter (closed-source)
- [ ] GPT-Image-1 adapter (closed-source)
- [ ] FLUX Kontext Pro adapter (closed-source)
- [ ] FLUX.1-dev adapter (open-source)
- [ ] Additional open-source image generation models from HuggingFace/GitHub

### Planned (December 2025 - January 2026)

**December 2025: Core API Infrastructure**

- [ ] Base provider classes/interfaces (`BaseProvider`, `BaseVTONAdapter`)
- [ ] Unified API response types (`GenerationResponse`, `VTONResponse`)
- [ ] Configuration management, error handling, retry logic
- [ ] VirtualTryOn unified interface
- [ ] Standardize existing adapters (Nova Canvas, Kling AI, Segmind)

**December 2025: Image Generation Unified Interface**

- [ ] ImageGenerator unified interface
- [ ] Model registry system for image generation models
- [ ] Standardize image generation adapters
- [ ] Unit/integration tests for image generation, >90% coverage

**January - February 2026: Video Generation & Agentic AI**

- [ ] VideoGenerator unified interface
- [ ] Video providers: SORA2, Kling AI, LUMA Ray (closed-source)
- [ ] Open-source video models from GitHub, HuggingFace
- [ ] Agentic AI system for PDP (Product Detail Page) optimization
- [ ] LLM and VLM integration for content analysis
- [ ] Automated PDP evaluation and optimization pipeline

**January - February 2026: Open-Source Virtual Try-On Models**

- [ ] Image VTON models: Leffa, DreamO, Voost, IDM-VTON, CatVTON
- [ ] Video VTON models integration
- [ ] 3D VTON models integration
- [ ] HuggingFace model loading utilities for VTON models
- [ ] GitHub model integration framework

### Exploring (February - April 2026)

- [ ] Additional providers: Fashn AI, TryOnLabs, Qwen-Image
- [ ] Additional open-source VTON models from community
- [ ] CLI improvements (`ot generate`, `ot tryon`, `ot edit`, `ot list-models`, `ot video`, `ot agent`)
- [ ] Additional datasets (DeepFashion, FashionGen)
- [ ] Advanced features: async/await, caching, batch processing (if time permits)
- [ ] Enhanced agentic AI capabilities and integrations

## Success Metrics

**November 2025**: ✓ Datasets module (2 datasets), ✓ 3 VTON adapters (Nova Canvas, Kling AI, Segmind), Image generation adapters (Nano Banana, GPT-Image-1, FLUX Kontext Pro, FLUX.1-dev), >80% test coverage

**December 2025**: Base architecture, Unified VirtualTryOn interface, ImageGenerator unified interface, Model registry system, >85% test coverage

**January - February 2026**: VideoGenerator interface, Video providers (SORA2, Kling AI, LUMA Ray), Open-source VTON models (Leffa, DreamO, Voost, IDM-VTON, CatVTON, Video VTON, 3D VTON), Agentic AI system for PDP optimization, >90% coverage

**February - April 2026**: Additional providers, CLI improvements, Enhanced DX, Advanced agentic AI features

## Contributor Roadmap

> **For Contributors**: This section highlights areas where we need your help! Pick a task that matches your skills and interests.

### Good First Issues (Great for New Contributors)

These are perfect for getting started with the project:

#### Documentation & Examples
- [ ] **Documentation**: Improve README examples and add code snippets
- [ ] **Tutorials**: Create Jupyter notebook tutorials for datasets module
- [ ] **Examples**: Add usage examples for each API adapter
- [ ] **Type Hints**: Add type hints to existing functions and classes
- **Labels**: `good first issue`, `documentation`, `help wanted`

#### Testing & Quality
- [ ] **Unit Tests**: Write tests for dataset loaders (Fashion-MNIST, VITON-HD)
- [ ] **Integration Tests**: Add tests for API adapters (Nova Canvas, Kling AI, Segmind)
- [ ] **Test Coverage**: Improve test coverage for existing modules
- **Labels**: `good first issue`, `testing`, `help wanted`

#### Code Quality
- [ ] **Linting**: Fix linting errors and improve code style
- [ ] **Error Handling**: Improve error messages and exception handling
- [ ] **Code Comments**: Add docstrings and inline comments
- **Labels**: `good first issue`, `code quality`, `help wanted`

### Intermediate Contributions

For contributors with some experience:

#### API Adapters & Integrations
- [ ] **Base Classes**: Implement `BaseProvider` and `BaseVTONAdapter` abstract classes
- [ ] **Response Types**: Create unified response types (`GenerationResponse`, `VTONResponse`)
- [ ] **Error Handling**: Implement retry logic with exponential backoff
- [ ] **Configuration**: Build configuration management system
- **Labels**: `intermediate`, `api`, `help wanted`

#### Image Generation Providers (November 2025 - High Priority)
- [ ] **Nano Banana**: Implement Nano Banana image generation adapter (closed-source)
- [ ] **GPT-Image-1**: Integrate GPT-Image-1 API (closed-source)
- [ ] **FLUX Kontext Pro**: Add FLUX Kontext Pro adapter (closed-source)
- [ ] **FLUX.1-dev**: Create adapter for open-source FLUX.1-dev model
- [ ] **Additional Open-Source Models**: Integrate other open-source image generation models from HuggingFace/GitHub
- **Labels**: `intermediate`, `image-generation`, `help wanted`, `high-priority`

#### Dataset Adapters
- [ ] **DeepFashion**: Create DeepFashion dataset adapter
- [ ] **FashionGen**: Implement FashionGen dataset loader
- [ ] **Dataset Utils**: Add preprocessing utilities (masks, segmentation, pose detection)
- **Labels**: `intermediate`, `datasets`, `help wanted`

#### Open-Source Virtual Try-On Models
- [ ] **Leffa**: Integrate Leffa image virtual try-on model
- [ ] **DreamO**: Integrate DreamO image virtual try-on model
- [ ] **Voost**: Integrate Voost image virtual try-on model
- [ ] **IDM-VTON**: Integrate IDM-VTON image virtual try-on model
- [ ] **CatVTON**: Integrate CatVTON image virtual try-on model
- [ ] **Video VTON**: Integrate video virtual try-on models
- [ ] **3D VTON**: Integrate 3D virtual try-on models
- **Labels**: `intermediate`, `virtual-try-on`, `open-source`, `help wanted`

### Advanced Contributions

For experienced contributors:

#### Video Generation
- [ ] **VideoGenerator Interface**: Design and implement unified VideoGenerator interface
- [ ] **SORA2 Integration**: Integrate SORA2 video generation API
- [ ] **LUMA Ray Integration**: Add LUMA Ray video generation adapter
- [ ] **Open-Source Video Models**: Integrate video models from HuggingFace/GitHub
- **Labels**: `advanced`, `video-generation`, `help wanted`

#### Agentic AI System
- [ ] **Multi-Agent Framework**: Design multi-agent system architecture
- [ ] **LLM Integration**: Integrate LLMs for text analysis
- [ ] **VLM Integration**: Add VLM support for image analysis
- [ ] **PDP Optimizer**: Build automated PDP evaluation and optimization pipeline
- **Labels**: `advanced`, `agentic-ai`, `help wanted`

#### Core Infrastructure
- [ ] **Model Registry**: Implement model registry system for easy model discovery
- [ ] **HuggingFace Integration**: Create utilities for loading models from HuggingFace Hub
- [ ] **CLI Tool**: Enhance CLI with `ot generate`, `ot tryon`, `ot video`, `ot agent` commands
- [ ] **Async Support**: Add async/await support for API calls
- **Labels**: `advanced`, `infrastructure`, `help wanted`

### Contribution Areas by Priority

#### High Priority (November 2025 - December 2025)
1. **Image Generation Providers** - Nano Banana, GPT-Image-1, FLUX Kontext Pro (closed-source), FLUX.1-dev (open-source)
2. **Core API Infrastructure** - Base classes, interfaces, unified responses
3. **ImageGenerator Unified Interface** - Standardize image generation adapters
4. **Testing** - Unit tests, integration tests, >90% coverage
5. **Documentation** - API docs, examples, tutorials

#### Medium Priority (January - February 2026)
1. **Open-Source VTON Models** - Leffa, DreamO, Voost, IDM-VTON, CatVTON, Video VTON, 3D VTON integrations
2. **Video Generation** - VideoGenerator interface, SORA2, LUMA Ray integrations
3. **Agentic AI System** - Multi-agent framework, LLM/VLM integration
4. **Model Registry** - Model discovery and management system
5. **CLI Improvements** - Enhanced command-line interface

#### Nice to Have (February - April 2026)
1. **Additional Providers** - Fashn AI, TryOnLabs, Qwen-Image
2. **Additional Datasets** - DeepFashion, FashionGen
3. **Advanced Features** - Async support, caching, batch processing
4. **Developer Tools** - VS Code extension, Jupyter integration

### How to Contribute

1. **Find an Issue**: Check our [GitHub Issues](https://github.com/tryonlabs/opentryon/issues) for tasks labeled `good first issue`, `help wanted`, or `intermediate`
2. **Claim a Task**: Comment on the issue to let us know you're working on it
3. **Fork & Branch**: Fork the repo and create a feature branch
4. **Code**: Write clean, tested code following our [Contributing Guidelines](./contributing)
5. **Test**: Ensure all tests pass and add new tests for your changes
6. **Document**: Update documentation and add docstrings
7. **Submit PR**: Open a pull request with a clear description

### Contribution Guidelines

- **Code Style**: Follow PEP 8, use type hints, add docstrings
- **Testing**: Write tests for new features, maintain >85% coverage
- **Documentation**: Update README, add examples, document APIs
- **Commits**: Write clear commit messages following conventional commits
- **PRs**: Keep PRs focused, include tests and documentation

### Issue Labels

We use these labels to help you find tasks:
- `good first issue` - Perfect for new contributors
- `help wanted` - We need help with this
- `intermediate` - Requires some experience
- `advanced` - Complex tasks for experienced contributors
- `documentation` - Documentation improvements
- `testing` - Test-related tasks
- `api` - API adapter work
- `image-generation` - Image generation features
- `video-generation` - Video generation features
- `virtual-try-on` - Virtual try-on model integrations
- `open-source` - Open-source model integrations
- `agentic-ai` - Agentic AI system work
- `datasets` - Dataset adapter work
- `infrastructure` - Core infrastructure improvements

### Get Help

- **Discord**: Join our [Discord community](https://discord.gg/T5mPpZHxkY)
- **GitHub Discussions**: Ask questions in [Discussions](https://github.com/tryonlabs/opentryon/discussions)
- **Issues**: Open an issue for bugs or feature requests

### Current Focus Areas

**This Month (November 2025)**:
- Dataset module testing and refinement
- API adapter pattern standardization
- **Image Generation Model Integrations**:
  - Closed-source: Nano Banana, GPT-Image-1, FLUX Kontext Pro
  - Open-source: FLUX.1-dev and other open-source models
- Documentation improvements

**Next Month (December 2025)**:
- ImageGenerator unified interface
- Model registry system
- Core API infrastructure (base classes, interfaces)
- Unified VirtualTryOn interface
- Configuration management system

**Coming Soon (January 2026)**:
- Video Generation capabilities
- Open-source VTON models (Leffa, DreamO, Voost, IDM-VTON, CatVTON, Video VTON, 3D VTON)
- Agentic AI system foundation

---

**Ready to contribute?** Check out our [Contributing Guide](./contributing) and start with a `good first issue`!
