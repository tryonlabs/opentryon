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


_QWEN_IMAGE_VERSIONS = [
    "qwen-image-3.0-pro",
    "qwen-image-3.0",
    "qwen-image-2.0-pro",
    "qwen-image-2.0",
]

# Keep in sync with tryon.api.nano_banana adapter ratio tables (registry stays
# import-free, so this is a declared copy for CLI/MCP JSON Schema enums).
_GEMINI_ASPECT_RATIOS = [
    "1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9",
]
_LUMA_ASPECT_RATIOS = ["1:1", "3:4", "4:3", "9:16", "16:9", "9:21", "21:9"]
_IDEOGRAM_ASPECT_RATIOS = [
    "1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3", "10:16", "16:10", "1:3", "3:1",
]


def _gemini_aspect_ratio() -> Arg:
    return Arg(
        ("--aspect-ratio",), "aspect_ratio",
        choices=_GEMINI_ASPECT_RATIOS,
        help="Gemini-supported aspect ratio",
    )


def _qwen_image_common_args() -> List[Arg]:
    return [
        Arg(("--model-version",), "model_version", target="init", call_name="model",
            default="qwen-image-3.0-pro", choices=_QWEN_IMAGE_VERSIONS,
            help="Qwen-Image DashScope model id"),
        Arg(("--size",), "size", help="Output size as width*height, e.g. 1024*1024"),
        Arg(("--n",), "n", type=int, default=1, help="Number of images 1-6"),
        Arg(("--negative-prompt",), "negative_prompt", help="What to avoid in the output"),
        Arg(("--seed",), "seed", type=int, help="Seed for reproducibility"),
        Arg(("--watermark",), "watermark", action="store_true", help="Add a Qwen-Image watermark"),
        Arg(("--no-thinking",), "enable_thinking", action="store_false", default=True,
            help="Disable thinking mode (faster, lower quality)"),
        Arg(("--no-prompt-extend",), "prompt_extend", action="store_false", default=True,
            help="Use the prompt as-is without rewriting"),
        Arg(("--prompt-extend-mode",), "prompt_extend_mode", default="direct",
            choices=["direct", "agent"], help="Prompt rewrite mode (agent is T2I-only)"),
    ]


