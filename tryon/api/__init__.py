"""
tryon.api — cloud API adapters (remote inference).

Attributes are imported lazily (PEP 562) so that, e.g., ``from tryon.api import
FluxVTONAdapter`` does not transitively import every adapter in this package
(some of which pull in heavy local-inference dependencies like torch/timm,
e.g. BEN2BackgroundRemoverAdapter). Each adapter's own submodule is only
imported the first time it's actually accessed.
"""

import importlib

_LAZY_ATTRS = {
    "AmazonNovaCanvasVTONAdapter": ".nova_canvas",
    "KlingAIVTONAdapter": ".kling_ai",
    "SegmindVTONAdapter": ".segmind",
    "FluxVTONAdapter": ".vton",
    "NanoBananaAdapter": ".nano_banana",
    "NanoBananaProAdapter": ".nano_banana",
    "NanoBanana2Adapter": ".nano_banana",
    "NanoBanana2LiteAdapter": ".nano_banana",
    "PImageTryOnAdapter": ".vton",
    "FashnVTONAdapter": ".vton",
    "LumaAIAdapter": ".lumaAI",
    "Flux2ProAdapter": ".flux2",
    "Flux2FlexAdapter": ".flux2",
    "LumaAIVideoAdapter": ".lumaAI.luma_video_adapter",
    "GPTImageAdapter": ".openAI.image_adapter",
    "SoraVideoAdapter": ".openAI.video_adapter",
    "VeoAdapter": ".veo",
    "GeminiOmniAdapter": ".omni",
    "BEN2BackgroundRemoverAdapter": ".ben2",
    "KimiUnderstandAdapter": ".kimi",
}

__all__ = sorted(_LAZY_ATTRS)


def __getattr__(name):
    module_path = _LAZY_ATTRS.get(name)
    if module_path is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = importlib.import_module(module_path, __name__)
    return getattr(module, name)


def __dir__():
    return sorted(list(globals()) + __all__)
