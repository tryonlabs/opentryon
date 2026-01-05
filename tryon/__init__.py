"""
OpenTryOn - Open-source AI toolkit for fashion tech and virtual try-on

This package provides tools for:
- Virtual Try-On (via cloud APIs and local models)
- Image Generation (Nano Banana, FLUX.2, GPT-Image, Luma AI)
- Video Generation (Sora, Veo, Luma AI)
- Background Removal (BEN2)
- Garment Preprocessing (segmentation, extraction)
- AI Agents (VTOnAgent, ModelSwapAgent, FashionAgent)

Modules:
    tryon.api       - Cloud API adapters (remote inference)
    tryon.models    - Local models (on-device inference, GPU required)
    tryon.agents    - AI agents for intelligent task routing
    tryon.datasets  - Dataset loaders (Fashion-MNIST, VITON-HD, etc.)
    tryon.preprocessing - Garment/human preprocessing utilities

Example:
    # Cloud API (remote)
    >>> from tryon.api import KlingAIVTONAdapter
    >>> adapter = KlingAIVTONAdapter()
    >>> images = adapter.generate_and_decode(source_image="person.jpg", reference_image="garment.jpg")
    
    # Local model (GPU required)
    >>> from tryon.models import Flux2TurboAdapter
    >>> adapter = Flux2TurboAdapter()
    >>> images = adapter.generate_text_to_image("A fashion model wearing a dress")

Documentation: https://tryonlabs.github.io/opentryon/
GitHub: https://github.com/tryonlabs/opentryon
"""

__version__ = "0.0.2"

