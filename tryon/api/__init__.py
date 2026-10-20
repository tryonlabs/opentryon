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
    "KlingVideoAdapter": ".kling_video",
    "SegmindVTONAdapter": ".segmind",
    "FluxVTONAdapter": ".vton",
    "NanoBananaAdapter": ".nano_banana",
    "NanoBananaProAdapter": ".nano_banana",
    "NanoBanana2Adapter": ".nano_banana",
    "NanoBanana21Adapter": ".nano_banana",
    "NanoBanana2LiteAdapter": ".nano_banana",
    "PImageTryOnAdapter": ".vton",
    "FashnVTONAdapter": ".vton",
    "FashnAdapter": ".fashn",
    "GoogleVTONAdapter": ".vton",
    "OutfitAnyonePlusAdapter": ".vton",
    "PhotoroomVTONAdapter": ".vton",
    "PImageAdapter": ".pruna",
    "PImageEditAdapter": ".pruna",
    "PImageIdeogramAdapter": ".pruna",
    "PImageUpscaleAdapter": ".pruna",
    "PVideoAdapter": ".pruna",
    "PVideo2ProAdapter": ".pruna",
    "PVideoReplaceAdapter": ".pruna",
    "PVideoAvatarAdapter": ".pruna",
    "PVideoAnimateAdapter": ".pruna",
    "LumaAIAdapter": ".lumaAI",
    "Flux2ProAdapter": ".flux2",
    "Flux2FlexAdapter": ".flux2",
    "Flux3ImageAdapter": ".flux3",
    "CladBodyApiAdapter": ".clad",
    "D3ApiAdapter": ".vllm_sr",
    "Dream1Adapter": ".dream_labs",
    "Flux3ImageKleinAdapter": ".flux3",
    "Flux3VideoAdapter": ".flux3_video",
    "Flux3MaxVideoAdapter": ".flux3_video",
    "TrellisMeshAdapter": ".nvidia.trellis_adapter",
    "LipSyncAdapter": ".nvidia.lipsync_adapter",
    "LumaAIVideoAdapter": ".lumaAI.luma_video_adapter",
    "LumaRay32Adapter": ".lumaAI.ray32_adapter",
    "GPTImageAdapter": ".openAI.image_adapter",
    "SoraVideoAdapter": ".openAI.video_adapter",
    "VeoAdapter": ".veo",
    "GeminiOmniAdapter": ".omni",
    "BEN2BackgroundRemoverAdapter": ".ben2",
    "Hy4Adapter": ".hy",
    "KimiUnderstandAdapter": ".kimi",
    "NemotronOmniUnderstandAdapter": ".nvidia",
    "Nemotron35SuperVLUnderstandAdapter": ".nvidia",
    "Cosmos3ReasonerAdapter": ".nvidia",
    "Cosmos3VideoAdapter": ".nvidia",
    "QwenUnderstandAdapter": ".qwen",
    "QwenImageAdapter": ".qwen",
    "GLMUnderstandAdapter": ".zai",
    "DeepSeekUnderstandAdapter": ".deepseek",
    "InceptionUnderstandAdapter": ".inception",
    "MercuryDecideAdapter": ".inception",
    "ClaudeUnderstandAdapter": ".claude",
    "ElevenLabsAdapter": ".elevenlabs",
    "GeminiUnderstandAdapter": ".gemini",
    "GeminiTTSAdapter": ".gemini",
    "GeminiEmbeddingAdapter": ".gemini",
    "SeedanceAdapter": ".byteplus",
    "SeedreamAdapter": ".byteplus",
    "IdeogramAdapter": ".ideogram",
    "GrokImagineImageAdapter": ".xai",
    "GrokImagineVideoAdapter": ".xai",
    "LTXVideoAdapter": ".ltx",
    "HailuoVideoAdapter": ".minimax",
    "MiniMaxH3Adapter": ".minimax",
    "FalH3MaxAdapter": ".fal",
    "MuseImageAdapter": ".muse",
    "WanVideoAdapter": ".wan",
    "RunwayVideoAdapter": ".runway",
    "Thx01Adapter": ".hal_x",
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