def _qwen_image_local_sample_args(*, t2i: bool) -> List[Arg]:
    args: List[Arg] = []
    if t2i:
        args.extend([
            Arg(("--aspect-ratio",), "aspect_ratio", default="1:1",
                choices=["1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3"],
                help="Packed Qwen-Image resolution (overridden by --width/--height)"),
            Arg(("--width",), "width", type=int, help="Output width (overrides --aspect-ratio)"),
            Arg(("--height",), "height", type=int, help="Output height (overrides --aspect-ratio)"),
            Arg(("--model-id",), "model_id", target="init",
                help="T2I HF repo id or local path (default Qwen/Qwen-Image-2512)"),
        ])
    else:
        args.extend([
            Arg(("--guidance-scale",), "guidance_scale", type=float, default=1.0,
                help="Edit-Plus guidance_scale (vendor default 1.0)"),
            Arg(("--edit-model-id",), "edit_model_id", target="init",
                help="Edit/VTON HF repo id or local path (default Qwen/Qwen-Image-Edit-2511)"),
        ])
    args.extend([
        Arg(("--negative-prompt",), "negative_prompt", help="What to avoid in the output"),
        Arg(("--seed",), "seed", type=int, help="Seed for reproducibility"),
        Arg(("--steps",), "num_inference_steps", type=int, default=50 if t2i else 40,
            help="Denoising steps (T2I default 50, edit/VTON default 40)"),
        Arg(("--true-cfg-scale",), "true_cfg_scale", type=float, default=4.0,
            help="True CFG scale (Qwen-Image default 4.0)"),
        Arg(("--num-images",), "num_images", type=int, default=1, help="Number of images"),
        Arg(("--dtype",), "dtype", target="init", default="bfloat16",
            choices=["bfloat16", "float16", "float32"], help="Weight dtype"),
        Arg(("--no-cpu-offload",), "cpu_offload", target="init",
            action="store_false", default=True,
            help="Disable CPU offload (needs ~40GB+ VRAM)"),
    ])
    return args


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
    "p-image-tryon": ModelSpec(
        id="p-image-tryon",
        label="Pruna P-Image-Try-On",
        import_path="tryon.api.vton.p_image_tryon",
        class_name="PImageTryOnAdapter",
        method="generate_and_decode",
        output_kind="images",
        env_hint="PRUNA_API_KEY",
        notes="Supports up to 11 garment reference images in one call (multi-garment try-on).",
        args=[
            _img(("--person-image", "--model-image"), "person_image", "Person/model image (path or URL)", required=True),
            Arg(("--garment-image", "--garment-images", "--cloth-image"), "garment_images", nargs="+", required=True,
                help="One or more garment reference images (paths or URLs), up to 11"),
            Arg(("--prompt",), "prompt", default="", help="Experimental guidance for non-flatlay garment images"),
            Arg(("--seed",), "seed", type=int, help="Seed for reproducibility"),
            Arg(("--turbo",), "turbo", action="store_true", help="Faster inference; not recommended for >4 garments"),
            Arg(("--output-format",), "output_format", default="jpg", choices=["jpg", "png", "webp"]),
            Arg(("--output-quality",), "output_quality", type=int, default=95, help="JPEG/WebP quality 0-100"),
            Arg(("--reference-pose",), "reference_pose", help="EXPERIMENTAL: reference pose image to repose the person before try-on"),
        ],
    ),
    "nano-banana-2-lite": ModelSpec(
        id="nano-banana-2-lite",
        label="Nano Banana 2 Lite (Gemini 3.1 Flash-Lite Image, via multi-image composition)",
        import_path="tryon.api.nano_banana",
        class_name="NanoBanana2LiteAdapter",
        method="generate_virtual_tryon",
        output_kind="images",
        env_hint="GEMINI_API_KEY",
        notes="Fast/cheap option, not the highest-fidelity one -- not optimized for multiple reference inputs per Google's docs.",
        args=[
            _img(("--person-image", "--model-image"), "person", "Person/model image (path or URL)", required=True),
            _img(("--garment-image", "--cloth-image"), "garment", "Garment reference image (path or URL)", required=True),
            Arg(("--prompt",), "prompt", "Full styling prompt (overrides --garment-description)"),
            Arg(("--garment-description",), "garment_description", help="Short garment description used to build the default prompt"),
            _gemini_aspect_ratio(),
        ],
    ),
    "fashn-tryon-max": ModelSpec(
        id="fashn-tryon-max",
        label="FASHN Try-On Max",
        import_path="tryon.api.vton.fashn",
        class_name="FashnVTONAdapter",
        method="generate_and_decode",
        output_kind="images",
        env_hint="FASHN_API_KEY",
        notes="Recommended FASHN try-on endpoint: enhanced fidelity, up to 4K, prompt-based styling.",
        args=[
            _img(("--person-image", "--model-image"), "model_image", "Person/model image (path or URL)", required=True),
            _img(("--garment-image", "--product-image", "--cloth-image"), "product_image",
                 "Garment/product image (path or URL)", required=True),
            Arg(("--prompt",), "prompt", help='Optional styling instruction, e.g. "roll up sleeves"'),
            Arg(("--resolution",), "resolution", choices=["1k", "2k", "4k"], help="Output resolution tier (default: 1k)"),
            Arg(("--generation-mode",), "generation_mode", choices=["fast", "balanced", "quality"],
                help="Quality/speed trade-off (default: auto/balanced)"),
            Arg(("--seed",), "seed", type=int, help="Seed for reproducibility"),
            Arg(("--num-images",), "num_images", type=int, help="Number of outputs 1-4"),
            Arg(("--output-format",), "output_format", default="png", choices=["png", "jpeg"]),
            Arg(("--model-name",), "model_name", default="tryon-max", choices=["tryon-max"],
                help="FASHN model name (fixed for this registry entry)"),
        ],
    ),
    "qwen-image": ModelSpec(
        id="qwen-image",
        label="Qwen-Image 3.0 (DashScope I2I virtual try-on)",
        import_path="tryon.api.qwen",
        class_name="QwenImageAdapter",
        method="generate_virtual_tryon",
        output_kind="images",
        env_hint="DASHSCOPE_API_KEY",
        notes="Person + garment I2I via Qwen-Image (same DashScope key as qwen3.8-max). "
        "Composition try-on, not a dedicated garment-fit model. Pair with "
        "`understand --model qwen3.8-max` to caption the garment first.",
        args=[
            _img(("--person-image", "--model-image"), "person", "Person/model image (path or URL)", required=True),
            _img(("--garment-image", "--cloth-image"), "garment", "Garment reference image (path or URL)", required=True),
            Arg(("--prompt",), "prompt", "Full styling prompt (overrides --garment-description)"),
            Arg(("--garment-description",), "garment_description",
                help="Short garment description used to build the default prompt"),
            *_qwen_image_common_args(),
        ],
    ),
    "qwen-image-local": ModelSpec(
        id="qwen-image-local",
        label="Qwen-Image-Edit-2511 (open-weight, local VTON)",
        import_path="tryon.models.qwen_image",
        class_name="QwenImageLocalAdapter",
        method="generate_virtual_tryon",
        output_kind="images",
        extra="local",
        notes="Local Diffusers Edit-Plus (default Qwen/Qwen-Image-Edit-2511). "
        "Person + garment I2I; needs CUDA + `pip install opentryon[local]` and "
        "a recent Diffusers. ~40GB+ VRAM bf16; cpu_offload on by default. "
        "Hosted twin: --model qwen-image.",
        args=[
            _img(("--person-image", "--model-image"), "person", "Person/model image (path or URL)", required=True),
            _img(("--garment-image", "--cloth-image"), "garment", "Garment reference image (path or URL)", required=True),
            Arg(("--prompt",), "prompt", "Full styling prompt (overrides --garment-description)"),
            Arg(("--garment-description",), "garment_description",
                help="Short garment description used to build the default prompt"),
            *_qwen_image_local_sample_args(t2i=False),
        ],
    ),
    "fashn-tryon-v1.6": ModelSpec(
        id="fashn-tryon-v1.6",
        label="FASHN Virtual Try-On v1.6",
        import_path="tryon.api.vton.fashn",
        class_name="FashnVTONAdapter",
        method="generate_and_decode",
        output_kind="images",
        env_hint="FASHN_API_KEY",
        notes="Fast/lightweight FASHN try-on for real-time e-commerce (1 credit/image).",
        args=[
            _img(("--person-image", "--model-image"), "model_image", "Person/model image (path or URL)", required=True),
            _img(("--garment-image", "--cloth-image"), "product_image",
                 "Garment/cloth image (path or URL)", required=True),
            Arg(("--category",), "category", default="auto",
                choices=["auto", "tops", "bottoms", "one-pieces"]),
            Arg(("--mode",), "mode", default="balanced",
                choices=["performance", "balanced", "quality"]),
            Arg(("--garment-photo-type",), "garment_photo_type", default="auto",
                choices=["auto", "flat-lay", "model"]),
            Arg(("--moderation-level",), "moderation_level", default="permissive",
                choices=["conservative", "permissive", "none"]),
            Arg(("--seed",), "seed", type=int, help="Seed for reproducibility"),
            Arg(("--num-samples",), "num_samples", type=int, help="Number of outputs 1-4"),
            Arg(("--output-format",), "output_format", default="png", choices=["png", "jpeg"]),
            Arg(("--model-name",), "model_name", default="tryon-v1.6", choices=["tryon-v1.6"],
                help="FASHN model name (fixed for this registry entry)"),
        ],
    ),
}

# --------------------------------------------------------------------------
# generate (text-to-image)
# --------------------------------------------------------------------------


