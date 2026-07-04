"""
Model registry for the ``opentryon`` CLI.

The CLI is organized in three levels of control:

    1. service  -- what kind of task (vton, generate, edit, understand,
                   video-generate, bg-remove)
    2. model    -- which adapter/provider to use for that service
    3. params   -- model-specific parameters (image inputs, prompts,
                   sampling knobs, etc.)

This module only declares *data* (which module/class/method implements each
model, and which CLI flags map to which call kwargs). No adapter modules are
imported here, so importing this registry is always fast and dependency-free.
Adapters are imported lazily by ``tryon.cli.runner`` only when a given model
is actually invoked.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple


@dataclass
class Arg:
    """One CLI flag, mapped to a kwarg on either the adapter constructor or
    the adapter method being invoked.

    ``dest`` is the argparse namespace attribute and must be unique within a
    model's parser (it shares a namespace with the service-level ``--model``
    selector, ``--output-dir``, etc.). ``call_name`` is the actual kwarg name
    passed to the adapter and defaults to ``dest`` when not given -- set it
    explicitly when the two need to differ (e.g. a per-model "model version"
    flag whose CLI dest can't be ``model`` because that's already the
    service-level model *selector*, but the adapter method itself expects a
    ``model=`` kwarg).
    """

    flags: Tuple[str, ...]
    dest: str
    help: str = ""
    type: Callable[[str], Any] = str
    required: bool = False
    default: Any = None
    choices: Optional[List[Any]] = None
    nargs: Optional[str] = None
    action: Optional[str] = None
    target: str = "call"  # "call" (method kwarg) or "init" (constructor kwarg)
    alt_only: bool = False  # only passed when a model's alt_method_on_image is used
    call_name: Optional[str] = None  # adapter kwarg name, if different from dest


@dataclass
class ModelSpec:
    id: str
    label: str
    import_path: str  # dotted submodule path, e.g. "tryon.api.vton.flux_vto"
    class_name: str
    method: str
    output_kind: str  # "images" | "image_bytes" | "video_bytes" | "text"
    args: List[Arg] = field(default_factory=list)
    alt_method_on_image: Optional[str] = None
    alt_image_dest: str = "image"
    extra: str = "core"  # "core" | "local" (needs `pip install opentryon[local]`)
    env_hint: Optional[str] = None
    notes: Optional[str] = None


def _img(flags, dest, help_, required=False, default=None):
    return Arg(flags=flags, dest=dest, help=help_, required=required, default=default)


# --------------------------------------------------------------------------
# vton
# --------------------------------------------------------------------------

_VTON = {
    "flux-vto": ModelSpec(
        id="flux-vto",
        label="Black Forest Labs FLUX VTO",
        import_path="tryon.api.vton.flux_vto",
        class_name="FluxVTONAdapter",
        method="generate_and_decode",
        output_kind="images",
        env_hint="BFL_API_KEY",
        args=[
            _img(("--person-image", "--model-image"), "person", "Person/model image (path or URL)", required=True),
            _img(("--garment-image", "--cloth-image"), "garment", "Garment reference image (path or URL)", required=True),
            Arg(("--prompt",), "prompt", "Full styling prompt (overrides --garment-description)"),
            Arg(("--garment-description",), "garment_description", "Short garment description used to build the default prompt"),
            Arg(("--seed",), "seed", type=int, help="Seed for reproducibility"),
            Arg(("--safety-tolerance",), "safety_tolerance", type=int, default=2, choices=list(range(6)), help="Moderation strictness 0-5"),
            Arg(("--output-format",), "output_format", default="webp", choices=["jpeg", "png", "webp"], help="Output image format"),
        ],
    ),
    "nova-canvas": ModelSpec(
        id="nova-canvas",
        label="Amazon Nova Canvas",
        import_path="tryon.api.nova_canvas",
        class_name="AmazonNovaCanvasVTONAdapter",
        method="generate_and_decode",
        output_kind="images",
        env_hint="AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY",
        args=[
            _img(("--person-image",), "source_image", "Person/model image (path or URL)", required=True),
            _img(("--garment-image",), "reference_image", "Garment reference image (path or URL)", required=True),
            Arg(("--mask-type",), "mask_type", default="GARMENT", choices=["GARMENT", "IMAGE"]),
            Arg(("--garment-class",), "garment_class", default="UPPER_BODY", choices=["UPPER_BODY", "LOWER_BODY", "FULL_BODY", "FOOTWEAR"]),
            Arg(("--mask-image",), "mask_image", help="Optional custom mask image (path or URL)"),
            Arg(("--region",), "region", target="init", help="AWS region, e.g. us-east-1"),
        ],
    ),
    "kling-ai": ModelSpec(
        id="kling-ai",
        label="Kling AI (Kolors Virtual Try-On)",
        import_path="tryon.api.kling_ai",
        class_name="KlingAIVTONAdapter",
        method="generate_and_decode",
        output_kind="images",
        env_hint="KLING_AI_API_KEY / KLING_AI_SECRET_KEY",
        args=[
            _img(("--person-image",), "source_image", "Person/model image (path or URL)", required=True),
            _img(("--garment-image",), "reference_image", "Garment reference image (path or URL)", required=True),
            Arg(("--model-version",), "model_version", call_name="model", choices=["kolors-virtual-try-on-v1", "kolors-virtual-try-on-v1-5"], help="Kling AI model version"),
        ],
    ),
    "segmind": ModelSpec(
        id="segmind",
        label="Segmind Try-On Diffusion",
        import_path="tryon.api.segmind",
        class_name="SegmindVTONAdapter",
        method="generate_and_decode",
        output_kind="images",
        env_hint="SEGMIND_API_KEY",
        args=[
            _img(("--person-image",), "model_image", "Model/person image (path or URL)", required=True),
            _img(("--garment-image",), "cloth_image", "Cloth/garment image (path or URL)", required=True),
            Arg(("--category",), "category", default="Upper body", choices=["Upper body", "Lower body", "Dress"]),
            Arg(("--steps",), "num_inference_steps", type=int, help="Denoising steps (20-100)"),
            Arg(("--guidance-scale",), "guidance_scale", type=float, help="Classifier-free guidance scale (1-25)"),
            Arg(("--seed",), "seed", type=int, help="Seed for reproducibility (-1 for random)"),
        ],
    ),
}

# --------------------------------------------------------------------------
# generate (text-to-image)
# --------------------------------------------------------------------------


def _nano_banana_generate_args(with_resolution: bool, with_grounding: bool) -> List[Arg]:
    args = [
        Arg(("--prompt", "-p"), "prompt", required=True, help="Text prompt"),
        Arg(("--aspect-ratio",), "aspect_ratio", help="e.g. 1:1, 16:9, 9:16"),
    ]
    if with_resolution:
        args.append(Arg(("--resolution",), "resolution", default="2K", choices=["1K", "2K", "4K"]))
    if with_grounding:
        args.append(Arg(("--use-search-grounding",), "use_search_grounding", action="store_true", help="Ground with Google Search"))
    return args


def _flux2_generate_args(is_flex: bool) -> List[Arg]:
    args = [
        Arg(("--prompt", "-p"), "prompt", required=True, help="Text prompt"),
        Arg(("--width",), "width", type=int, help="Output width (min 64)"),
        Arg(("--height",), "height", type=int, help="Output height (min 64)"),
        Arg(("--seed",), "seed", type=int, help="Seed for reproducibility"),
        Arg(("--safety-tolerance",), "safety_tolerance", type=int, default=2, choices=list(range(6))),
        Arg(("--output-format",), "output_format", default="png", choices=["jpeg", "png"]),
    ]
    if is_flex:
        args.insert(3, Arg(("--guidance",), "guidance", type=float, default=3.5, help="Guidance scale 1.5-10"))
        args.insert(4, Arg(("--steps",), "steps", type=int, default=28, help="Inference steps"))
    return args


_GENERATE = {
    "nano-banana": ModelSpec(
        id="nano-banana", label="Nano Banana (Gemini 2.5 Flash Image)",
        import_path="tryon.api.nano_banana", class_name="NanoBananaAdapter",
        method="generate_text_to_image", output_kind="images", env_hint="GEMINI_API_KEY",
        args=_nano_banana_generate_args(with_resolution=False, with_grounding=False),
    ),
    "nano-banana-pro": ModelSpec(
        id="nano-banana-pro", label="Nano Banana Pro (Gemini 3 Pro Image Preview)",
        import_path="tryon.api.nano_banana", class_name="NanoBananaProAdapter",
        method="generate_text_to_image", output_kind="images", env_hint="GEMINI_API_KEY",
        args=_nano_banana_generate_args(with_resolution=True, with_grounding=True),
    ),
    "nano-banana-2": ModelSpec(
        id="nano-banana-2", label="Nano Banana 2 (Gemini 3.1 Flash Image)",
        import_path="tryon.api.nano_banana", class_name="NanoBanana2Adapter",
        method="generate_text_to_image", output_kind="images", env_hint="GEMINI_API_KEY",
        args=_nano_banana_generate_args(with_resolution=True, with_grounding=True),
    ),
    "flux2-pro": ModelSpec(
        id="flux2-pro", label="FLUX.2 [pro]",
        import_path="tryon.api.flux2", class_name="Flux2ProAdapter",
        method="generate_text_to_image", output_kind="images", env_hint="BFL_API_KEY",
        args=_flux2_generate_args(is_flex=False),
    ),
    "flux2-flex": ModelSpec(
        id="flux2-flex", label="FLUX.2 [flex]",
        import_path="tryon.api.flux2", class_name="Flux2FlexAdapter",
        method="generate_text_to_image", output_kind="images", env_hint="BFL_API_KEY",
        args=_flux2_generate_args(is_flex=True),
    ),
    "flux2-turbo": ModelSpec(
        id="flux2-turbo", label="FLUX.2-dev Turbo (local, 8-step)",
        import_path="tryon.models.flux2_turbo", class_name="Flux2TurboAdapter",
        method="generate_text_to_image", output_kind="images", extra="local",
        notes="Local GPU inference. Requires `pip install opentryon[local]` and a CUDA GPU (12GB+ VRAM recommended).",
        args=[
            Arg(("--prompt", "-p"), "prompt", required=True, help="Text prompt"),
            Arg(("--width",), "width", type=int, default=1024),
            Arg(("--height",), "height", type=int, default=1024),
            Arg(("--guidance-scale",), "guidance_scale", type=float, default=2.5),
            Arg(("--steps",), "num_inference_steps", type=int, default=8),
            Arg(("--num-images",), "num_images", type=int, default=1),
            Arg(("--seed",), "seed", type=int),
        ],
    ),
    "gpt-image": ModelSpec(
        id="gpt-image", label="OpenAI GPT Image",
        import_path="tryon.api.openAI.image_adapter", class_name="GPTImageAdapter",
        method="generate_text_to_image", output_kind="image_bytes", env_hint="OPENAI_API_KEY",
        args=[
            Arg(("--prompt", "-p"), "prompt", required=True, help="Text prompt"),
            Arg(("--size",), "size", default="auto"),
            Arg(("--quality",), "quality", default="auto"),
            Arg(("--background",), "background", default="auto"),
            Arg(("--n",), "n", type=int, default=1, help="Number of images"),
            Arg(("--model-version",), "model_version", target="init", default="gpt-image-1.5"),
        ],
    ),
    "luma-image": ModelSpec(
        id="luma-image", label="Luma Photon",
        import_path="tryon.api.lumaAI", class_name="LumaAIAdapter",
        method="generate_text_to_image", output_kind="images", env_hint="LUMA_AI_API_KEY",
        args=[
            Arg(("--prompt", "-p"), "prompt", required=True, help="Text prompt"),
            Arg(("--model-version",), "model_version", call_name="model", default="photon-1", choices=["photon-1", "photon-flash-1"]),
            Arg(("--aspect-ratio",), "aspect_ratio", help="e.g. 1:1, 16:9, 9:16"),
        ],
    ),
}

# --------------------------------------------------------------------------
# edit (image editing)
# --------------------------------------------------------------------------

_EDIT = {
    "nano-banana": ModelSpec(
        id="nano-banana", label="Nano Banana (Gemini 2.5 Flash Image)",
        import_path="tryon.api.nano_banana", class_name="NanoBananaAdapter",
        method="generate_image_edit", output_kind="images", env_hint="GEMINI_API_KEY",
        args=[
            _img(("--image", "-i"), "image", "Input image (path or URL)", required=True),
            Arg(("--prompt", "-p"), "prompt", required=True, help="Editing instruction"),
            Arg(("--aspect-ratio",), "aspect_ratio"),
        ],
    ),
    "nano-banana-pro": ModelSpec(
        id="nano-banana-pro", label="Nano Banana Pro",
        import_path="tryon.api.nano_banana", class_name="NanoBananaProAdapter",
        method="generate_image_edit", output_kind="images", env_hint="GEMINI_API_KEY",
        args=[
            _img(("--image", "-i"), "image", "Input image (path or URL)", required=True),
            Arg(("--prompt", "-p"), "prompt", required=True, help="Editing instruction"),
            Arg(("--aspect-ratio",), "aspect_ratio"),
            Arg(("--resolution",), "resolution", default="2K", choices=["1K", "2K", "4K"]),
        ],
    ),
    "nano-banana-2": ModelSpec(
        id="nano-banana-2", label="Nano Banana 2",
        import_path="tryon.api.nano_banana", class_name="NanoBanana2Adapter",
        method="generate_image_edit", output_kind="images", env_hint="GEMINI_API_KEY",
        args=[
            _img(("--image", "-i"), "image", "Input image (path or URL)", required=True),
            Arg(("--prompt", "-p"), "prompt", required=True, help="Editing instruction"),
            Arg(("--aspect-ratio",), "aspect_ratio"),
            Arg(("--resolution",), "resolution", default="2K", choices=["1K", "2K", "4K"]),
        ],
    ),
    "flux2-pro": ModelSpec(
        id="flux2-pro", label="FLUX.2 [pro]",
        import_path="tryon.api.flux2", class_name="Flux2ProAdapter",
        method="generate_image_edit", output_kind="images", env_hint="BFL_API_KEY",
        args=[
            _img(("--image", "-i"), "input_image", "Input image (path or URL)", required=True),
            Arg(("--prompt", "-p"), "prompt", required=True, help="Editing instruction"),
            Arg(("--width",), "width", type=int),
            Arg(("--height",), "height", type=int),
            Arg(("--seed",), "seed", type=int),
            Arg(("--safety-tolerance",), "safety_tolerance", type=int, default=2, choices=list(range(6))),
            Arg(("--output-format",), "output_format", default="png", choices=["jpeg", "png"]),
        ],
    ),
    "flux2-flex": ModelSpec(
        id="flux2-flex", label="FLUX.2 [flex]",
        import_path="tryon.api.flux2", class_name="Flux2FlexAdapter",
        method="generate_image_edit", output_kind="images", env_hint="BFL_API_KEY",
        args=[
            _img(("--image", "-i"), "input_image", "Input image (path or URL)", required=True),
            Arg(("--prompt", "-p"), "prompt", required=True, help="Editing instruction"),
            Arg(("--width",), "width", type=int),
            Arg(("--height",), "height", type=int),
            Arg(("--guidance",), "guidance", type=float, default=3.5),
            Arg(("--steps",), "steps", type=int, default=28),
            Arg(("--seed",), "seed", type=int),
            Arg(("--safety-tolerance",), "safety_tolerance", type=int, default=2, choices=list(range(6))),
            Arg(("--output-format",), "output_format", default="png", choices=["jpeg", "png"]),
        ],
    ),
    "flux2-turbo": ModelSpec(
        id="flux2-turbo", label="FLUX.2-dev Turbo (local, image-to-image)",
        import_path="tryon.models.flux2_turbo", class_name="Flux2TurboAdapter",
        method="generate_image_to_image", output_kind="images", extra="local",
        notes="Local GPU inference. Requires `pip install opentryon[local]` and a CUDA GPU.",
        args=[
            _img(("--image", "-i"), "image", "Input image (path)", required=True),
            Arg(("--prompt", "-p"), "prompt", required=True, help="Editing instruction"),
            Arg(("--guidance-scale",), "guidance_scale", type=float, default=2.5),
            Arg(("--steps",), "num_inference_steps", type=int, default=8),
            Arg(("--seed",), "seed", type=int),
        ],
    ),
    "gpt-image": ModelSpec(
        id="gpt-image", label="OpenAI GPT Image",
        import_path="tryon.api.openAI.image_adapter", class_name="GPTImageAdapter",
        method="generate_image_edit", output_kind="image_bytes", env_hint="OPENAI_API_KEY",
        args=[
            Arg(("--images",), "images", nargs="+", required=True, help="One or more input images (paths or URLs)"),
            Arg(("--prompt", "-p"), "prompt", help="Editing instruction"),
            Arg(("--mask",), "mask", help="Optional mask image"),
            Arg(("--size",), "size", default="auto"),
            Arg(("--quality",), "quality", default="auto"),
            Arg(("--background",), "background", default="auto"),
            Arg(("--input-fidelity",), "input_fidelity", default="low", choices=["low", "high"]),
            Arg(("--n",), "n", type=int, default=1),
            Arg(("--model-version",), "model_version", target="init", default="gpt-image-1.5"),
        ],
    ),
}

# --------------------------------------------------------------------------
# understand (image understanding / captioning)
# --------------------------------------------------------------------------

_UNDERSTAND = {
    "llava-next": ModelSpec(
        id="llava-next", label="LLaVA-NeXT (local VLM captioning)",
        import_path="tryon.cli.local_wrappers", class_name="LlavaNextUnderstandAdapter",
        method="understand", output_kind="text", extra="local",
        notes="Local GPU inference. Requires `pip install opentryon[local]` and a CUDA GPU.",
        args=[
            _img(("--image", "-i"), "image", "Image to describe (path or URL)", required=True),
            Arg(("--prompt", "-p"), "prompt", help="Question/instruction for the model"),
            Arg(("--json-only",), "json_only", action="store_true", help="Return structured JSON only, skip natural-language caption"),
        ],
    ),
    "kimi-k2.6": ModelSpec(
        id="kimi-k2.6", label="Kimi K2.6 (Moonshot AI multimodal understanding)",
        import_path="tryon.api.kimi", class_name="KimiUnderstandAdapter",
        method="understand", output_kind="text", env_hint="MOONSHOT_API_KEY",
        notes="General-purpose: understands images AND video, any domain (not fashion-specific). 256K context.",
        args=[
            Arg(("--image", "-i"), "image", help="Image to understand (path or URL)"),
            Arg(("--video",), "video", help="Video to understand (path or URL)"),
            Arg(("--prompt", "-p"), "prompt", help="Question/instruction for the model"),
            Arg(("--no-thinking",), "thinking", action="store_false", default=True, help="Disable Kimi's thinking mode"),
            Arg(("--max-tokens",), "max_tokens", type=int, help="Max output tokens (server default: 32768)"),
        ],
    ),
    "kimi-k2.7-code": ModelSpec(
        id="kimi-k2.7-code", label="Kimi K2.7 Code (Moonshot AI coding + multimodal understanding)",
        import_path="tryon.api.kimi", class_name="KimiUnderstandAdapter",
        method="understand", output_kind="text", env_hint="MOONSHOT_API_KEY",
        notes="Coding-focused variant of K2.6 with the same image/video understanding. Thinking mode is always on.",
        args=[
            Arg(("--kimi-model",), "kimi_model", target="init", call_name="model", default="kimi-k2.7-code",
                choices=["kimi-k2.7-code", "kimi-k2.7-code-highspeed"], help="Kimi K2.7 Code variant"),
            Arg(("--image", "-i"), "image", help="Image to understand (path or URL)"),
            Arg(("--video",), "video", help="Video to understand (path or URL)"),
            Arg(("--prompt", "-p"), "prompt", help="Question/instruction for the model"),
            Arg(("--max-tokens",), "max_tokens", type=int, help="Max output tokens (server default: 32768)"),
        ],
    ),
    "kimi-vl": ModelSpec(
        id="kimi-vl", label="Kimi-VL (open-weight, local)",
        import_path="tryon.models.kimi_vl", class_name="KimiVLAdapter",
        method="understand", output_kind="text", extra="local",
        notes="Open-weight counterpart to kimi-k2.6/k2.7-code. Local GPU inference "
        "(24GB+ VRAM recommended). Requires `pip install opentryon[local]`.",
        args=[
            Arg(("--image", "-i"), "image", help="Image to understand (path or URL)"),
            Arg(("--video",), "video", help="Video to understand (path or URL, requires `pip install decord`)"),
            Arg(("--prompt", "-p"), "prompt", help="Question/instruction for the model"),
            Arg(("--num-frames",), "num_frames", type=int, default=8, help="Frames to sample from --video"),
            Arg(("--max-new-tokens",), "max_new_tokens", type=int, default=4096, help="Max output tokens"),
            Arg(("--temperature",), "temperature", type=float, default=0.8, help="Sampling temperature"),
        ],
    ),
}

# --------------------------------------------------------------------------
# video-generate
# --------------------------------------------------------------------------

_VIDEO_GENERATE = {
    "veo": ModelSpec(
        id="veo", label="Google Veo",
        import_path="tryon.api.veo", class_name="VeoAdapter",
        method="generate_text_to_video", output_kind="video_bytes",
        alt_method_on_image="generate_image_to_video", alt_image_dest="image",
        env_hint="GEMINI_API_KEY",
        args=[
            Arg(("--prompt", "-p"), "prompt", required=True, help="Text prompt"),
            Arg(("--image",), "image", help="Optional still image to animate (switches to image-to-video)", alt_only=True),
            Arg(("--duration",), "duration_seconds", default="4", help='Clip length in seconds, e.g. "4", "6", "8"'),
            Arg(("--aspect-ratio",), "aspect_ratio", default="16:9"),
            Arg(("--resolution",), "resolution", default="720p", choices=["720p", "1080p"]),
            Arg(("--negative-prompt",), "negative_prompt"),
            Arg(("--model-version",), "model_version", call_name="model", default="veo-3.1-generate-preview"),
        ],
    ),
    "sora": ModelSpec(
        id="sora", label="OpenAI Sora",
        import_path="tryon.api.openAI.video_adapter", class_name="SoraVideoAdapter",
        method="generate_text_to_video", output_kind="video_bytes",
        alt_method_on_image="generate_image_to_video", alt_image_dest="image",
        env_hint="OPENAI_API_KEY",
        args=[
            Arg(("--prompt", "-p"), "prompt", required=True, help="Text prompt"),
            Arg(("--image",), "image", help="Optional still image to animate (switches to image-to-video)", alt_only=True),
            Arg(("--duration",), "duration", type=int, default=4, choices=[4, 8, 12]),
            Arg(("--resolution",), "resolution", default="1280x720"),
            Arg(("--no-wait",), "wait", action="store_false", default=True, help="Return immediately with a video ID instead of polling until ready"),
        ],
    ),
    "luma-video": ModelSpec(
        id="luma-video", label="Luma Dream Machine",
        import_path="tryon.api.lumaAI.luma_video_adapter", class_name="LumaAIVideoAdapter",
        method="generate_text_to_video", output_kind="video_bytes",
        alt_method_on_image="generate_image_to_video", alt_image_dest="start_image",
        env_hint="LUMA_AI_API_KEY",
        args=[
            Arg(("--prompt", "-p"), "prompt", help="Text prompt"),
            Arg(("--image",), "start_image", help="Optional start image (switches to image-to-video)", alt_only=True),
            Arg(("--end-image",), "end_image", help="Optional end image (for interpolation, image-to-video only)", alt_only=True),
            Arg(("--loop",), "loop", action="store_true"),
            Arg(("--resolution",), "resolution", default="540p", choices=["540p", "720p", "1080p", "4k"]),
            Arg(("--duration",), "duration", default="5s"),
            Arg(("--model-version",), "model_version", call_name="model", default="ray-2", choices=["ray-1-6", "ray-2", "ray-flash-2"]),
            Arg(("--aspect-ratio",), "aspect_ratio"),
        ],
    ),
}

# --------------------------------------------------------------------------
# bg-remove
# --------------------------------------------------------------------------

_BG_REMOVE = {
    "ben2": ModelSpec(
        id="ben2", label="BEN2 background remover (local)",
        import_path="tryon.api.ben2.adapter", class_name="BEN2BackgroundRemoverAdapter",
        method="remove_background", output_kind="images", extra="local",
        notes="Local GPU/CPU inference. Requires `pip install opentryon[local]`.",
        args=[
            _img(("--image", "-i"), "image", "Input image (path or URL)", required=True),
            Arg(("--refine",), "refine", action="store_true", help="Refined foreground enhancement"),
        ],
    ),
}

SERVICES: Dict[str, Dict[str, ModelSpec]] = {
    "vton": _VTON,
    "generate": _GENERATE,
    "edit": _EDIT,
    "understand": _UNDERSTAND,
    "video-generate": _VIDEO_GENERATE,
    "bg-remove": _BG_REMOVE,
}

SERVICE_HELP = {
    "vton": "Virtual try-on: compose a garment onto a person image",
    "generate": "Text-to-image generation",
    "edit": "Image editing (image + instruction -> image)",
    "understand": "Image understanding / captioning",
    "video-generate": "Text/image-to-video generation",
    "bg-remove": "Background removal",
}


def get_service(service: str) -> Dict[str, ModelSpec]:
    if service not in SERVICES:
        raise KeyError(f"Unknown service '{service}'. Available: {', '.join(SERVICES)}")
    return SERVICES[service]


def get_model(service: str, model: str) -> ModelSpec:
    models = get_service(service)
    if model not in models:
        raise KeyError(
            f"Unknown model '{model}' for service '{service}'. "
            f"Available: {', '.join(models)}"
        )
    return models[model]


RESERVED_FLAGS = {"--model", "-o", "--output-dir", "--dry-run", "-h", "--help"}
RESERVED_DESTS = {"model", "output_dir", "dry_run"}


def validate_registry() -> None:
    """Sanity-check every model's args against reserved/duplicate flags and
    dests.

    Raises AssertionError with a descriptive message on the first problem
    found. Intended to be exercised by tests so a bad registry entry (e.g. a
    per-model "model version" arg whose ``dest`` collides with the
    service-level ``--model`` selector's dest -- argparse won't error on
    this, it will just silently let one clobber the other) fails fast
    instead of only surfacing when a user hits it.
    """
    for service, models in SERVICES.items():
        for model_id, spec in models.items():
            seen_flags: set = set()
            seen_dests: set = set()
            for arg in spec.args:
                assert arg.dest not in RESERVED_DESTS, (
                    f"{service}/{model_id}: dest {arg.dest!r} collides with a "
                    "reserved CLI dest (use `call_name=` to map to the real "
                    "adapter kwarg while keeping `dest` unique)"
                )
                assert arg.dest not in seen_dests, (
                    f"{service}/{model_id}: dest {arg.dest!r} is declared more "
                    "than once"
                )
                seen_dests.add(arg.dest)
                for flag in arg.flags:
                    assert flag not in RESERVED_FLAGS, (
                        f"{service}/{model_id}: flag {flag!r} collides with a "
                        "reserved CLI flag"
                    )
                    assert flag not in seen_flags, (
                        f"{service}/{model_id}: flag {flag!r} is declared more "
                        "than once"
                    )
                    seen_flags.add(flag)