def _nano_banana_generate_args(with_resolution: bool, with_grounding: bool) -> List[Arg]:
    args = [
        Arg(("--prompt", "-p"), "prompt", required=True, help="Text prompt"),
        _gemini_aspect_ratio(),
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
    "nano-banana-2-lite": ModelSpec(
        id="nano-banana-2-lite", label="Nano Banana 2 Lite (Gemini 3.1 Flash-Lite Image)",
        import_path="tryon.api.nano_banana", class_name="NanoBanana2LiteAdapter",
        method="generate_text_to_image", output_kind="images", env_hint="GEMINI_API_KEY",
        notes="Fastest/cheapest Nano Banana tier; 1K resolution only.",
        args=_nano_banana_generate_args(with_resolution=False, with_grounding=False),
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
            Arg(("--aspect-ratio",), "aspect_ratio", choices=_LUMA_ASPECT_RATIOS,
                help="Luma Photon aspect ratio"),
        ],
    ),
    "seedream": ModelSpec(
        id="seedream", label="ByteDance Seedream 5.0 Pro (BytePlus ModelArk)",
        import_path="tryon.api.byteplus", class_name="SeedreamAdapter",
        method="generate_text_to_image", output_kind="images", env_hint="ARK_API_KEY",
        notes="Also supports Seedream 5.0 Lite / 4.x via --model-version.",
        args=[
            Arg(("--prompt", "-p"), "prompt", required=True, help="Text prompt"),
            Arg(("--size",), "size", default="2K", help="1K, 2K, or WxH"),
            Arg(("--output-format",), "output_format", default="png", choices=["png", "jpeg"]),
            Arg(("--watermark",), "watermark", action="store_true", help="Include AI watermark"),
            Arg(("--seed",), "seed", type=int),
            Arg(("--model-version",), "model_version", target="init", call_name="model",
                default="seedream-5-0-pro",
                choices=["seedream-5-0-pro", "seedream-5-0-lite", "seedream-4-5", "seedream-4-0"]),
        ],
    ),
    "qwen-image": ModelSpec(
        id="qwen-image", label="Qwen-Image 3.0 (DashScope text-to-image)",
        import_path="tryon.api.qwen", class_name="QwenImageAdapter",
        method="generate_text_to_image", output_kind="images", env_hint="DASHSCOPE_API_KEY",
        notes="Qwen-Image T2I. Same DASHSCOPE_API_KEY as understand qwen3.8-max. "
        "Default qwen-image-3.0-pro; thinking + prompt rewrite on.",
        args=[
            Arg(("--prompt", "-p"), "prompt", required=True, help="Text prompt"),
            *_qwen_image_common_args(),
        ],
    ),
    "qwen-image-local": ModelSpec(
        id="qwen-image-local", label="Qwen-Image-2512 (open-weight, local T2I)",
        import_path="tryon.models.qwen_image", class_name="QwenImageLocalAdapter",
        method="generate_text_to_image", output_kind="images", extra="local",
        notes="Local Diffusers T2I (default Qwen/Qwen-Image-2512). Needs CUDA + "
        "`pip install opentryon[local]` and a recent Diffusers. Hosted twin: --model qwen-image.",
        args=[
            Arg(("--prompt", "-p"), "prompt", required=True, help="Text prompt"),
            *_qwen_image_local_sample_args(t2i=True),
        ],
    ),
    "ideogram": ModelSpec(
        id="ideogram", label="Ideogram 4.0",
        import_path="tryon.api.ideogram", class_name="IdeogramAdapter",
        method="generate_text_to_image", output_kind="images", env_hint="IDEOGRAM_API_KEY",
        notes="Rendering speed tiers: TURBO / DEFAULT / QUALITY.",
        args=[
            Arg(("--prompt", "-p"), "prompt", required=True, help="Text prompt"),
            Arg(("--rendering-speed",), "rendering_speed", default="DEFAULT",
                choices=["TURBO", "DEFAULT", "QUALITY"]),
            Arg(("--aspect-ratio",), "aspect_ratio", choices=_IDEOGRAM_ASPECT_RATIOS,
                help="Ideogram aspect ratio"),
            Arg(("--num-images",), "num_images", type=int, default=1),
            Arg(("--seed",), "seed", type=int),
            Arg(("--style-type",), "style_type"),
            Arg(("--magic-prompt",), "magic_prompt", choices=["AUTO", "ON", "OFF"],
                help="AUTO / ON / OFF"),
        ],
    ),
    "grok-imagine-image": ModelSpec(
        id="grok-imagine-image", label="xAI Grok Imagine Image Quality",
        import_path="tryon.api.xai", class_name="GrokImagineImageAdapter",
        method="generate_text_to_image", output_kind="images", env_hint="XAI_API_KEY",
        args=[
            Arg(("--prompt", "-p"), "prompt", required=True, help="Text prompt"),
            Arg(("--model-version",), "model_version", target="init", call_name="model",
                default="grok-imagine-image-quality",
                choices=["grok-imagine-image-quality", "grok-imagine-image", "grok-imagine-image-pro"]),
            Arg(("--n",), "n", type=int, default=1, help="Number of images"),
            Arg(("--aspect-ratio",), "aspect_ratio", help="e.g. 1:1, 16:9, 9:16"),
            Arg(("--resolution",), "resolution", choices=["1k", "2k"], help="Output resolution"),
        ],
    ),
    "p-image": ModelSpec(
        id="p-image", label="Pruna P-Image",
        import_path="tryon.api.pruna", class_name="PImageAdapter",
        method="generate_text_to_image", output_kind="images", env_hint="PRUNA_API_KEY",
        notes="Ultra-fast T2I with optional prompt upsampling and LoRA weights.",
        args=[
            Arg(("--prompt", "-p"), "prompt", required=True, help="Text prompt"),
            Arg(("--aspect-ratio",), "aspect_ratio", default="16:9",
                choices=["1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3", "custom"]),
            Arg(("--width",), "width", type=int, help="Custom width (256-1440, multiple of 16); requires --aspect-ratio custom"),
            Arg(("--height",), "height", type=int, help="Custom height (256-1440, multiple of 16); requires --aspect-ratio custom"),
            Arg(("--seed",), "seed", type=int),
            Arg(("--prompt-upsampling",), "prompt_upsampling", action="store_true",
                help="Upsample the prompt with an LLM"),
            Arg(("--lora-weights",), "lora_weights", help="HuggingFace LoRA URL"),
            Arg(("--lora-scale",), "lora_scale", type=float, help="LoRA strength (-1 to 3)"),
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
            _gemini_aspect_ratio(),
        ],
    ),
    "nano-banana-pro": ModelSpec(
        id="nano-banana-pro", label="Nano Banana Pro",
        import_path="tryon.api.nano_banana", class_name="NanoBananaProAdapter",
        method="generate_image_edit", output_kind="images", env_hint="GEMINI_API_KEY",
        args=[
            _img(("--image", "-i"), "image", "Input image (path or URL)", required=True),
            Arg(("--prompt", "-p"), "prompt", required=True, help="Editing instruction"),
            _gemini_aspect_ratio(),
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
            _gemini_aspect_ratio(),
            Arg(("--resolution",), "resolution", default="2K", choices=["1K", "2K", "4K"]),
        ],
    ),
    "nano-banana-2-lite": ModelSpec(
        id="nano-banana-2-lite", label="Nano Banana 2 Lite",
        import_path="tryon.api.nano_banana", class_name="NanoBanana2LiteAdapter",
        method="generate_image_edit", output_kind="images", env_hint="GEMINI_API_KEY",
        notes="Fastest/cheapest Nano Banana tier; 1K resolution only.",
        args=[
            _img(("--image", "-i"), "image", "Input image (path or URL)", required=True),
            Arg(("--prompt", "-p"), "prompt", required=True, help="Editing instruction"),
            _gemini_aspect_ratio(),
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
    "seedream": ModelSpec(
        id="seedream", label="ByteDance Seedream 5.0 Pro (edit / multi-ref)",
        import_path="tryon.api.byteplus", class_name="SeedreamAdapter",
        method="generate_image_edit", output_kind="images", env_hint="ARK_API_KEY",
        notes="Pass one image for edit, or multiple refs (2-10) for fusion.",
        args=[
            Arg(("--images",), "image", nargs="+", required=True, help="One or more reference images"),
            Arg(("--prompt", "-p"), "prompt", required=True, help="Editing / fusion instruction"),
            Arg(("--size",), "size", default="2K"),
            Arg(("--output-format",), "output_format", default="png", choices=["png", "jpeg"]),
            Arg(("--seed",), "seed", type=int),
            Arg(("--model-version",), "model_version", target="init", call_name="model",
                default="seedream-5-0-pro",
                choices=["seedream-5-0-pro", "seedream-5-0-lite", "seedream-4-5", "seedream-4-0"]),
        ],
    ),
    "qwen-image": ModelSpec(
        id="qwen-image", label="Qwen-Image 3.0 (DashScope image edit / I2I)",
        import_path="tryon.api.qwen", class_name="QwenImageAdapter",
        method="generate_image_edit", output_kind="images", env_hint="DASHSCOPE_API_KEY",
        notes="1–3 reference images + instruction. Same DASHSCOPE_API_KEY as qwen3.8-max.",
        args=[
            Arg(("--images",), "image", nargs="+", required=True,
                help="1–3 reference images (paths or URLs)"),
            Arg(("--prompt", "-p"), "prompt", required=True, help="Editing / composition instruction"),
            *_qwen_image_common_args(),
        ],
    ),
    "qwen-image-local": ModelSpec(
        id="qwen-image-local", label="Qwen-Image-Edit-2511 (open-weight, local I2I)",
        import_path="tryon.models.qwen_image", class_name="QwenImageLocalAdapter",
        method="generate_image_edit", output_kind="images", extra="local",
        notes="Local Diffusers Edit-Plus (1–3 refs). Default Qwen/Qwen-Image-Edit-2511. "
        "Needs CUDA + `pip install opentryon[local]`. Hosted twin: --model qwen-image.",
        args=[
            Arg(("--images",), "image", nargs="+", required=True,
                help="1–3 reference images (paths or URLs)"),
            Arg(("--prompt", "-p"), "prompt", required=True, help="Editing / composition instruction"),
            *_qwen_image_local_sample_args(t2i=False),
        ],
    ),
    "p-image-edit": ModelSpec(
        id="p-image-edit", label="Pruna P-Image-Edit",
        import_path="tryon.api.pruna", class_name="PImageEditAdapter",
        method="generate_image_edit", output_kind="images", env_hint="PRUNA_API_KEY",
        notes="Compose/edit with 1–5 reference images.",
        args=[
            Arg(("--images",), "image", nargs="+", required=True, help="1–5 reference images (paths or URLs)"),
            Arg(("--prompt", "-p"), "prompt", required=True, help="Edit / composition instruction"),
            Arg(("--aspect-ratio",), "aspect_ratio", default="match_input_image",
                choices=["match_input_image", "1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3"]),
            Arg(("--no-turbo",), "turbo", action="store_false", default=True,
                help="Disable turbo mode for harder edits"),
            Arg(("--seed",), "seed", type=int),
        ],
    ),
    "p-image-upscale": ModelSpec(
        id="p-image-upscale", label="Pruna P-Image-Upscale",
        import_path="tryon.api.pruna", class_name="PImageUpscaleAdapter",
        method="upscale", output_kind="images", env_hint="PRUNA_API_KEY",
        notes="Upscale to a target megapixel count (1–128 MP).",
        args=[
            _img(("--image", "-i"), "image", "Input image (path or URL)", required=True),
            Arg(("--target",), "target", type=int, default=4, help="Target resolution in megapixels (1-128)"),
            Arg(("--output-format",), "output_format", default="jpg", choices=["jpg", "png", "webp"]),
            Arg(("--output-quality",), "output_quality", type=int, default=80, help="JPEG/WebP quality 0-100"),
            Arg(("--enhance-details",), "enhance_details", action="store_true"),
            Arg(("--enhance-realism",), "enhance_realism", action="store_true"),
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
    "kimi-k3": ModelSpec(
        id="kimi-k3", label="Kimi K3 (Moonshot AI flagship multimodal reasoning model)",
        import_path="tryon.api.kimi", class_name="KimiUnderstandAdapter",
        method="understand", output_kind="text", env_hint="MOONSHOT_API_KEY",
        notes="Official Moonshot K3 API channel. K3 always uses thinking mode; use reasoning_effort to control depth.",
        args=[
            Arg(("--kimi-model",), "kimi_model", target="init", call_name="model", default="kimi-k3",
                choices=["kimi-k3"], help="Kimi model variant"),
            Arg(("--image", "-i"), "image", help="Image to understand (path or URL)"),
            Arg(("--video",), "video", help="Video to understand (path or URL)"),
            Arg(("--prompt", "-p"), "prompt", help="Question/instruction for the model"),
            Arg(("--reasoning-effort",), "reasoning_effort", default="max",
                choices=["low", "high", "max"], help="K3 reasoning effort level"),
            Arg(("--max-tokens",), "max_tokens", type=int, help="Max completion tokens (server default: 131072)"),
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
    "qwen3.8-max": ModelSpec(
        id="qwen3.8-max", label="Qwen3.8-Max (DashScope multimodal understanding)",
        import_path="tryon.api.qwen", class_name="QwenUnderstandAdapter",
        method="understand", output_kind="text", env_hint="DASHSCOPE_API_KEY",
        notes="Hosted Qwen3.8-Max via DashScope OpenAI-compatible API. Native text/image/video. "
        "Thinking on by default; use --no-thinking or --reasoning-effort to control.",
        args=[
            Arg(("--qwen-model",), "qwen_model", target="init", call_name="model", default="qwen3.8-max",
                choices=["qwen3.8-max"], help="Qwen DashScope model id"),
            Arg(("--image", "-i"), "image", help="Image to understand (path or URL)"),
            Arg(("--video",), "video", help="Video to understand (path or URL)"),
            Arg(("--prompt", "-p"), "prompt", help="Question/instruction for the model"),
            Arg(("--no-thinking",), "enable_thinking", action="store_false", default=True,
                help="Disable Qwen thinking mode (enable_thinking=False)"),
            Arg(("--reasoning-effort",), "reasoning_effort", default="xhigh",
                choices=["xhigh", "medium", "low"], help="Reasoning depth (xhigh/medium/low)"),
            Arg(("--max-tokens",), "max_tokens", type=int, help="Max output tokens"),
        ],
    ),
    "qwen3.8": ModelSpec(
        id="qwen3.8", label="Qwen3.8-27B (open-weight, local)",
        import_path="tryon.models.qwen38", class_name="Qwen38Adapter",
        method="understand", output_kind="text", extra="local",
        notes="Open-weight counterpart to qwen3.8-max. Default HF id Qwen/Qwen3.8-27B. "
        "Needs recent transformers + substantial VRAM (bf16 ~50GB+). "
        "Requires `pip install opentryon[local]`.",
        args=[
            Arg(("--image", "-i"), "image", help="Image to understand (path or URL)"),
            Arg(("--video",), "video", help="Video to understand (path or URL, requires `pip install decord`)"),
            Arg(("--prompt", "-p"), "prompt", help="Question/instruction for the model"),
            Arg(("--num-frames",), "num_frames", type=int, default=8, help="Frames to sample from --video"),
            Arg(("--max-new-tokens",), "max_new_tokens", type=int, default=4096, help="Max output tokens"),
            Arg(("--temperature",), "temperature", type=float, default=0.8, help="Sampling temperature"),
            Arg(("--no-thinking",), "enable_thinking", action="store_false", default=True,
                help="Disable thinking mode in the chat template"),
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
    "gemini-omni": ModelSpec(
        id="gemini-omni",
        label="Gemini Omni Flash (video generation / conversational editing)",
        import_path="tryon.api.omni",
        class_name="GeminiOmniAdapter",
        method="generate_text_to_video",
        output_kind="video_bytes",
        alt_method_on_image="generate_image_to_video",
        alt_image_dest="image",
        env_hint="GEMINI_API_KEY",
        notes=(
            "Uses gemini-omni-flash-preview via the Interactions API. "
            "Pass --previous-interaction-id to conversationally edit a prior clip."
        ),
        args=[
            Arg(("--prompt", "-p"), "prompt", required=True, help="Text prompt or edit instruction"),
            Arg(("--image",), "image", help="Optional still image to animate (switches to image-to-video)", alt_only=True),
            Arg(("--reference-image",), "reference_images", nargs="+",
                help="Optional extra subject/style reference images (image-to-video only)", alt_only=True),
            Arg(("--aspect-ratio",), "aspect_ratio", default="16:9", choices=["16:9", "9:16"]),
            Arg(("--previous-interaction-id",), "previous_interaction_id",
                help="Prior Omni interaction id for conversational video editing"),
        ],
    ),
    "seedance": ModelSpec(
        id="seedance",
        label="ByteDance Seedance 2.5 (BytePlus ModelArk)",
        import_path="tryon.api.byteplus",
        class_name="SeedanceAdapter",
        method="generate_text_to_video",
        output_kind="video_bytes",
        alt_method_on_image="generate_image_to_video",
        alt_image_dest="image",
        env_hint="ARK_API_KEY",
        notes=(
            "Seedance 2.5 targets up to 30s audio-video clips. "
            "Also supports Seedance 2.0 Standard/Fast/Mini via --model-version. "
            "See https://seed.bytedance.com/en/seedance2_5"
        ),
        args=[
            Arg(("--prompt", "-p"), "prompt", help="Text prompt"),
            Arg(("--image",), "image", help="Optional first-frame image (switches to image-to-video)", alt_only=True),
            Arg(("--end-image",), "end_image", help="Optional last-frame image (I2V only)", alt_only=True),
            Arg(("--duration",), "duration", type=int, default=5, help="Clip length in seconds"),
            Arg(("--ratio",), "ratio", default="16:9",
                choices=["21:9", "16:9", "4:3", "1:1", "3:4", "9:16"]),
            Arg(("--resolution",), "resolution", default="720p",
                choices=["480p", "720p", "1080p", "2k", "4k"]),
            Arg(("--no-audio",), "generate_audio", action="store_false", default=True,
                help="Disable native audio generation"),
            Arg(("--seed",), "seed", type=int),
            Arg(("--model-version",), "model_version", target="init", call_name="model",
                default="seedance-2-5",
                choices=[
                    "seedance-2-5",
                    "seedance-2-0",
                    "seedance-2-0-fast",
                    "seedance-2-0-mini",
                    "dreamina-seedance-2-0-260128",
                    "dreamina-seedance-2-0-fast-260128",
                    "dreamina-seedance-2-0-mini-260615",
                ]),
        ],
    ),
    "luma-ray-3.2": ModelSpec(
        id="luma-ray-3.2",
        label="Luma Ray 3.2 (Agents API)",
        import_path="tryon.api.lumaAI.ray32_adapter",
        class_name="LumaRay32Adapter",
        method="generate_text_to_video",
        output_kind="video_bytes",
        alt_method_on_image="generate_image_to_video",
        alt_image_dest="start_image",
        env_hint="LUMA_AGENTS_API_KEY / LUMA_AI_API_KEY",
        notes="Professional Ray 3.2 via Luma Agents API (HDR, start/end frames).",
        args=[
            Arg(("--prompt", "-p"), "prompt", help="Text prompt"),
            Arg(("--image",), "start_image", help="Optional start frame (switches to image-to-video)", alt_only=True),
            Arg(("--end-image",), "end_image", help="Optional end frame (I2V only)", alt_only=True),
            Arg(("--resolution",), "resolution", default="720p",
                choices=["360p", "540p", "720p", "1080p"]),
            Arg(("--duration",), "duration", default="5s", choices=["5s", "10s"]),
            Arg(("--aspect-ratio",), "aspect_ratio", default="16:9"),
            Arg(("--loop",), "loop", action="store_true"),
            Arg(("--hdr",), "hdr", action="store_true", help="Native 16-bit HDR output"),
            Arg(("--model-version",), "model_version", target="init", call_name="model",
                default="ray-3.2", choices=["ray-3.2"]),
        ],
    ),
    "kling-v3": ModelSpec(
        id="kling-v3",
        label="Kling 3.0 video",
        import_path="tryon.api.kling_video",
        class_name="KlingVideoAdapter",
        method="generate_text_to_video",
        output_kind="video_bytes",
        alt_method_on_image="generate_image_to_video",
        alt_image_dest="image",
        env_hint="KLING_AI_API_KEY / KLING_AI_SECRET_KEY",
        notes="Official Kling Open Platform. Duration 3-15s; mode std/pro.",
        args=[
            Arg(("--prompt", "-p"), "prompt", help="Text prompt"),
            Arg(("--image",), "image", help="Optional start image (switches to image-to-video)", alt_only=True),
            Arg(("--end-image",), "end_image", help="Optional end frame (I2V only)", alt_only=True),
            Arg(("--duration",), "duration", default="5", help="3-15 seconds"),
            Arg(("--mode",), "mode", default="pro", choices=["std", "pro"]),
            Arg(("--aspect-ratio",), "aspect_ratio", default="16:9", choices=["16:9", "9:16", "1:1"]),
            Arg(("--negative-prompt",), "negative_prompt"),
            Arg(("--sound",), "sound", default="off", choices=["on", "off"]),
            Arg(("--model-version",), "model_version", target="init", call_name="model",
                default="kling-v3", choices=["kling-v3"]),
        ],
    ),
    "kling-v3-omni": ModelSpec(
        id="kling-v3-omni",
        label="Kling 3.0 Omni video",
        import_path="tryon.api.kling_video",
        class_name="KlingVideoAdapter",
        method="generate_text_to_video",
        output_kind="video_bytes",
        alt_method_on_image="generate_image_to_video",
        alt_image_dest="image",
        env_hint="KLING_AI_API_KEY / KLING_AI_SECRET_KEY",
        notes="Unified multimodal Kling Omni endpoint (elements, refs, audio).",
        args=[
            Arg(("--prompt", "-p"), "prompt", help="Text prompt"),
            Arg(("--image",), "image", help="Optional reference / start image", alt_only=True),
            Arg(("--end-image",), "end_image", help="Optional end frame", alt_only=True),
            Arg(("--duration",), "duration", default="5"),
            Arg(("--mode",), "mode", default="pro", choices=["std", "pro", "4k"]),
            Arg(("--aspect-ratio",), "aspect_ratio", default="16:9", choices=["16:9", "9:16", "1:1"]),
            Arg(("--negative-prompt",), "negative_prompt"),
            Arg(("--sound",), "sound", default="off", choices=["on", "off"]),
            Arg(("--model-version",), "model_version", target="init", call_name="model",
                default="kling-v3-omni", choices=["kling-v3-omni"]),
        ],
    ),
    "kling-v2-5-turbo": ModelSpec(
        id="kling-v2-5-turbo",
        label="Kling 2.5 Turbo video",
        import_path="tryon.api.kling_video",
        class_name="KlingVideoAdapter",
        method="generate_text_to_video",
        output_kind="video_bytes",
        alt_method_on_image="generate_image_to_video",
        alt_image_dest="image",
        env_hint="KLING_AI_API_KEY / KLING_AI_SECRET_KEY",
        notes="Fast Kling Turbo tier for rapid iteration.",
        args=[
            Arg(("--prompt", "-p"), "prompt", help="Text prompt"),
            Arg(("--image",), "image", help="Optional start image", alt_only=True),
            Arg(("--end-image",), "end_image", help="Optional end frame", alt_only=True),
            Arg(("--duration",), "duration", default="5"),
            Arg(("--mode",), "mode", default="std", choices=["std", "pro"]),
            Arg(("--aspect-ratio",), "aspect_ratio", default="16:9", choices=["16:9", "9:16", "1:1"]),
            Arg(("--negative-prompt",), "negative_prompt"),
            Arg(("--cfg-scale",), "cfg_scale", type=float),
            Arg(("--model-version",), "model_version", target="init", call_name="model",
                default="kling-v2-5-turbo", choices=["kling-v2-5-turbo"]),
        ],
    ),
    "grok-imagine-video": ModelSpec(
        id="grok-imagine-video",
        label="xAI Grok Imagine Video 1.5",
        import_path="tryon.api.xai",
        class_name="GrokImagineVideoAdapter",
        method="generate_text_to_video",
        output_kind="video_bytes",
        alt_method_on_image="generate_image_to_video",
        alt_image_dest="image",
        env_hint="XAI_API_KEY",
        notes="Supports T2V and I2V up to 1080p. See https://docs.x.ai/developers/models/grok-imagine-video-1.5",
        args=[
            Arg(("--prompt", "-p"), "prompt", required=True, help="Text prompt"),
            Arg(("--image",), "image", help="Optional start image (switches to image-to-video)", alt_only=True),
            Arg(("--duration",), "duration", type=int, default=6, help="Duration in seconds (up to 15)"),
            Arg(("--aspect-ratio",), "aspect_ratio", default="16:9"),
            Arg(("--resolution",), "resolution", default="720p", choices=["480p", "720p", "1080p"]),
            Arg(("--model-version",), "model_version", target="init", call_name="model",
                default="grok-imagine-video-1.5",
                choices=["grok-imagine-video-1.5"]),
        ],
    ),
    "p-video": ModelSpec(
        id="p-video",
        label="Pruna P-Video",
        import_path="tryon.api.pruna",
        class_name="PVideoAdapter",
        method="generate_text_to_video",
        output_kind="video_bytes",
        alt_method_on_image="generate_image_to_video",
        alt_image_dest="image",
        env_hint="PRUNA_API_KEY",
        notes="T2V / I2V with optional audio conditioning, draft mode, and prompt upsampling.",
        args=[
            Arg(("--prompt", "-p"), "prompt", required=True, help="Text prompt"),
            Arg(("--image",), "image", help="Optional start image (switches to image-to-video)", alt_only=True),
            Arg(("--audio",), "audio", help="Optional audio file (flac/mp3/wav) to condition duration"),
            Arg(("--last-frame-image",), "last_frame_image", help="Optional last-frame reference image"),
            Arg(("--duration",), "duration", type=int, default=5, help="Duration in seconds (1-20); ignored when audio is set"),
            Arg(("--resolution",), "resolution", default="720p", choices=["720p", "1080p"]),
            Arg(("--fps",), "fps", type=int, default=24, choices=[24, 48]),
            Arg(("--aspect-ratio",), "aspect_ratio", default="16:9",
                choices=["16:9", "9:16", "4:3", "3:4", "3:2", "2:3", "1:1"]),
            Arg(("--seed",), "seed", type=int),
            Arg(("--draft",), "draft", action="store_true", help="Faster lower-quality draft preview"),
            Arg(("--no-save-audio",), "save_audio", action="store_false", default=True),
            Arg(("--no-prompt-upsampling",), "prompt_upsampling", action="store_false", default=True),
        ],
    ),
    "p-video-replace": ModelSpec(
        id="p-video-replace",
        label="Pruna P-Video-Replace",
        import_path="tryon.api.pruna",
        class_name="PVideoReplaceAdapter",
        method="generate_video_replace",
        output_kind="video_bytes",
        env_hint="PRUNA_API_KEY",
        notes="Replace people in a source video using 1–3 identity reference images.",
        args=[
            Arg(("--video",), "video", required=True, help="Source RGB video (.mp4 path or URL)"),
            Arg(("--images",), "images", nargs="+", required=True, help="1–3 identity reference images"),
            Arg(("--instruction-prompt", "-p"), "instruction_prompt", default="",
                help="Optional placement / scene instruction"),
            Arg(("--resolution",), "resolution", default="720p", choices=["720p", "1080p"]),
            Arg(("--target-fps",), "target_fps", default="original", choices=["original", "24", "48"]),
            Arg(("--turbo",), "turbo", action="store_true"),
            Arg(("--no-save-audio",), "save_audio", action="store_false", default=True),
            Arg(("--ignore-audio",), "ignore_audio", action="store_true"),
            Arg(("--seed",), "seed", type=int),
        ],
    ),
    "p-video-avatar": ModelSpec(
        id="p-video-avatar",
        label="Pruna P-Video-Avatar",
        import_path="tryon.api.pruna",
        class_name="PVideoAvatarAdapter",
        method="generate_video_avatar",
        output_kind="video_bytes",
        env_hint="PRUNA_API_KEY",
        notes="Talking-head avatar from a portrait + voice_script and/or audio (audio wins if both).",
        args=[
            _img(("--image", "-i"), "image", "Portrait / first-frame image (path or URL)", required=True),
            Arg(("--voice-script",), "voice_script", default="",
                help="Script to speak when no --audio is provided"),
            Arg(("--audio",), "audio", help="Speech audio file (flac/mp3/wav); overrides voice_script"),
            Arg(("--voice",), "voice", default="Zephyr (Female)",
                help='TTS voice name, e.g. "Zephyr (Female)", "Puck (Male)"'),
            Arg(("--voice-language",), "voice_language", default="English (US)",
                choices=[
                    "English (US)", "English (UK)", "Spanish", "French", "German",
                    "Italian", "Portuguese (Brazil)", "Japanese", "Korean", "Hindi",
                ]),
            Arg(("--resolution",), "resolution", default="720p", choices=["720p", "1080p"]),
            Arg(("--video-prompt",), "video_prompt", default="The person is talking."),
            Arg(("--voice-prompt",), "voice_prompt", default="Say the following.",
                help="Speaking style / tone / pacing instruction"),
            Arg(("--negative-prompt",), "negative_prompt", default=""),
            Arg(("--strength-negative-prompt",), "strength_negative_prompt", type=float, default=0.5),
            Arg(("--seed",), "seed", type=int),
            Arg(("--disable-prompt-upsampling",), "disable_prompt_upsampling", action="store_true"),
        ],
    ),
    "p-video-animate": ModelSpec(
        id="p-video-animate",
        label="Pruna P-Video-Animate",
        import_path="tryon.api.pruna",
        class_name="PVideoAnimateAdapter",
        method="generate_video_animate",
        output_kind="video_bytes",
        env_hint="PRUNA_API_KEY",
        notes="Animate a subject reference image using motion (and audio) from a source video.",
        args=[
            Arg(("--video",), "video", required=True, help="Source RGB video (.mp4 path or URL)"),
            _img(("--image", "-i"), "image", "Subject reference image (path or URL)", required=True),
            Arg(("--instruction-prompt", "-p"), "instruction_prompt", default="",
                help="Optional animation / scene instruction"),
            Arg(("--resolution",), "resolution", default="720p", choices=["720p", "1080p"]),
            Arg(("--target-fps",), "target_fps", default="original", choices=["original", "24", "48"]),
            Arg(("--turbo",), "turbo", action="store_true"),
            Arg(("--no-save-audio",), "save_audio", action="store_false", default=True),
            Arg(("--ignore-audio",), "ignore_audio", action="store_true"),
            Arg(("--seed",), "seed", type=int),
        ],
    ),
    "ltx-2.5-api": ModelSpec(
        id="ltx-2.5-api",
        label="LTX-2.5 (official API)",
        import_path="tryon.api.ltx",
        class_name="LTXVideoAdapter",
        method="generate_text_to_video",
        output_kind="video_bytes",
        alt_method_on_image="generate_image_to_video",
        alt_image_dest="image",
        env_hint="LTX_API_KEY",
        notes=(
            "First-party LTX API (async V2 by default). Models: ltx-2-5-fast / ltx-2-5-pro. "
            "Pass --duration auto for automatic clip length. Synced audio on by default."
        ),
        args=[
            Arg(("--prompt", "-p"), "prompt", required=True, help="Text prompt (long A/V captions work best)"),
            Arg(("--image",), "image", help="Optional still to animate (switches to image-to-video)", alt_only=True),
            Arg(("--last-frame",), "last_frame", help="Optional last-frame image (image-to-video only)", alt_only=True),
            Arg(
                ("--model-version",),
                "model_version",
                call_name="model",
                default="ltx-2-5-pro",
                choices=["ltx-2-5-fast", "ltx-2-5-pro", "fast", "pro"],
                help="LTX-2.5 Fast or Pro",
            ),
            Arg(
                ("--duration",),
                "duration",
                default="8",
                help='Seconds (e.g. 6, 8, 10) or "auto" for model-chosen length',
            ),
            Arg(
                ("--resolution",),
                "resolution",
                default="1920x1080",
                help="WxH, e.g. 1280x720, 1920x1080, 1080x1920 (see LTX-2.5 matrix)",
            ),
            Arg(("--fps",), "fps", type=int, default=24, help="Frame rate (24/25/48/50 depending on tier)"),
            Arg(
                ("--no-audio",),
                "generate_audio",
                action="store_false",
                default=True,
                help="Disable synchronized audio generation",
            ),
            Arg(
                ("--camera-motion",),
                "camera_motion",
                choices=[
                    "dolly_in", "dolly_out", "dolly_left", "dolly_right",
                    "jib_up", "jib_down", "static", "focus_shift",
                ],
                help="Optional camera motion preset",
            ),
        ],
    ),
    "ltx-2.5": ModelSpec(
        id="ltx-2.5",
        label="LTX-2.5 (local Diffusers)",
        import_path="tryon.models.ltx25",
        class_name="LTX25Adapter",
        method="generate_text_to_video",
        output_kind="video_bytes",
        alt_method_on_image="generate_image_to_video",
        alt_image_dest="image",
        extra="local",
        notes=(
            "Open weights via Hugging Face Diffusers (requires CUDA + diffusers from main). "
            "Gated model: accept terms on HF and set HF_TOKEN. Default distilled recipe."
        ),
        args=[
            Arg(("--prompt", "-p"), "prompt", required=True, help="Long audiovisual caption works best"),
            Arg(("--image",), "image", help="Optional still to animate (switches to image-to-video)", alt_only=True),
            Arg(("--negative-prompt",), "negative_prompt", help="Optional negative prompt"),
            Arg(("--width",), "width", type=int, default=960, help="Width (divisible by 32)"),
            Arg(("--height",), "height", type=int, default=544, help="Height (divisible by 32)"),
            Arg(
                ("--num-frames",),
                "num_frames",
                type=int,
                default=121,
                help="Frame count; must satisfy num_frames % 8 == 1 (e.g. 97, 121)",
            ),
            Arg(("--frame-rate",), "frame_rate", type=float, default=24.0, help="Output FPS"),
            Arg(("--seed",), "seed", type=int, help="RNG seed"),
            Arg(
                ("--model-id",),
                "model_id",
                target="init",
                help="HF repo id or local path (default Lightricks/LTX-2.5-Diffusers)",
            ),
        ],
    ),
    "hailuo-2.3": ModelSpec(
        id="hailuo-2.3",
        label="MiniMax Hailuo 2.3 (official API)",
        import_path="tryon.api.minimax",
        class_name="HailuoVideoAdapter",
        method="generate_text_to_video",
        output_kind="video_bytes",
        alt_method_on_image="generate_image_to_video",
        alt_image_dest="image",
        env_hint="MINIMAX_API_KEY",
        notes=(
            "First-party MiniMax Hailuo 2.3 T2V/I2V. No open weights. "
            "Camera moves via [Tracking shot] style commands in the prompt."
        ),
        args=[
            Arg(("--prompt", "-p"), "prompt", help="Text prompt (required for T2V)"),
            Arg(("--image",), "image", help="First-frame image (switches to I2V)", alt_only=True),
            Arg(
                ("--model-version",),
                "model_version",
                call_name="model",
                default="MiniMax-Hailuo-2.3",
                choices=["MiniMax-Hailuo-2.3", "MiniMax-Hailuo-2.3-Fast", "hailuo-2.3", "hailuo-2.3-fast"],
            ),
            Arg(("--duration",), "duration", type=int, default=6, choices=[6, 10]),
            Arg(("--resolution",), "resolution", default="768P", choices=["512P", "720P", "768P", "1080P"]),
            Arg(("--no-prompt-optimizer",), "prompt_optimizer", action="store_false", default=True),
            Arg(("--fast-pretreatment",), "fast_pretreatment", action="store_true"),
        ],
    ),
    "wan-api": ModelSpec(
        id="wan-api",
        label="Alibaba Wan (DashScope / Model Studio API)",
        import_path="tryon.api.wan",
        class_name="WanVideoAdapter",
        method="generate_text_to_video",
        output_kind="video_bytes",
        alt_method_on_image="generate_image_to_video",
        alt_image_dest="image",
        env_hint="DASHSCOPE_API_KEY",
        notes=(
            "First-party Alibaba Wan 2.x via DashScope. Default wan2.6-t2v. "
            "Wan 3.0 is --model wan-3.0. Set WAN_API_BASE_URL for China or workspace endpoints."
        ),
        args=[
            Arg(("--prompt", "-p"), "prompt", help="Text prompt"),
            Arg(("--image",), "image", help="First-frame image (switches to I2V)", alt_only=True),
            Arg(
                ("--model-version",),
                "model_version",
                call_name="model",
                default="wan2.6-t2v",
                help="e.g. wan2.6-t2v, wan2.7-t2v, wan2.2-t2v-plus, wan2.6-i2v, wan3.0-video",
            ),
            Arg(("--duration",), "duration", type=int, default=5),
            Arg(("--resolution",), "resolution", default="720P", help="720P / 1080P (newer models)"),
            Arg(("--size",), "size", help="Optional WxH e.g. 1280*720 for older size-based models"),
            Arg(("--ratio",), "ratio", help="Optional aspect ratio e.g. 16:9"),
            Arg(("--negative-prompt",), "negative_prompt"),
            Arg(("--no-prompt-extend",), "prompt_extend", action="store_false", default=True),
            Arg(("--watermark",), "watermark", action="store_true"),
        ],
    ),
    "wan-3.0": ModelSpec(
        id="wan-3.0",
        label="Alibaba Wan 3.0 (DashScope API)",
        import_path="tryon.api.wan",
        class_name="WanVideoAdapter",
        method="generate_text_to_video",
        output_kind="video_bytes",
        alt_method_on_image="generate_image_to_video",
        alt_image_dest="image",
        env_hint="DASHSCOPE_API_KEY",
        notes=(
            "First-party Wan 3.0 (wan3.0-video). Preview / invitation-gated. "
            "T2V, first-frame I2V, first-last frame, document/URL-to-video. "
            "No open weights; local Wan remains --model wan-2.2."
        ),
        args=[
            Arg(("--prompt", "-p"), "prompt", help="Text prompt (or pair with --file/--link)"),
            Arg(("--image",), "image", help="First-frame image (switches to I2V)", alt_only=True),
            Arg(
                ("--last-frame",),
                "last_frame",
                help="Last-frame image (requires --image)",
                alt_only=True,
            ),
            Arg(
                ("--file",),
                "file",
                help="Public HTTP(S)/OSS document URL (pdf/pptx/docx/…)",
            ),
            Arg(("--link",), "link", help="Public webpage URL (mutually exclusive with --file)"),
            Arg(
                ("--model-version",),
                "model_version",
                call_name="model",
                default="wan3.0-video",
                choices=["wan3.0-video", "wan3.0", "wan-3.0"],
            ),
            Arg(
                ("--duration",),
                "duration",
                type=int,
                default=5,
                help="Seconds 2-30, or -1 for smart duration",
            ),
            Arg(
                ("--resolution",),
                "resolution",
                default="720P",
                choices=["480P", "720P", "1080P"],
            ),
            Arg(
                ("--ratio",),
                "ratio",
                default="adaptive",
                choices=["adaptive", "16:9", "4:3", "1:1", "3:4", "9:16"],
            ),
            Arg(("--seed",), "seed", type=int),
            Arg(("--no-prompt-extend",), "prompt_extend", action="store_false", default=True),
            Arg(("--no-audio",), "audio", action="store_false", default=True,
                help="Generate a silent video"),
            Arg(("--watermark",), "watermark", action="store_true"),
        ],
    ),
    "wan-2.2": ModelSpec(
        id="wan-2.2",
        label="Wan 2.2 (local Diffusers)",
        import_path="tryon.models.wan22",
        class_name="Wan22Adapter",
        method="generate_text_to_video",
        output_kind="video_bytes",
        alt_method_on_image="generate_image_to_video",
        alt_image_dest="image",
        extra="local",
        notes=(
            "Open weights Wan 2.2 via Diffusers. Default Wan-AI/Wan2.2-TI2V-5B-Diffusers. "
            "Requires CUDA + recent diffusers. Wan 3.0 has no official local weights; "
            "use --model wan-3.0 for the hosted API."
        ),
        args=[
            Arg(("--prompt", "-p"), "prompt", required=True, help="Text prompt"),
            Arg(("--image",), "image", help="Optional still (switches to I2V)", alt_only=True),
            Arg(("--negative-prompt",), "negative_prompt"),
            Arg(("--num-frames",), "num_frames", type=int, default=81),
            Arg(("--guidance-scale",), "guidance_scale", type=float, default=5.0),
            Arg(("--num-inference-steps",), "num_inference_steps", type=int, default=40),
            Arg(("--fps",), "fps", type=float, default=16.0),
            Arg(("--width",), "width", type=int),
            Arg(("--height",), "height", type=int),
            Arg(("--seed",), "seed", type=int),
            Arg(
                ("--model-id",),
                "model_id",
                target="init",
                help="HF repo id or path (default Wan-AI/Wan2.2-TI2V-5B-Diffusers)",
            ),
        ],
    ),
    "runway-gen4.5": ModelSpec(
        id="runway-gen4.5",
        label="Runway Gen-4.5 (official API)",
        import_path="tryon.api.runway",
        class_name="RunwayVideoAdapter",
        method="generate_text_to_video",
        output_kind="video_bytes",
        alt_method_on_image="generate_image_to_video",
        alt_image_dest="image",
        env_hint="RUNWAYML_API_SECRET",
        notes="First-party Runway Gen-4.5 T2V/I2V. No open weights.",
        args=[
            Arg(("--prompt", "-p"), "prompt", help="promptText (required for T2V)"),
            Arg(("--image",), "image", help="promptImage (switches to I2V)", alt_only=True),
            Arg(
                ("--model-version",),
                "model_version",
                call_name="model",
                default="gen4.5",
                choices=["gen4.5", "gen-4.5"],
            ),
            Arg(("--duration",), "duration", type=int, default=5, help="Seconds (typically 5 or 10)"),
            Arg(
                ("--ratio",),
                "ratio",
                default="1280:720",
                help="Pixel ratio e.g. 1280:720, 720:1280, 960:960",
            ),
            Arg(("--seed",), "seed", type=int),
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
            _img(("--image", "-i"), "image", "Input image (path, URL, or base64)", required=True),
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
