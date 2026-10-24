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
    alt_only: bool = False  # only passed when an alt method (image or video) is active
    call_name: Optional[str] = None  # adapter kwarg name, if different from dest


@dataclass
class ModelSpec:
    id: str
    label: str
    import_path: str  # dotted submodule path, e.g. "tryon.api.vton.flux_vto"
    class_name: str
    method: str
    output_kind: str  # "images" | "image_bytes" | "video_bytes" | "audio_bytes" | "mesh_bytes" | "text" | "embeddings"
    args: List[Arg] = field(default_factory=list)
    alt_method_on_image: Optional[str] = None
    alt_image_dest: str = "image"
    alt_method_on_video: Optional[str] = None
    alt_video_dest: str = "video"
    extra: str = "core"  # "core" | "local" (needs `pip install opentryon[local]`)
    env_hint: Optional[str] = None
    notes: Optional[str] = None


def _img(flags, dest, help_, required=False, default=None):
    return Arg(flags=flags, dest=dest, help=help_, required=required, default=default)


def _hy4_understand_args(*, endpoint: str) -> List[Arg]:
    """Shared CLI flags for TokenHub Hy4 and the local vLLM/SGLang twin."""
    return [
        Arg(("--prompt", "-p"), "prompt", help="Text prompt (required unless --image is set)"),
        Arg(("--image", "-i"), "image", help="Optional image (OpenAI vision part; Hy4 is a text LLM)"),
        Arg(("--no-thinking",), "enable_thinking", action="store_false", default=True,
            help="Disable Hy4 deep reasoning (TokenHub thinking.type=disabled / local no_think)"),
        Arg(("--reasoning-effort",), "reasoning_effort", default="high",
            choices=["high", "medium", "low"], help="Reasoning depth (Hy4 default high)"),
        Arg(("--max-tokens",), "max_tokens", type=int, help="Max output tokens"),
        Arg(("--temperature",), "temperature", type=float, default=0.9,
            help="Sampling temperature (official default 0.9)"),
        Arg(("--top-p",), "top_p", type=float, default=1.0, help="Nucleus sampling (official default 1.0)"),
        Arg(("--hy-model",), "hy_model", target="init", call_name="model", default="hy4-preview",
            choices=["hy4-preview"], help="Hy4 model id"),
        Arg(("--endpoint",), "endpoint", target="init", default=endpoint,
            choices=["tokenhub", "local"],
            help="tokenhub = Tencent Cloud TokenHub; local = vLLM/SGLang OpenAI server"),
        Arg(("--base-url",), "base_url", target="init",
            help="Override TokenHub or HY4_BASE_URL"),
    ]


_QWEN_IMAGE_VERSIONS = [
    "qwen-image-3.0-pro",
    "qwen-image-3.0",
    "qwen-image-2.1-pro",
    "qwen-image-2.1-turbo",
    "qwen-image-2.0-pro",
    "qwen-image-2.0",
]

# Keep in sync with tryon.api.nano_banana adapter ratio tables (registry stays
# import-free, so this is a declared copy for CLI/MCP JSON Schema enums).
_GEMINI_ASPECT_RATIOS = [
    "1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9",
]
# Nano Banana 2.1 adds wide / panoramic ratios on top of the shared Gemini set.
_GEMINI_21_ASPECT_RATIOS = _GEMINI_ASPECT_RATIOS + ["1:4", "4:1", "1:8", "8:1"]
_LUMA_ASPECT_RATIOS = ["1:1", "3:4", "4:3", "9:16", "16:9", "9:21", "21:9"]
_IDEOGRAM_ASPECT_RATIOS = [
    "1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3", "10:16", "16:10", "1:3", "3:1",
]
# Keep in sync with tryon.api.vton.photoroom (registry stays import-free).
_PHOTOROOM_PRESETS = [
    "avery", "sam", "taylor", "kendall", "jordan", "casey", "maya", "reece",
    "lena", "julia", "jackson", "sophia", "emma", "ava", "zoe", "fiona",
]
_PHOTOROOM_SCENES = [
    "random", "street", "bedroom", "sunset", "factory", "studio",
    "coloredstudio", "concretestudio", "beach", "tropical", "library",
    "forest", "businessdistrict", "countryside", "flowers", "goldenlight",
    "mountain", "pool", "latincity", "cafe", "asiancity", "nightlights",
    "desert",
]
_PHOTOROOM_POSES = [
    "random", "standing", "34turn", "powerstance", "walkingforward",
    "handinpocket", "crossedarms", "back", "overtheshoulder", "seated",
    "adjustingclothing", "playfulspin",
]
_PHOTOROOM_SIZES = [
    "PORTRAIT_HD_16_9", "PORTRAIT_HD_4_3", "PORTRAIT_HD_3_2", "SQUARE_HD",
    "LANDSCAPE_HD_3_2", "LANDSCAPE_HD_4_3", "LANDSCAPE_HD_16_9",
]


def _gemini_aspect_ratio(wide: bool = False) -> Arg:
    return Arg(
        ("--aspect-ratio",), "aspect_ratio",
        choices=_GEMINI_21_ASPECT_RATIOS if wide else _GEMINI_ASPECT_RATIOS,
        help="Gemini-supported aspect ratio" + (" (2.1 adds 1:4, 4:1, 1:8, 8:1)" if wide else ""),
    )


_GPT_IMAGE_2_5_VERSIONS = [
    "gpt-image-2.5-flare",
    "gpt-image-2.5-sunburst",
    "gpt-image-2.5",
    "gpt-image-2.5-flare-2026-09-08",
    "gpt-image-2.5-sunburst-2026-09-08",
]
_GPT_IMAGE_2_5_QUALITY = ["low", "medium", "high", "xhigh", "max", "auto"]
_GPT_IMAGE_2_5_SIZES = ["1024x1024", "1536x1024", "1024x1536", "auto"]


def _gpt_image_25_generate_args(default_version: str) -> List[Arg]:
    return [
        Arg(("--prompt", "-p"), "prompt", required=True, help="Text prompt"),
        Arg(("--size",), "size", default="auto", choices=_GPT_IMAGE_2_5_SIZES),
        Arg(("--quality",), "quality", default="auto", choices=_GPT_IMAGE_2_5_QUALITY,
            help="2.5 adds xhigh and max on top of low/medium/high/auto"),
        Arg(("--background",), "background", default="auto"),
        Arg(("--n",), "n", type=int, default=1, help="Number of images"),
        Arg(
            ("--model-version",), "model_version", target="init",
            default=default_version, choices=_GPT_IMAGE_2_5_VERSIONS,
            help="OpenAI Images API id. Flare = everyday; Sunburst = precision edits. "
            "gpt-image-2.5 aliases to Flare.",
        ),
    ]


def _gpt_image_25_edit_args(default_version: str) -> List[Arg]:
    return [
        Arg(("--images",), "images", nargs="+", required=True,
            help="One or more input images (paths or URLs)"),
        Arg(("--prompt", "-p"), "prompt", help="Editing instruction"),
        Arg(("--mask",), "mask", help="Optional mask image"),
        Arg(("--size",), "size", default="auto", choices=_GPT_IMAGE_2_5_SIZES),
        Arg(("--quality",), "quality", default="auto", choices=_GPT_IMAGE_2_5_QUALITY,
            help="2.5 adds xhigh and max on top of low/medium/high/auto"),
        Arg(("--background",), "background", default="auto"),
        Arg(("--input-fidelity",), "input_fidelity", default="low", choices=["low", "high"]),
        Arg(("--n",), "n", type=int, default=1),
        Arg(
            ("--model-version",), "model_version", target="init",
            default=default_version, choices=_GPT_IMAGE_2_5_VERSIONS,
            help="OpenAI Images API id. Flare = everyday; Sunburst = precision edits. "
            "gpt-image-2.5 aliases to Flare.",
        ),
    ]


def _qwen_image_pinned_common_args(dashscope_model: str) -> List[Arg]:
    tail = _qwen_image_common_args()[1:]
    return [
        Arg(
            ("--model-version",),
            "model_version",
            target="init",
            call_name="model",
            default=dashscope_model,
            choices=[dashscope_model],
            help=f"DashScope model id (fixed: {dashscope_model})",
        ),
    ] + tail


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


def _muse_image_common_args() -> List[Arg]:
    return [
        Arg(("--n",), "n", type=int, default=1, help="Number of images 1-10"),
        Arg(
            ("--size",),
            "size",
            help='Aspect hint as WxH e.g. 1024x1536 (not exact pixels; omit for default)',
        ),
        Arg(
            ("--output-format",),
            "output_format",
            default="webp",
            choices=["webp", "png", "jpeg"],
        ),
        Arg(
            ("--reasoning-strength",),
            "reasoning_strength",
            default="high",
            choices=["high", "low"],
            help="high = self-refine (default); low = single pass",
        ),
        Arg(
            ("--no-image-search",),
            "enable_image_search",
            action="store_false",
            default=True,
            help="Disable built-in visual web search",
        ),
        Arg(
            ("--no-web-search",),
            "enable_web_search",
            action="store_false",
            default=True,
            help="Disable built-in factual web search",
        ),
        Arg(
            ("--no-shell",),
            "enable_shell",
            action="store_false",
            default=True,
            help="Disable built-in code/layout tool",
        ),
    ]


def _qwen_image_21_local_core_args(default_model_id: str) -> List[Arg]:
    return [
        Arg(("--width",), "width", type=int, help="Output width in pixels"),
        Arg(("--height",), "height", type=int, help="Output height in pixels"),
        Arg(
            ("--model-id",),
            "model_id",
            target="init",
            default=default_model_id,
            help=f"HF repo id or local path (default {default_model_id})",
        ),
        Arg(
            ("--no-kv-cache",),
            "use_kv_cache",
            action="store_false",
            default=True,
            help="Disable prefix KV cache reuse (Qwen-Image-2.1)",
        ),
        Arg(("--seed",), "seed", type=int),
        Arg(("--num-images",), "num_images", type=int, default=1),
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
    "google-vton": ModelSpec(
        id="google-vton",
        label="Google Virtual Try-On (Vertex virtual-try-on-001)",
        import_path="tryon.api.vton.google_vton",
        class_name="GoogleVTONAdapter",
        method="generate_and_decode",
        output_kind="images",
        env_hint="GOOGLE_CLOUD_PROJECT",
        notes=(
            "Dedicated Vertex / Gemini Enterprise try-on. Not Nano Banana and not "
            "GEMINI_API_KEY. Requires ADC (`gcloud auth application-default login` "
            "or GOOGLE_APPLICATION_CREDENTIALS). Optional GOOGLE_CLOUD_LOCATION "
            "(default global)."
        ),
        args=[
            _img(("--person-image", "--model-image"), "person", "Person/model image (path or URL)", required=True),
            _img(("--garment-image", "--cloth-image", "--product-image"), "garment",
                 "Garment/product image (path or URL)", required=True),
            Arg(("--project",), "project", target="init", help="GCP project id (default: GOOGLE_CLOUD_PROJECT)"),
            Arg(("--location",), "location", target="init", help="Vertex location (default: GOOGLE_CLOUD_LOCATION or global)"),
            Arg(("--num-images",), "number_of_images", type=int, default=1, help="Number of outputs 1-4"),
            Arg(("--seed",), "seed", type=int, help="Seed for reproducibility"),
            Arg(("--person-generation",), "person_generation", default="allow_adult",
                choices=["dont_allow", "allow_adult", "allow_all"],
                help="Person policy (shopper photos: allow_adult)"),
            Arg(("--safety-filter-level",), "safety_filter_level",
                choices=["block_low_and_above", "block_medium_and_above", "block_only_high", "block_none"],
                help="Vertex safety filter"),
            Arg(("--no-watermark",), "add_watermark", action="store_false", default=True,
                help="Disable SynthID / C2PA watermark (on by default)"),
            Arg(("--output-mime-type",), "output_mime_type", default="image/png",
                choices=["image/png", "image/jpeg"], help="Output MIME type"),
            Arg(("--output-gcs-uri",), "output_gcs_uri", help="Optional gs:// prefix to store outputs"),
        ],
    ),
    "outfitanyone-plus": ModelSpec(
        id="outfitanyone-plus",
        label="Alibaba OutfitAnyone-Plus (aitryon-plus)",
        import_path="tryon.api.vton.outfitanyone",
        class_name="OutfitAnyonePlusAdapter",
        method="generate_and_decode",
        output_kind="images",
        env_hint="DASHSCOPE_API_KEY",
        notes=(
            "Dedicated DashScope try-on (aitryon-plus). Beijing-region key only. "
            "Not Qwen-Image composition. Public HTTP(S) URLs, or local files "
            "uploaded to DashScope temp OSS. Optional --bottom-garment-image "
            "for top+bottoms combo. Dress/jumpsuit: garment only."
        ),
        args=[
            _img(("--person-image", "--model-image"), "person",
                 "Full-body front-facing person image (path or public URL)", required=True),
            _img(("--garment-image", "--cloth-image", "--top-garment-image"), "garment",
                 "Flat-lay top or dress (path or public URL)", required=False),
            _img(("--bottom-garment-image",), "bottom_garment",
                 "Optional flat-lay bottoms (path or public URL)"),
            Arg(("--no-restore-face",), "restore_face", action="store_false", default=True,
                help="Generate a random face (default: keep the original face)"),
            Arg(("--resolution",), "resolution", type=int, default=-1,
                choices=[-1, 1024, 1280],
                help="-1 match person; 1024 = 576x1024; 1280 = 720x1280"),
            Arg(("--base-url",), "base_url", target="init",
                help="DashScope /api/v1 host (default: China Beijing)"),
        ],
    ),
    "photoroom-vton": ModelSpec(
        id="photoroom-vton",
        label="Photoroom Virtual Try-On",
        import_path="tryon.api.vton.photoroom",
        class_name="PhotoroomVTONAdapter",
        method="generate_and_decode",
        output_kind="images",
        env_hint="PHOTOROOM_API_KEY",
        notes=(
            "Shopper photo + product photo via Image Editing API /v2/edit. "
            "Not Virtual Model (flat-lay → generated model). Prefix the key "
            "with sandbox_ for watermarked tests."
        ),
        args=[
            _img(("--person-image", "--model-image"), "person",
                 "Shopper / custom model photo (path or URL)", required=True),
            _img(("--garment-image", "--cloth-image", "--product-image"), "garment",
                 "Clothing product image (path or URL)", required=True),
            Arg(("--scene",), "scene", default="random",
                choices=list(_PHOTOROOM_SCENES), help="Preset scene (default random)"),
            Arg(("--pose",), "pose", default="standing",
                choices=list(_PHOTOROOM_POSES),
                help="Pose (docs recommend standing for try-on)"),
            Arg(("--size",), "size", default="PORTRAIT_HD_3_2",
                choices=list(_PHOTOROOM_SIZES), help="Output aspect / HD size"),
            Arg(("--prompt",), "prompt", help="Optional style hint, e.g. street style"),
            Arg(("--scene-image",), "scene_image", help="Optional custom scene image"),
            Arg(("--additional-product-images",), "additional_product_images", nargs="+",
                help="Extra angles of the same product"),
            Arg(("--remove-background",), "remove_background", action="store_true",
                help="Strip the generated scene (off by default)"),
            Arg(("--mode",), "mode", default="try-on", choices=["try-on"],
                help="Fixed: shopper Virtual Try-On"),
        ],
    ),
    "photoroom-virtual-model": ModelSpec(
        id="photoroom-virtual-model",
        label="Photoroom Virtual Model",
        import_path="tryon.api.vton.photoroom",
        class_name="PhotoroomVTONAdapter",
        method="generate_virtual_model",
        output_kind="images",
        env_hint="PHOTOROOM_API_KEY",
        notes=(
            "Flat-lay / product photo → on-model catalog shot. No shopper "
            "photo required. Optional --person-image uses a custom model "
            "instead of --preset-model (default avery)."
        ),
        args=[
            _img(("--garment-image", "--cloth-image", "--product-image"), "garment",
                 "Product / flat-lay image (path or URL)", required=True),
            _img(("--person-image", "--model-image"), "person",
                 "Optional custom model photo (overrides --preset-model)"),
            Arg(("--preset-model",), "preset_model", default="avery",
                choices=list(_PHOTOROOM_PRESETS),
                help="Photoroom preset model when no custom person is passed"),
            Arg(("--scene",), "scene", default="random",
                choices=list(_PHOTOROOM_SCENES), help="Preset scene"),
            Arg(("--pose",), "pose", default="standing",
                choices=list(_PHOTOROOM_POSES), help="Pose"),
            Arg(("--size",), "size", default="PORTRAIT_HD_3_2",
                choices=list(_PHOTOROOM_SIZES), help="Output aspect / HD size"),
            Arg(("--prompt",), "prompt", help="Optional style hint, e.g. street style"),
            Arg(("--scene-image",), "scene_image", help="Optional custom scene image"),
            Arg(("--additional-product-images",), "additional_product_images", nargs="+",
                help="Extra angles of the same product"),
            Arg(("--remove-background",), "remove_background", action="store_true",
                help="Strip the generated scene (off by default)"),
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
    "qwen-image-2.1-pro": ModelSpec(
        id="qwen-image-2.1-pro",
        label="Qwen-Image-2.1 Pro (DashScope)",
        import_path="tryon.api.qwen",
        class_name="QwenImageAdapter",
        method="generate_virtual_tryon",
        output_kind="images",
        env_hint="DASHSCOPE_API_KEY",
        notes="DashScope qwen-image-2.1-pro: up to 10 reference images on edit/VTON; thinking + prompt rewrite.",
        args=[
            _img(("--person-image", "--model-image"), "person", "Person/model image (path or URL)", required=True),
            _img(("--garment-image", "--cloth-image"), "garment", "Garment reference image (path or URL)", required=True),
            Arg(("--prompt",), "prompt", "Full styling prompt (overrides --garment-description)"),
            Arg(("--garment-description",), "garment_description",
                help="Short garment description used to build the default prompt"),
            *_qwen_image_pinned_common_args("qwen-image-2.1-pro"),
        ],
    ),
    "qwen-image-2.1-turbo": ModelSpec(
        id="qwen-image-2.1-turbo",
        label="Qwen-Image-2.1 Turbo (DashScope)",
        import_path="tryon.api.qwen",
        class_name="QwenImageAdapter",
        method="generate_virtual_tryon",
        output_kind="images",
        env_hint="DASHSCOPE_API_KEY",
        notes="DashScope qwen-image-2.1-turbo hosted API (fast tier). Open weights: --model qwen-image-2.1-turbo-local.",
        args=[
            _img(("--person-image", "--model-image"), "person", "Person/model image (path or URL)", required=True),
            _img(("--garment-image", "--cloth-image"), "garment", "Garment reference image (path or URL)", required=True),
            Arg(("--prompt",), "prompt", "Full styling prompt (overrides --garment-description)"),
            Arg(("--garment-description",), "garment_description",
                help="Short garment description used to build the default prompt"),
            *_qwen_image_pinned_common_args("qwen-image-2.1-turbo"),
        ],
    ),
    "qwen-image-2.1-local": ModelSpec(
        id="qwen-image-2.1-local",
        label="Qwen-Image-2.1 (open-weight, local)",
        import_path="tryon.models.qwen_image_21",
        class_name="QwenImage21LocalAdapter",
        method="generate_virtual_tryon",
        output_kind="images",
        extra="local",
        notes="HF Qwen/Qwen-Image-2.1 (Diffusers QwenImage21Pipeline). Hosted twin: qwen-image-2.1-pro.",
        args=[
            _img(("--person-image", "--model-image"), "person", "Person/model image (path or URL)", required=True),
            _img(("--garment-image", "--cloth-image"), "garment", "Garment reference image (path or URL)", required=True),
            Arg(("--prompt",), "prompt", "Full styling prompt (overrides --garment-description)"),
            Arg(("--garment-description",), "garment_description",
                help="Short garment description used to build the default prompt"),
            *_qwen_image_21_local_core_args("Qwen/Qwen-Image-2.1"),
        ],
    ),
    "qwen-image-2.1-turbo-local": ModelSpec(
        id="qwen-image-2.1-turbo-local",
        label="Qwen-Image-2.1 Turbo (open-weight, local 8-step)",
        import_path="tryon.models.qwen_image_21",
        class_name="QwenImage21LocalAdapter",
        method="generate_virtual_tryon",
        output_kind="images",
        extra="local",
        notes="HF Qwen/Qwen-Image-2.1-Turbo. Hosted twin: qwen-image-2.1-turbo.",
        args=[
            _img(("--person-image", "--model-image"), "person", "Person/model image (path or URL)", required=True),
            _img(("--garment-image", "--cloth-image"), "garment", "Garment reference image (path or URL)", required=True),
            Arg(("--prompt",), "prompt", "Full styling prompt (overrides --garment-description)"),
            Arg(("--garment-description",), "garment_description",
                help="Short garment description used to build the default prompt"),
            *_qwen_image_21_local_core_args("Qwen/Qwen-Image-2.1-Turbo"),
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
    "fashn-vton-1.5": ModelSpec(
        id="fashn-vton-1.5",
        label="FASHN VTON v1.5 (open-weight local VTON, Apache-2.0)",
        import_path="tryon.models.fashn_vton",
        class_name="FashnVTONLocalAdapter",
        method="generate_and_decode",
        output_kind="images",
        extra="local",
        notes=(
            "Maskless pixel-space try-on (972M; Apache-2.0 code + weights, the commercial-friendly local "
            "option vs Leffa/CatVTON). Garment may be worn on a model or a flat-lay. ~2GB weights "
            "auto-download to ~/.cache/opentryon/fashn-vton-1.5 (override FASHN_VTON_WEIGHTS_DIR). Needs "
            "pip install opentryon[local] plus: pip install 'git+https://github.com/fashn-AI/fashn-vton-1.5.git' "
            "(pulls onnxruntime-gpu; CPU-only: swap to onnxruntime). bf16 on Ampere+ GPUs. Hosted twin: "
            "--model fashn-tryon-max / fashn-tryon-v1.6 (FASHN_API_KEY). fashn-human-parser has its own "
            "licence -- review before commercial use."
        ),
        args=[
            _img(("--person-image", "--model-image"), "person", "Person/model image (path or URL)", required=True),
            _img(("--garment-image", "--cloth-image"), "garment", "Garment image: worn on a model or flat-lay (path or URL)", required=True),
            Arg(("--category",), "category", default="tops", choices=["tops", "bottoms", "one-pieces"],
                help="tops (shirts, jackets), bottoms (pants, skirts), one-pieces (dresses, jumpsuits)"),
            Arg(("--garment-photo-type",), "garment_photo_type", default="model", choices=["model", "flat-lay"],
                help="'model' if the garment is worn by someone, 'flat-lay' for product shots"),
            Arg(("--num-samples",), "num_samples", type=int, default=1, choices=[1, 2, 3, 4],
                help="Number of output images"),
            Arg(("--steps",), "num_timesteps", type=int, default=30,
                help="Diffusion steps: 20 fast, 30 balanced, 50 quality"),
            Arg(("--guidance-scale",), "guidance_scale", type=float, default=1.5,
                help="Classifier-free guidance strength"),
            Arg(("--seed",), "seed", type=int, default=42),
            Arg(("--no-segmentation-free",), "segmentation_free", action="store_false", default=True,
                help="Disable segmentation-free mode (default preserves body features / garment volume)"),
            Arg(("--weights-dir",), "weights_dir", target="init",
                help="Directory with model.safetensors + dwpose/ (default FASHN_VTON_WEIGHTS_DIR or the cache dir)"),
            Arg(("--device",), "device", target="init", help="Device override (cuda/cpu)"),
        ],
    ),
    "klein-4b-tryon": ModelSpec(
        id="klein-4b-tryon",
        label="FLUX.2-klein-4B try-on LoRA (xocialize, local, Apache-2.0 stack)",
        import_path="tryon.models.klein_tryon",
        class_name="Klein4BTryOnAdapter",
        method="generate_and_decode",
        output_kind="images",
        extra="local",
        notes=(
            "Community rank-32 LoRA (xocialize/tryon-FLUX.2-klein-4B-lora) on FLUX.2-klein-4B; both Apache-2.0, "
            "unlike the klein-9B try-on LoRAs (9B base is non-commercial). Inputs are ordered person, top, bottom "
            "(--dress-image fills both slots). The person image must be CLOTHING-AGNOSTIC (outfit area greyed): pass "
            "--mask-image (white = clothing region) and it is greyed here; this adapter does not segment. v1 LoRA "
            "trained on 273 tuples, no metrics; weakest on all-dark outfits. Defaults are BFL's klein-4B settings "
            "(4 steps, guidance 1.0) -- the card gives none, so tune. Needs CUDA (~13GB+), diffusers from GitHub "
            "(Flux2KleinPipeline) and peft: pip install git+https://github.com/huggingface/diffusers.git peft accelerate."
        ),
        args=[
            _img(("--person-image", "--model-image"), "person", "Full-body person photo, clothing-agnostic (or use --mask-image)", required=True),
            Arg(("--top-image",), "top", help="Isolated upper-body garment"),
            Arg(("--bottom-image",), "bottom", help="Isolated lower-body garment"),
            Arg(("--dress-image",), "dress", help="One-piece garment (used for both top and bottom slots)"),
            Arg(("--mask-image",), "mask", help="Clothing-region mask (white = replace); greyed out of the person image"),
            Arg(("--prompt", "-p"), "prompt", help="Defaults to the LoRA trigger prompt (must start with TRYON)"),
            Arg(("--steps",), "num_inference_steps", type=int, default=4, help="Denoising steps (klein-4B default 4)"),
            Arg(("--guidance-scale",), "guidance_scale", type=float, default=1.0),
            Arg(("--height",), "height", type=int, help="Output height (default: person size, long side <= 1024, multiple of 16)"),
            Arg(("--width",), "width", type=int, help="Output width"),
            Arg(("--seed",), "seed", type=int),
            Arg(("--num-images",), "num_images", type=int, default=1),
            Arg(("--lora-id",), "lora_id", target="init", help="LoRA repo id or path (default xocialize/tryon-FLUX.2-klein-4B-lora)"),
            Arg(("--base-model-id",), "base_model_id", target="init", help="Base model (default black-forest-labs/FLUX.2-klein-4B)"),
            Arg(("--dtype",), "dtype", target="init", default="bfloat16", choices=["bfloat16", "float16", "float32"]),
            Arg(("--no-cpu-offload",), "cpu_offload", target="init", action="store_false", default=True,
                help="Disable CPU offload (needs ~13GB+ VRAM)"),
        ],
    ),
    "leffa": ModelSpec(
        id="leffa",
        label="Leffa (open-weight local VTON, CVPR 2025)",
        import_path="tryon.models.leffa",
        class_name="LeffaAdapter",
        method="generate_and_decode",
        output_kind="images",
        extra="local",
        notes=(
            "Local GPU try-on (MIT code; confirm HF weight card for commercial D2C). "
            "Weights franciszzj/Leffa. Optional LEFFA_HOME clone + LEFFA_CKPT snapshot. "
            "Needs pip install opentryon[local]. Pass --mask-image for best results."
        ),
        args=[
            _img(("--person-image", "--model-image"), "person", "Person/model image (path or URL)", required=True),
            _img(("--garment-image", "--cloth-image"), "garment", "Garment reference image (path or URL)", required=True),
            _img(("--mask-image",), "mask", "Optional agnostic clothing mask (white = replace)"),
            _img(("--densepose-image",), "densepose", "Optional DensePose control image"),
            Arg(("--garment-type",), "garment_type", default="upper_body",
                choices=["upper_body", "lower_body", "dresses"],
                help="Used when auto-masking / geometric mask fallback"),
            Arg(("--vt-model-type",), "vt_model_type", default="viton_hd",
                choices=["viton_hd", "dress_code"],
                help="VITON-HD (recommended) or DressCode checkpoint"),
            Arg(("--steps",), "num_inference_steps", type=int, default=30, help="Denoising steps"),
            Arg(("--guidance-scale",), "guidance_scale", type=float, default=2.5),
            Arg(("--seed",), "seed", type=int, default=42),
            Arg(("--ref-acceleration",), "ref_acceleration", action="store_true",
                help="Faster reference UNet (may slightly reduce quality)"),
            Arg(("--repaint",), "repaint", action="store_true"),
            Arg(("--control-type",), "control_type", default="virtual_tryon",
                choices=["virtual_tryon", "pose_transfer"]),
            Arg(("--ckpt-dir",), "ckpt_dir", target="init", help="Local HF snapshot (default LEFFA_CKPT)"),
            Arg(("--src-dir",), "src_dir", target="init",
                help="Clone of franciszzj/Leffa (default LEFFA_HOME / auto-download)"),
            Arg(("--dtype",), "dtype", target="init", default="float16",
                choices=["float16", "bfloat16", "float32"]),
        ],
    ),
    "catvton": ModelSpec(
        id="catvton",
        label="CatVTON (open-weight local VTON, ICLR 2025)",
        import_path="tryon.models.catvton",
        class_name="CatVTONAdapter",
        method="generate_and_decode",
        output_kind="images",
        extra="local",
        notes=(
            "Local GPU concatenation try-on (<8GB @ 1024x768). "
            "CC BY-NC-SA 4.0 — not for commercial D2C. Weights zhengchong/CatVTON. "
            "Needs pip install opentryon[local]. Pass --mask-image for best results."
        ),
        args=[
            _img(("--person-image", "--model-image"), "person", "Person/model image (path or URL)", required=True),
            _img(("--garment-image", "--cloth-image"), "garment", "Garment reference image (path or URL)", required=True),
            _img(("--mask-image",), "mask", "Optional agnostic clothing mask (white = replace)"),
            Arg(("--garment-type",), "garment_type", default="upper_body",
                choices=["upper_body", "lower_body", "dresses"],
                help="Geometric mask fallback when --mask-image is omitted"),
            Arg(("--attn-version",), "attn_version", target="init", default="mix",
                choices=["mix", "vitonhd", "dresscode"],
                help="Attention checkpoint: mix-48k-1024 (default), vitonhd, dresscode"),
            Arg(("--steps",), "num_inference_steps", type=int, default=50, help="Denoising steps"),
            Arg(("--guidance-scale",), "guidance_scale", type=float, default=2.5),
            Arg(("--height",), "height", type=int, default=1024),
            Arg(("--width",), "width", type=int, default=768),
            Arg(("--seed",), "seed", type=int),
            Arg(("--repaint",), "repaint", action="store_true",
                help="Composite the result back onto the original background"),
            Arg(("--attn-ckpt",), "attn_ckpt", target="init",
                help="HF repo or local snapshot (default zhengchong/CatVTON)"),
            Arg(("--base-ckpt",), "base_ckpt", target="init",
                help="SD 1.5 inpainting repo (or CATVTON_BASE_MODEL)"),
            Arg(("--dtype",), "dtype", target="init", default="float16",
                choices=["float16", "bfloat16", "float32"]),
        ],
    ),
    "muse-image": ModelSpec(
        id="muse-image",
        label="Muse Image (Meta Model API, composition try-on)",
        import_path="tryon.api.muse",
        class_name="MuseImageAdapter",
        method="generate_virtual_tryon",
        output_kind="images",
        env_hint="MODEL_API_KEY",
        notes=(
            "Person + garment composition via Muse Image multi-ref edit. "
            "Not a dedicated garment-fit model. Same MODEL_API_KEY as generate/edit --model muse-image. "
            "Muse Video has no API yet."
        ),
        args=[
            _img(("--person-image", "--model-image"), "person", "Person/model image (path or URL)", required=True),
            _img(("--garment-image", "--cloth-image"), "garment", "Garment reference image (path or URL)", required=True),
            Arg(("--prompt",), "prompt", "Full styling prompt (overrides --garment-description)"),
            Arg(("--garment-description",), "garment_description",
                help="Short garment description used to build the default prompt"),
            *_muse_image_common_args(),
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


def _fashn_common_args(modes: bool = True, n: bool = True, fmt: str = "png") -> List[Arg]:
    """Shared FASHN image-endpoint flags (resolution tier, quality mode, seed, count, format)."""
    args = [Arg(("--resolution",), "resolution", choices=["1k", "2k", "4k"], help="Output tier (~1/4/16 MP); default 1k")]
    if modes:
        args.append(Arg(("--generation-mode",), "generation_mode", choices=["fast", "balanced", "quality"],
                        help="Quality tier; credits = mode x resolution (1..5). Omit for FASHN's automatic pick"))
    args.append(Arg(("--seed",), "seed", type=int, help="Seed (default 42 server-side)"))
    if n:
        args.append(Arg(("--num-images",), "num_images", type=int, choices=[1, 2, 3, 4], help="Images per request (multiplies credits)"))
    args.append(Arg(("--output-format",), "output_format", default=fmt, choices=["png", "jpeg"]))
    return args


_FASHN_FACE_ARGS = [
    Arg(("--face-reference",), "face_reference", help="Identity reference portrait (+3 credits, ~+20s)"),
    Arg(("--face-reference-mode",), "face_reference_mode", choices=["match_base", "match_reference"],
        help="match_reference follows the reference face's pose/expression; match_base keeps the base"),
]

_FASHN_NOTE = ("FASHN catalogue endpoint over the universal /v1/run API (same FASHN_API_KEY as "
               "fashn-tryon-max). ")


def _nano_banana_generate_args(
    with_resolution: bool,
    with_grounding: bool,
    wide: bool = False,
    *,
    with_video_to_image: bool = False,
) -> List[Arg]:
    args = [
        Arg(("--prompt", "-p"), "prompt", required=True, help="Text prompt"),
        _gemini_aspect_ratio(wide),
    ]
    if with_video_to_image:
        args.insert(
            0,
            Arg(
                ("--video",),
                "video",
                help="Video-to-image: local path, URL, or YouTube link (Interactions API; Nano Banana 2 / 2.1 / 2 Lite only)",
            ),
        )
    if with_resolution:
        args.append(Arg(("--resolution",), "resolution", default="2K", choices=["1K", "2K", "4K"]))
    if with_grounding:
        args.append(Arg(("--use-search-grounding",), "use_search_grounding", action="store_true", help="Ground with Google Search"))
    return args


def _flux3_image_args(*, for_edit: bool) -> List[Arg]:
    aspect_choices = [
        "auto",
        "21:9",
        "2:1",
        "16:9",
        "3:2",
        "7:5",
        "4:3",
        "5:4",
        "1:1",
        "4:5",
        "3:4",
        "5:7",
        "2:3",
        "9:16",
        "1:2",
        "9:21",
    ]
    args: List[Arg] = []
    if for_edit:
        args.append(
            _img(("--image", "-i"), "input_image", "Primary reference image (path or URL)", required=True)
        )
        args.append(
            Arg(
                ("--reference-images",),
                "reference_images",
                nargs="+",
                help="Additional reference images (up to 9 more; 10 total with --image)",
            )
        )
    args.extend(
        [
            Arg(("--prompt", "-p"), "prompt", required=True, help="Text prompt"),
            Arg(("--aspect-ratio",), "aspect_ratio", default="auto", choices=aspect_choices),
            Arg(
                ("--resolution",),
                "resolution",
                default="1k",
                choices=["768sq", "1k", "1.5k", "2k", "4k"],
            ),
            Arg(
                ("--safety-tolerance",),
                "safety_tolerance",
                type=int,
                default=2,
                choices=list(range(5)),
            ),
            Arg(
                ("--no-grounding",),
                "grounding",
                action="store_false",
                default=True,
                help="Disable web and image search grounding before generation",
            ),
        ]
    )
    return args


def _flux3_image_klein_args(*, for_edit: bool) -> List[Arg]:
    args = _flux3_image_args(for_edit=for_edit)
    args = [a for a in args if a.dest != "grounding"]
    for i, arg in enumerate(args):
        if arg.dest == "safety_tolerance":
            args[i] = Arg(
                ("--safety-tolerance",),
                "safety_tolerance",
                type=int,
                default=2,
                choices=list(range(8)),
            )
            break
    args.extend(
        [
            Arg(("--seed",), "seed", type=int, help="Reproducibility seed (0–4294967295)"),
            Arg(("--steps",), "steps", type=int, help="Denoising steps (1–16, default 16)"),
            Arg(("--width",), "width", type=int, help="Exact output width (with --height)"),
            Arg(("--height",), "height", type=int, help="Exact output height (with --width)"),
            Arg(
                ("--output-format",),
                "output_format",
                default="jpeg",
                choices=["jpeg", "png"],
            ),
        ]
    )
    return args


def _flux3_image_klein_local_args(*, for_edit: bool) -> List[Arg]:
    args: List[Arg] = []
    if for_edit:
        args.append(
            _img(("--image", "-i"), "input_image", "Primary reference image (path or URL)", required=True)
        )
        args.append(
            Arg(
                ("--reference-images",),
                "reference_images",
                nargs="+",
                help="Additional references (multi-ref edits; use <ref_image_N> in prompt)",
            )
        )
    args.extend(
        [
            Arg(("--prompt", "-p"), "prompt", required=True, help="Text prompt"),
            Arg(("--width",), "width", type=int, default=1024 if not for_edit else None),
            Arg(("--height",), "height", type=int, default=1024 if not for_edit else None),
            Arg(
                ("--steps",),
                "num_inference_steps",
                type=int,
                help="Denoising steps (default 16 distilled / 50 base)",
            ),
            Arg(("--seed",), "seed", type=int),
            Arg(
                ("--model-id",),
                "model_id",
                target="init",
                default="black-forest-labs/flux-3-image-klein",
                help="HF repo: flux-3-image-klein (distilled) or flux-3-image-klein-base",
            ),
            Arg(
                ("--guidance-scale",),
                "guidance_scale",
                target="init",
                type=float,
                help="CFG for klein-base only (default 3.5); ignored for distilled checkpoint",
            ),
            Arg(
                ("--device",),
                "device",
                target="init",
                choices=["cuda", "mps", "cpu"],
            ),
        ]
    )
    return args


def _flux3_video_args() -> List[Arg]:
    aspect_choices = [
        "auto",
        "21:9",
        "2:1",
        "16:9",
        "4:3",
        "1:1",
        "3:4",
        "9:16",
        "9:21",
    ]
    return [
        Arg(
            ("--prompt", "-p"),
            "prompt",
            help="Text prompt (required for t2v/i2v/v2v; omit when using --draft-cache only)",
        ),
        Arg(
            ("--image",),
            "image",
            help="Optional opening frame (switches to image-to-video)",
            alt_only=True,
        ),
        Arg(
            ("--end-image",),
            "end_image",
            help="Optional closing frame (image-to-video only)",
            alt_only=True,
        ),
        Arg(
            ("--video",),
            "video",
            help="Existing clip to continue from (video continuation / v2v)",
        ),
        Arg(
            ("--draft-cache",),
            "draft_cache",
            help="Draft bundle from a prior --draft run (full-quality draft_enhance)",
        ),
        Arg(("--aspect-ratio",), "aspect_ratio", default="auto", choices=aspect_choices),
        Arg(
            ("--duration",),
            "duration",
            default="auto",
            help='Seconds 5–20, or "auto" (v2v max 15)',
        ),
        Arg(
            ("--resolution",),
            "resolution",
            default="hd",
            choices=["hd", "fhd", "qhd", "uhd"],
        ),
        Arg(
            ("--safety-tolerance",),
            "safety_tolerance",
            type=int,
            default=2,
            choices=list(range(8)),
        ),
        Arg(
            ("--draft",),
            "draft",
            action="store_true",
            help="Fast hd preview; result includes draft_cache URL for a later enhance pass",
        ),
        Arg(
            ("--no-audio",),
            "generate_audio",
            action="store_false",
            default=True,
            help="Disable synchronized audio",
        ),
        Arg(
            ("--version",),
            "version",
            default="latest",
            choices=["latest", "max"],
            help="BFL harness version pin (flux3-video default latest; flux3-max pins max)",
        ),
    ]


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
        alt_method_on_video="generate_video_to_image",
        args=_nano_banana_generate_args(with_resolution=True, with_grounding=True, with_video_to_image=True),
    ),
    "nano-banana-2.1": ModelSpec(
        id="nano-banana-2.1", label="Nano Banana 2.1 (gemini-nano-banana-2.1)",
        import_path="tryon.api.nano_banana", class_name="NanoBanana21Adapter",
        method="generate_text_to_image", output_kind="images", env_hint="GEMINI_API_KEY",
        notes="GA 2026-10-06; successor to nano-banana-2 (gemini-3.1-flash-image is deprecated, no shutdown "
        "date yet). Better quality, text rendering and multi-turn character consistency at Flash speed/cost; "
        "1K/2K/4K plus wide ratios 1:4, 4:1, 1:8, 8:1. Pass --video for video-to-image (poster/thumbnail). "
        "Same GEMINI_API_KEY.",
        alt_method_on_video="generate_video_to_image",
        args=_nano_banana_generate_args(
            with_resolution=True, with_grounding=True, wide=True, with_video_to_image=True
        ),
    ),
    "nano-banana-2-lite": ModelSpec(
        id="nano-banana-2-lite", label="Nano Banana 2 Lite (Gemini 3.1 Flash-Lite Image)",
        import_path="tryon.api.nano_banana", class_name="NanoBanana2LiteAdapter",
        method="generate_text_to_image", output_kind="images", env_hint="GEMINI_API_KEY",
        notes="Fastest/cheapest Nano Banana tier; 1K resolution only. Pass --video for video-to-image.",
        alt_method_on_video="generate_video_to_image",
        args=_nano_banana_generate_args(with_resolution=False, with_grounding=False, with_video_to_image=True),
    ),
    "flux3-image": ModelSpec(
        id="flux3-image",
        label="FLUX 3 Image",
        import_path="tryon.api.flux3",
        class_name="Flux3ImageAdapter",
        method="generate_text_to_image",
        output_kind="images",
        env_hint="BFL_API_KEY",
        notes="BFL unified generate/edit endpoint; resolution tiers up to 4k; optional grounding.",
        args=_flux3_image_args(for_edit=False),
    ),
    "flux3-image-klein": ModelSpec(
        id="flux3-image-klein",
        label="FLUX 3 Image Klein",
        import_path="tryon.api.flux3",
        class_name="Flux3ImageKleinAdapter",
        method="generate_text_to_image",
        output_kind="images",
        env_hint="BFL_API_KEY",
        notes=(
            "Distilled Klein sibling on POST /v1/flux-3-image-klein — faster, same edit/multi-ref "
            "contract; optional seed/steps; no grounding."
        ),
        args=_flux3_image_klein_args(for_edit=False),
    ),
    "flux3-image-klein-local": ModelSpec(
        id="flux3-image-klein-local",
        label="FLUX 3 Image Klein (local Diffusers)",
        import_path="tryon.models.flux3_image_klein",
        class_name="Flux3ImageKleinLocalAdapter",
        method="generate_text_to_image",
        output_kind="images",
        extra="local",
        notes=(
            "Open FLUX.3 Klein via ModularPipeline (default black-forest-labs/flux-3-image-klein). "
            "RTX 3090+ class GPU recommended; needs pip install -U diffusers transformers. "
            "Hosted twin: flux3-image (BFL_API_KEY)."
        ),
        args=_flux3_image_klein_local_args(for_edit=False),
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
    "sana-sprint": ModelSpec(
        id="sana-sprint",
        label="SANA-Sprint 1.6B (local ultra-fast T2I, 1–4 steps)",
        import_path="tryon.models.sana_sprint",
        class_name="SanaSprintAdapter",
        method="generate_text_to_image",
        output_kind="images",
        extra="local",
        notes=(
            "NVLabs/MIT HAN 1–4 step distilled T2I at 1024px. Needs diffusers from GitHub "
            "(SanaSprintPipeline), not the older opentryon[local] pin alone. "
            "Apache-2.0 weights on Hugging Face."
        ),
        args=[
            Arg(("--prompt", "-p"), "prompt", required=True, help="Text prompt"),
            Arg(("--width",), "width", type=int, default=1024),
            Arg(("--height",), "height", type=int, default=1024),
            Arg(("--steps",), "num_inference_steps", type=int, default=2, help="1–4 steps"),
            Arg(("--guidance-scale",), "guidance_scale", type=float, default=4.5),
            Arg(("--seed",), "seed", type=int),
            Arg(("--model-id",), "model_id", target="init", help="HF repo or local diffusers folder"),
            Arg(("--device",), "device", target="init", choices=["cuda", "mps", "cpu"]),
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
    "gpt-image-2.5": ModelSpec(
        id="gpt-image-2.5",
        label="ChatGPT Images 2.5 Flare (OpenAI)",
        import_path="tryon.api.openAI.image_adapter",
        class_name="GPTImageAdapter",
        method="generate_text_to_image",
        output_kind="image_bytes",
        env_hint="OPENAI_API_KEY",
        notes=(
            "ChatGPT Images 2.5 Flare (everyday). Same OPENAI_API_KEY as --model gpt-image. "
            "Official API id gpt-image-2.5-flare; --model-version can pin Sunburst or dated snapshots. "
            "CLI --model gpt-image stays on 1.5."
        ),
        args=_gpt_image_25_generate_args("gpt-image-2.5-flare"),
    ),
    "gpt-image-2.5-sunburst": ModelSpec(
        id="gpt-image-2.5-sunburst",
        label="ChatGPT Images 2.5 Sunburst (OpenAI)",
        import_path="tryon.api.openAI.image_adapter",
        class_name="GPTImageAdapter",
        method="generate_text_to_image",
        output_kind="image_bytes",
        env_hint="OPENAI_API_KEY",
        notes=(
            "ChatGPT Images 2.5 Sunburst (precision edits). Same OPENAI_API_KEY as --model gpt-image. "
            "Everyday gen: --model gpt-image-2.5 (Flare)."
        ),
        args=_gpt_image_25_generate_args("gpt-image-2.5-sunburst"),
    ),
    "muse-image": ModelSpec(
        id="muse-image",
        label="Muse Image (Meta Model API)",
        import_path="tryon.api.muse",
        class_name="MuseImageAdapter",
        method="generate_text_to_image",
        output_kind="images",
        env_hint="MODEL_API_KEY",
        notes=(
            "First-party Meta Muse Image (muse-image-1.0). Agentic search/code on by default. "
            "No open weights. Muse Video has no developer API yet."
        ),
        args=[
            Arg(("--prompt", "-p"), "prompt", required=True, help="Text prompt"),
            *_muse_image_common_args(),
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
    "qwen-image-2.1-pro": ModelSpec(
        id="qwen-image-2.1-pro", label="Qwen-Image-2.1 Pro (DashScope)",
        import_path="tryon.api.qwen", class_name="QwenImageAdapter",
        method="generate_text_to_image", output_kind="images", env_hint="DASHSCOPE_API_KEY",
        notes="Alibaba Model Studio qwen-image-2.1-pro (T2I + edit up to 10 refs).",
        args=[
            Arg(("--prompt", "-p"), "prompt", required=True, help="Text prompt"),
            *_qwen_image_pinned_common_args("qwen-image-2.1-pro"),
        ],
    ),
    "qwen-image-2.1-turbo": ModelSpec(
        id="qwen-image-2.1-turbo", label="Qwen-Image-2.1 Turbo (DashScope)",
        import_path="tryon.api.qwen", class_name="QwenImageAdapter",
        method="generate_text_to_image", output_kind="images", env_hint="DASHSCOPE_API_KEY",
        notes="Hosted qwen-image-2.1-turbo. Local open weights: qwen-image-2.1-turbo-local.",
        args=[
            Arg(("--prompt", "-p"), "prompt", required=True, help="Text prompt"),
            *_qwen_image_pinned_common_args("qwen-image-2.1-turbo"),
        ],
    ),
    "qwen-image-2.1-local": ModelSpec(
        id="qwen-image-2.1-local", label="Qwen-Image-2.1 (open-weight, local T2I)",
        import_path="tryon.models.qwen_image_21", class_name="QwenImage21LocalAdapter",
        method="generate_text_to_image", output_kind="images", extra="local",
        notes="HF Qwen/Qwen-Image-2.1 via QwenImage21Pipeline. Hosted twin: qwen-image-2.1-pro.",
        args=[
            Arg(("--prompt", "-p"), "prompt", required=True, help="Text prompt"),
            *_qwen_image_21_local_core_args("Qwen/Qwen-Image-2.1"),
        ],
    ),
    "qwen-image-2.1-turbo-local": ModelSpec(
        id="qwen-image-2.1-turbo-local", label="Qwen-Image-2.1 Turbo (local 8-step)",
        import_path="tryon.models.qwen_image_21", class_name="QwenImage21LocalAdapter",
        method="generate_text_to_image", output_kind="images", extra="local",
        notes="HF Qwen/Qwen-Image-2.1-Turbo. Hosted twin: qwen-image-2.1-turbo.",
        args=[
            Arg(("--prompt", "-p"), "prompt", required=True, help="Text prompt"),
            *_qwen_image_21_local_core_args("Qwen/Qwen-Image-2.1-Turbo"),
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
    "p-image-ideogram": ModelSpec(
        id="p-image-ideogram", label="P-Image-Ideogram (Pruna × Ideogram)",
        import_path="tryon.api.pruna", class_name="PImageIdeogramAdapter",
        method="generate_text_to_image", output_kind="images", env_hint="PRUNA_API_KEY",
        notes="Pruna predictions Model: p-image-ideogram. Thinking very low–very high "
        "(default high). Use 2K + high/very high for typography. Prompt upsampling on by default.",
        args=[
            Arg(("--prompt", "-p"), "prompt", required=True,
                help="Natural language or Ideogram 4.0 JSON prompt"),
            Arg(("--thinking",), "thinking", default="high",
                choices=["very-low", "low", "medium", "high", "very-high"],
                help="Quality / cost / latency (Pruna: very low–very high). Default high. Pair high or very-high with 2K for text."),
            Arg(("--image-size",), "image_size", default="1K", choices=["1K", "2K"],
                help="Resolution budget (ignored when --aspect-ratio custom)"),
            Arg(("--aspect-ratio",), "aspect_ratio", default="1:1",
                choices=["1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3", "custom"]),
            Arg(("--width",), "width", type=int,
                help="Custom width (multiple of 16, max 2560); requires --aspect-ratio custom"),
            Arg(("--height",), "height", type=int,
                help="Custom height (multiple of 16, max 2560); requires --aspect-ratio custom"),
            Arg(("--seed",), "seed", type=int),
            Arg(("--no-prompt-upsampling",), "prompt_upsampling", action="store_false",
                default=True, help="Pass the raw prompt (needed for exact on-image text / JSON specs)"),
            Arg(("--output-format",), "output_format", default="jpg",
                choices=["jpg", "png", "webp"]),
            Arg(("--output-quality",), "output_quality", type=int,
                help="JPEG/WebP quality 0–100 (default 80)"),
        ],
    ),
    "fashn-model-create": ModelSpec(
        id="fashn-model-create", label="FASHN Model Create (fashion model from a prompt)",
        import_path="tryon.api.fashn", class_name="FashnAdapter",
        method="generate_model_create", output_kind="images", env_hint="FASHN_API_KEY",
        notes=_FASHN_NOTE + "Experimental lifecycle. Prompt (+ optional pose/composition reference) -> a new "
        "fashion model photo; --face-reference keeps one identity across generations (capped at 2K).",
        args=[
            Arg(("--prompt", "-p"), "prompt", required=True, help="Model, outfit, pose and scene description"),
            Arg(("--image-reference",), "image_reference", help="Optional composition/pose inspiration (not copied exactly)"),
            Arg(("--aspect-ratio",), "aspect_ratio",
                choices=["21:9", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3", "4:5", "5:4", "1:1"], help="Default 1:1"),
            *_FASHN_FACE_ARGS,
            *_fashn_common_args(),
        ],
    ),
    "cosmos3-nano-t2i": ModelSpec(
        id="cosmos3-nano-t2i",
        label="Cosmos 3 Nano text-to-image (certified NIM)",
        import_path="tryon.api.nvidia.cosmos_nano",
        class_name="Cosmos3NanoNimAdapter",
        method="generate_text_to_image",
        output_kind="image_bytes",
        notes=(
            "Self-hosted Cosmos3 certified NIM with NIM_MODEL_VARIANT=nano, model_mode=text2image. "
            "The hosted build.nvidia.com cosmos3 endpoint does not serve stills. "
            "Set COSMOS3_NIM_URL (default http://127.0.0.1:8010/v1/infer). "
            "Existing video ids remain cosmos3 (hosted) and cosmos3-local (Diffusers)."
        ),
        args=[
            Arg(("--prompt", "-p"), "prompt", required=True, help="Text prompt"),
            Arg(("--resolution",), "resolution", default="720_1_1",
                help="NIM resolution key (default 720_1_1)"),
            Arg(("--num-inference-steps",), "num_inference_steps", type=int),
            Arg(("--guidance-scale",), "guidance_scale", type=float),
            Arg(("--seed",), "seed", type=int),
            Arg(("--infer-url",), "infer_url", target="init",
                help="Override COSMOS3_NIM_URL"),
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
    "nano-banana-2.1": ModelSpec(
        id="nano-banana-2.1", label="Nano Banana 2.1",
        import_path="tryon.api.nano_banana", class_name="NanoBanana21Adapter",
        method="generate_image_edit", output_kind="images", env_hint="GEMINI_API_KEY",
        notes="GA 2026-10-06; successor to nano-banana-2. Adds wide ratios 1:4, 4:1, 1:8, 8:1.",
        args=[
            _img(("--image", "-i"), "image", "Input image (path or URL)", required=True),
            Arg(("--prompt", "-p"), "prompt", required=True, help="Editing instruction"),
            _gemini_aspect_ratio(wide=True),
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
    "flux3-image": ModelSpec(
        id="flux3-image",
        label="FLUX 3 Image",
        import_path="tryon.api.flux3",
        class_name="Flux3ImageAdapter",
        method="generate_image_edit",
        output_kind="images",
        env_hint="BFL_API_KEY",
        notes="Same BFL endpoint as generate; describe edits and optional layout boxes in the prompt.",
        args=_flux3_image_args(for_edit=True),
    ),
    "flux3-image-klein": ModelSpec(
        id="flux3-image-klein",
        label="FLUX 3 Image Klein",
        import_path="tryon.api.flux3",
        class_name="Flux3ImageKleinAdapter",
        method="generate_image_edit",
        output_kind="images",
        env_hint="BFL_API_KEY",
        notes="Same Klein endpoint as generate; bounding-box layout prompts supported.",
        args=_flux3_image_klein_args(for_edit=True),
    ),
    "flux3-image-klein-local": ModelSpec(
        id="flux3-image-klein-local",
        label="FLUX 3 Image Klein (local Diffusers)",
        import_path="tryon.models.flux3_image_klein",
        class_name="Flux3ImageKleinLocalAdapter",
        method="generate_image_edit",
        output_kind="images",
        extra="local",
        notes="Same ModularPipeline as generate; multi-ref + layout boxes in prompt.",
        args=_flux3_image_klein_local_args(for_edit=True),
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
    "gpt-image-2.5": ModelSpec(
        id="gpt-image-2.5",
        label="ChatGPT Images 2.5 Flare (OpenAI, edit)",
        import_path="tryon.api.openAI.image_adapter",
        class_name="GPTImageAdapter",
        method="generate_image_edit",
        output_kind="image_bytes",
        env_hint="OPENAI_API_KEY",
        notes=(
            "ChatGPT Images 2.5 Flare edit. Same OPENAI_API_KEY as --model gpt-image. "
            "Precision edits: --model gpt-image-2.5-sunburst. CLI --model gpt-image stays on 1.5."
        ),
        args=_gpt_image_25_edit_args("gpt-image-2.5-flare"),
    ),
    "gpt-image-2.5-sunburst": ModelSpec(
        id="gpt-image-2.5-sunburst",
        label="ChatGPT Images 2.5 Sunburst (OpenAI, edit)",
        import_path="tryon.api.openAI.image_adapter",
        class_name="GPTImageAdapter",
        method="generate_image_edit",
        output_kind="image_bytes",
        env_hint="OPENAI_API_KEY",
        notes=(
            "ChatGPT Images 2.5 Sunburst (precision edits). Same OPENAI_API_KEY as --model gpt-image. "
            "Everyday gen/edit: --model gpt-image-2.5 (Flare)."
        ),
        args=_gpt_image_25_edit_args("gpt-image-2.5-sunburst"),
    ),
    "muse-image": ModelSpec(
        id="muse-image",
        label="Muse Image (Meta Model API, edit / multi-ref)",
        import_path="tryon.api.muse",
        class_name="MuseImageAdapter",
        method="generate_image_edit",
        output_kind="images",
        env_hint="MODEL_API_KEY",
        notes="One or more reference images + instruction. Same MODEL_API_KEY as generate --model muse-image.",
        args=[
            Arg(("--images",), "image", nargs="+", required=True, help="One or more input images (paths or URLs)"),
            Arg(("--prompt", "-p"), "prompt", required=True, help="Editing / composition instruction"),
            *_muse_image_common_args(),
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
    "qwen-image-2.1-pro": ModelSpec(
        id="qwen-image-2.1-pro", label="Qwen-Image-2.1 Pro (DashScope edit)",
        import_path="tryon.api.qwen", class_name="QwenImageAdapter",
        method="generate_image_edit", output_kind="images", env_hint="DASHSCOPE_API_KEY",
        notes="Up to 10 reference images on qwen-image-2.1-pro.",
        args=[
            Arg(("--images",), "image", nargs="+", required=True,
                help="1–10 reference images (paths or URLs)"),
            Arg(("--prompt", "-p"), "prompt", required=True, help="Editing / composition instruction"),
            *_qwen_image_pinned_common_args("qwen-image-2.1-pro"),
        ],
    ),
    "qwen-image-2.1-turbo": ModelSpec(
        id="qwen-image-2.1-turbo", label="Qwen-Image-2.1 Turbo (DashScope edit)",
        import_path="tryon.api.qwen", class_name="QwenImageAdapter",
        method="generate_image_edit", output_kind="images", env_hint="DASHSCOPE_API_KEY",
        notes="Hosted qwen-image-2.1-turbo edit (up to 10 refs per 2.1 family docs).",
        args=[
            Arg(("--images",), "image", nargs="+", required=True,
                help="1–10 reference images (paths or URLs)"),
            Arg(("--prompt", "-p"), "prompt", required=True, help="Editing / composition instruction"),
            *_qwen_image_pinned_common_args("qwen-image-2.1-turbo"),
        ],
    ),
    "qwen-image-2.1-local": ModelSpec(
        id="qwen-image-2.1-local", label="Qwen-Image-2.1 (open-weight, local edit)",
        import_path="tryon.models.qwen_image_21", class_name="QwenImage21LocalAdapter",
        method="generate_image_edit", output_kind="images", extra="local",
        notes="HF Qwen/Qwen-Image-2.1 unified T2I+edit pipeline.",
        args=[
            Arg(("--images",), "image", nargs="+", required=True,
                help="1–10 reference images (paths or URLs)"),
            Arg(("--prompt", "-p"), "prompt", required=True, help="Editing / composition instruction"),
            *_qwen_image_21_local_core_args("Qwen/Qwen-Image-2.1"),
        ],
    ),
    "qwen-image-2.1-turbo-local": ModelSpec(
        id="qwen-image-2.1-turbo-local", label="Qwen-Image-2.1 Turbo (local edit)",
        import_path="tryon.models.qwen_image_21", class_name="QwenImage21LocalAdapter",
        method="generate_image_edit", output_kind="images", extra="local",
        notes="HF Qwen/Qwen-Image-2.1-Turbo.",
        args=[
            Arg(("--images",), "image", nargs="+", required=True,
                help="1–10 reference images (paths or URLs)"),
            Arg(("--prompt", "-p"), "prompt", required=True, help="Editing / composition instruction"),
            *_qwen_image_21_local_core_args("Qwen/Qwen-Image-2.1-Turbo"),
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
    "qie-2511-extract-outfit": ModelSpec(
        id="qie-2511-extract-outfit",
        label="QIE-2511 Extract-Outfit (worn outfit photo -> flat mockup, local)",
        import_path="tryon.models.extract_outfit", class_name="ExtractOutfitAdapter",
        method="extract_outfit", output_kind="images", extra="local",
        notes="Apache-2.0 LoRA (prithivMLmods/QIE-2511-Extract-Outfit) on Qwen-Image-Edit-2511: removes the body, "
        "pose and background and renders the clothing as a flat studio mockup (garment extraction / 'try-off'). "
        "Input must show the full outfit (cropped photos extract only the visible region). Same hardware as "
        "qwen-image-local (CUDA, ~40GB+ bf16, CPU offload on by default); needs peft: pip install -U peft diffusers "
        "transformers accelerate. Community adapter, no published metrics. Reverse direction: --model qwen-image-local / fashn-tryon-max.",
        args=[
            _img(("--image", "-i"), "image", "Photo showing the full outfit (path or URL)", required=True),
            Arg(("--prompt", "-p"), "prompt", default="Extract the clothing and create a flat mockup.",
                help="Trigger prompt (the default activates the LoRA)"),
            Arg(("--steps",), "num_inference_steps", type=int, default=40, help="Denoising steps"),
            Arg(("--true-cfg-scale",), "true_cfg_scale", type=float, default=4.0),
            Arg(("--guidance-scale",), "guidance_scale", type=float, default=1.0),
            Arg(("--seed",), "seed", type=int),
            Arg(("--num-images",), "num_images", type=int, default=1),
            Arg(("--lora-id",), "lora_id", target="init", help="LoRA repo id or path (default prithivMLmods/QIE-2511-Extract-Outfit)"),
            Arg(("--edit-model-id",), "edit_model_id", target="init", help="Base edit model (default Qwen/Qwen-Image-Edit-2511)"),
            Arg(("--dtype",), "dtype", target="init", default="bfloat16", choices=["bfloat16", "float16", "float32"]),
            Arg(("--no-cpu-offload",), "cpu_offload", target="init", action="store_false", default=True,
                help="Disable CPU offload (needs ~40GB+ VRAM)"),
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
    "fashn-product-to-model": ModelSpec(
        id="fashn-product-to-model", label="FASHN Product to Model (product photo -> person wearing it)",
        import_path="tryon.api.fashn", class_name="FashnAdapter",
        method="generate_product_to_model", output_kind="images", env_hint="FASHN_API_KEY",
        notes=_FASHN_NOTE + "Preview lifecycle. Clothing, shoes, hats, jewellery, bags. Generates a NEW person "
        "(it does not keep an existing photo's pose/background -- use --model fashn-tryon-max for that). "
        "--image-prompt guides pose/lighting, --background-reference anchors the scene, --face-reference fixes identity.",
        args=[
            _img(("--product-image", "--image", "-i"), "product_image", "Product photo (path or URL)", required=True),
            Arg(("--prompt", "-p"), "prompt", help='Styling / person / background, e.g. "tucked-in, studio background"'),
            Arg(("--image-prompt",), "image_prompt", help="Inspiration image for pose, environment and lighting"),
            Arg(("--background-reference",), "background_reference", help="Backdrop image (people in it are ignored)"),
            Arg(("--aspect-ratio",), "aspect_ratio",
                choices=["1:1", "3:4", "4:3", "9:16", "16:9", "2:3", "3:2", "4:5", "5:4"],
                help="Default: inherited from the most specific image supplied"),
            *_FASHN_FACE_ARGS,
            *_fashn_common_args(),
        ],
    ),
    "fashn-model-swap": ModelSpec(
        id="fashn-model-swap", label="FASHN Model Swap (change the model, keep the outfit)",
        import_path="tryon.api.fashn", class_name="FashnAdapter",
        method="generate_model_swap", output_kind="images", env_hint="FASHN_API_KEY",
        notes=_FASHN_NOTE + "Experimental lifecycle. Changes face, skin tone and hair while preserving clothing "
        "and pose; --face-reference gives repeatable campaign identities.",
        args=[
            _img(("--model-image", "--image", "-i"), "model_image", "Source fashion photo (path or URL)", required=True),
            Arg(("--prompt", "-p"), "prompt", help='Identity guidance, e.g. "Asian woman with blue hair" (auto if omitted)'),
            *_FASHN_FACE_ARGS,
            *_fashn_common_args(),
        ],
    ),
    "fashn-face-to-model": ModelSpec(
        id="fashn-face-to-model", label="FASHN Face to Model (headshot -> try-on-ready avatar)",
        import_path="tryon.api.fashn", class_name="FashnAdapter",
        method="generate_face_to_model", output_kind="images", env_hint="FASHN_API_KEY",
        notes=_FASHN_NOTE + "Experimental lifecycle. Turns a selfie/headshot into an upper-body avatar usable as "
        "the person image for fashn-tryon-max when no full-body photo exists. Vertical ratios only.",
        args=[
            _img(("--face-image", "--image", "-i"), "face_image", "Headshot or selfie (path or URL)", required=True),
            Arg(("--prompt", "-p"), "prompt", help='Body shape guidance, e.g. "athletic build" (inferred if omitted)'),
            Arg(("--aspect-ratio",), "aspect_ratio", choices=["1:1", "4:5", "3:4", "2:3", "9:16"], help="Default 2:3"),
            *_fashn_common_args(fmt="jpeg"),
        ],
    ),
    "fashn-reframe": ModelSpec(
        id="fashn-reframe", label="FASHN Reframe (expand or crop to a new aspect ratio)",
        import_path="tryon.api.fashn", class_name="FashnAdapter",
        method="generate_reframe", output_kind="images", env_hint="FASHN_API_KEY",
        notes=_FASHN_NOTE + "Experimental lifecycle. FASHN decides whether to outpaint or crop; errors if the image "
        "already has the target ratio.",
        args=[
            _img(("--image", "-i"), "image", "Source image (path or URL)", required=True),
            Arg(("--aspect-ratio",), "aspect_ratio", required=True,
                choices=["21:9", "1:1", "4:3", "3:2", "2:3", "5:4", "4:5", "3:4", "16:9", "9:16"]),
            *_fashn_common_args(),
        ],
    ),
    "fashn-edit": ModelSpec(
        id="fashn-edit", label="FASHN Edit (prompt edit preserving subject and product)",
        import_path="tryon.api.fashn", class_name="FashnAdapter",
        method="generate_image_edit", output_kind="images", env_hint="FASHN_API_KEY",
        notes=_FASHN_NOTE + "Pose/view changes, styling, lighting, small fixes. Optional --mask (white = prioritise, "
        "same size as the image) and --image-context (background/pose/texture reference).",
        args=[
            _img(("--image", "-i"), "image", "Source image (path or URL)", required=True),
            Arg(("--prompt", "-p"), "prompt", required=True, help="Edit instruction"),
            Arg(("--mask",), "mask", help="Mask image, same dimensions as the source"),
            Arg(("--image-context",), "image_context", help="Visual reference for the edit"),
            *_fashn_common_args(),
        ],
    ),
}

# --------------------------------------------------------------------------
# understand (image understanding / captioning)
# --------------------------------------------------------------------------

def _moondream_understand_args(*, model_id: str, local: bool) -> List[Arg]:
    args = [
        Arg(("--image", "-i"), "image", required=True, help="Image (path, http URL, or data URL)"),
        Arg(("--prompt", "-p"), "prompt", help="Question. Required for --skill query"),
        Arg(("--skill",), "skill", default="query", choices=["query", "caption"],
            help="query = visual question; caption = a description"),
        Arg(("--length",), "length", default="normal", choices=["short", "normal", "long"],
            help="Caption density (caption skill only)"),
        Arg(("--temperature",), "temperature", type=float, help="Optional sampling temperature"),
        Arg(("--max-tokens",), "max_tokens", type=int, help="Optional max output tokens"),
        Arg(("--moondream-model",), "moondream_model", target="init", call_name="model",
            default=model_id, help="Upstream Moondream model id"),
    ]
    if not local:
        args.append(Arg(("--base-url",), "base_url", target="init", help="Override MOONDREAM_BASE_URL"))
    return args


def _moondream_detect_args(*, model_id: str, local: bool) -> List[Arg]:
    args = [
        Arg(("--image", "-i"), "image", required=True, help="Image (path, http URL, or data URL)"),
        Arg(("--object",), "object", required=True, help="What to find, in plain language (dress, button, logo)"),
        Arg(("--skill",), "skill", default="detect", choices=["detect", "point", "segment"],
            help="detect = boxes; point = centroids; segment = SVG path"),
        Arg(("--threshold",), "threshold", type=float, help="Detect confidence cut (default 0.30 upstream)"),
        Arg(("--max-points",), "max_points", type=int, help="Point skill cap (default 64 upstream)"),
        Arg(("--moondream-model",), "moondream_model", target="init", call_name="model",
            default=model_id, help="Upstream Moondream model id"),
    ]
    if not local:
        args.append(Arg(("--base-url",), "base_url", target="init", help="Override MOONDREAM_BASE_URL"))
    return args


def _moondream_understand_specs() -> Dict[str, ModelSpec]:
    cloud = "tryon.api.moondream"
    return {
        "moondream-3.1": ModelSpec(
            id="moondream-3.1",
            label="Moondream 3.1 (query / caption)",
            import_path=cloud,
            class_name="MoondreamAdapter",
            method="understand",
            output_kind="text",
            env_hint="MOONDREAM_API_KEY",
            notes=(
                "Hosted moondream3.1-9B-A2B. --skill query asks a question; --skill caption "
                "describes the image. Boxes, points, and SVG masks: detect --model moondream-3.1. "
                "Local twin: moondream-3.1-local (pip install moondream)."
            ),
            args=_moondream_understand_args(model_id="moondream3.1-9B-A2B", local=False),
        ),
        "moondream-3-preview": ModelSpec(
            id="moondream-3-preview",
            label="Moondream 3 Preview (query / caption)",
            import_path=cloud,
            class_name="MoondreamAdapter",
            method="understand",
            output_kind="text",
            env_hint="MOONDREAM_API_KEY",
            notes="Hosted moondream3-preview. Same skills as moondream-3.1. No Photon twin.",
            args=_moondream_understand_args(model_id="moondream3-preview", local=False),
        ),
        "moondream-3.1-local": ModelSpec(
            id="moondream-3.1-local",
            label="Moondream 3.1 local (Photon)",
            import_path="tryon.models.moondream",
            class_name="MoondreamLocalAdapter",
            method="understand",
            output_kind="text",
            notes=(
                "Photon runtime, model moondream3.1-9B-A2B. pip install moondream. "
                "NVIDIA Ampere+ or Apple Silicon. Base weights do not need MOONDREAM_API_KEY."
            ),
            args=_moondream_understand_args(model_id="moondream3.1-9B-A2B", local=True),
        ),
    }


def _moondream_detect_specs() -> Dict[str, ModelSpec]:
    cloud = "tryon.api.moondream"
    note = (
        "Open-vocabulary grounding. Coordinates are normalized 0–1 from the top-left. "
        "--skill detect returns boxes, point returns centroids, segment returns an SVG path. "
        "This is not the garment-parser segment service."
    )
    return {
        "moondream-3.1": ModelSpec(
            id="moondream-3.1",
            label="Moondream 3.1 (detect / point / segment)",
            import_path=cloud,
            class_name="MoondreamAdapter",
            method="detect",
            output_kind="text",
            env_hint="MOONDREAM_API_KEY",
            notes=note + " Hosted moondream3.1-9B-A2B.",
            args=_moondream_detect_args(model_id="moondream3.1-9B-A2B", local=False),
        ),
        "moondream-3-preview": ModelSpec(
            id="moondream-3-preview",
            label="Moondream 3 Preview (detect / point / segment)",
            import_path=cloud,
            class_name="MoondreamAdapter",
            method="detect",
            output_kind="text",
            env_hint="MOONDREAM_API_KEY",
            notes=note + " Hosted moondream3-preview.",
            args=_moondream_detect_args(model_id="moondream3-preview", local=False),
        ),
        "moondream-3.1-local": ModelSpec(
            id="moondream-3.1-local",
            label="Moondream 3.1 local (detect / point / segment)",
            import_path="tryon.models.moondream",
            class_name="MoondreamLocalAdapter",
            method="detect",
            output_kind="text",
            notes=note + " Photon. pip install moondream.",
            args=_moondream_detect_args(model_id="moondream3.1-9B-A2B", local=True),
        ),
    }


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
    "kimi-k3.1-pro": ModelSpec(
        id="kimi-k3.1-pro", label="Kimi K3.1 Pro (Moonshot AI flagship multimodal reasoning model)",
        import_path="tryon.api.kimi", class_name="KimiUnderstandAdapter",
        method="understand", output_kind="text", env_hint="MOONSHOT_API_KEY",
        notes="Official Moonshot API (released 24 Oct 2026): post-trained successor to kimi-k3, 1M context, "
        "image + video input, thinking always on (--reasoning-effort low/high/max, default max). "
        "--kimi-model kimi-k3.1-pro-highspeed selects the ~2-3x faster variant. Flagship tier: needs a >= $1 "
        "Moonshot top-up. Open weights announced for early Nov 2026 (local adapter not added yet).",
        args=[
            Arg(("--kimi-model",), "kimi_model", target="init", call_name="model", default="kimi-k3.1-pro",
                choices=["kimi-k3.1-pro", "kimi-k3.1-pro-highspeed"], help="Kimi K3.1 Pro variant"),
            Arg(("--image", "-i"), "image", help="Image to understand (path or URL)"),
            Arg(("--video",), "video", help="Video to understand (path or URL)"),
            Arg(("--prompt", "-p"), "prompt", help="Question/instruction for the model"),
            Arg(("--reasoning-effort",), "reasoning_effort", default="max",
                choices=["low", "high", "max"], help="Reasoning effort level"),
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
    "glm-5.3-flashx": ModelSpec(
        id="glm-5.3-flashx",
        label="GLM-5.3-FlashX (Zhipu / Z.ai multimodal understanding, 200 tok/s)",
        import_path="tryon.api.zai", class_name="GLMUnderstandAdapter",
        method="understand", output_kind="text", env_hint="ZAI_API_KEY",
        notes="High-speed serving tier of GLM-5.3-Flash via Z.ai's OpenAI-compatible API. "
        "Native text/image/video. Thinking is always on (FlashX rejects thinking.type=disabled); "
        "use --reasoning-effort to control depth. 1M context, 128K max output.",
        args=[
            Arg(("--glm-model",), "glm_model", target="init", call_name="model",
                default="glm-5.3-flashx", choices=["glm-5.3-flashx"], help="GLM model id"),
            Arg(("--image", "-i"), "image", help="Image to understand (path or URL)"),
            Arg(("--video",), "video", help="Video to understand (path or URL)"),
            Arg(("--prompt", "-p"), "prompt", help="Question/instruction for the model"),
            Arg(("--reasoning-effort",), "reasoning_effort", default="max",
                choices=["low", "high", "max"], help="Reasoning depth (low/high/max)"),
            Arg(("--max-tokens",), "max_tokens", type=int, help="Max output tokens"),
            Arg(("--temperature",), "temperature", type=float, help="Sampling temperature (Z.ai default 1.0)"),
            Arg(("--top-p",), "top_p", type=float, help="Nucleus sampling (Z.ai default 0.95)"),
        ],
    ),
    "deepseek-flash": ModelSpec(
        id="deepseek-flash",
        label="DeepSeek-V4.1-Flash (multimodal understanding)",
        import_path="tryon.api.deepseek", class_name="DeepSeekUnderstandAdapter",
        method="understand", output_kind="text", env_hint="DEEPSEEK_API_KEY",
        notes="First-party DeepSeek Platform API (OpenAI-compatible). Native text/image only -- "
        "no video (unlike kimi-k2.6/qwen3.8-max/glm-5.3-flashx). Thinking on by default; "
        "--reasoning-effort none disables it. 1M context, 384K max output. "
        "Legacy ids deepseek-v4-flash / deepseek-v4-flash-vision-exp are billed as this model upstream.",
        args=[
            Arg(("--deepseek-model",), "deepseek_model", target="init", call_name="model",
                default="deepseek-flash", choices=["deepseek-flash"], help="DeepSeek model id"),
            Arg(("--image", "-i"), "image", required=True, help="Image to understand (path or URL)"),
            Arg(("--prompt", "-p"), "prompt", help="Question/instruction for the model"),
            Arg(("--reasoning-effort",), "reasoning_effort", default="high",
                choices=["none", "low", "high", "max"], help="Reasoning depth; none disables thinking"),
            Arg(("--max-tokens",), "max_tokens", type=int, help="Max output tokens"),
        ],
    ),
    "fashion-florence": ModelSpec(
        id="fashion-florence",
        label="Fashion Florence (open-weight garment tagger, JSON attributes)",
        import_path="tryon.models.fashion_florence", class_name="FashionFlorenceAdapter",
        method="understand", output_kind="text", extra="local",
        notes="Florence-2-large LoRA (0.77B, MIT) fine-tuned on iMaterialist: one clothing photo -> JSON "
        "{category, primary_color, material, style_tags}. Self-hosted catalogue tagging; ignores free-form "
        "questions (use a VLM such as --model gemini-3.8-flash for those). Card metrics on iMaterialist: 89.5% "
        "category, 52.7% colour / 42.6% material exact-match; weak on shoes/accessories -- validate on your own "
        "catalogue. trust_remote_code; Florence-2's custom code targets the transformers 4.4x line pinned by "
        "opentryon[local]. Runs on CPU (slow) or GPU (fp16).",
        args=[
            Arg(("--image", "-i"), "image", nargs="+", required=True, help="Clothing image(s) to tag (path or URL)"),
            Arg(("--prompt", "-p"), "prompt",
                help="Override the tagging instruction (the fine-tune expects the default; changing it may break the JSON)"),
            Arg(("--max-new-tokens",), "max_new_tokens", type=int, default=256),
            Arg(("--num-beams",), "num_beams", type=int, default=3),
            Arg(("--model-id",), "model_id", target="init", help="HF repo id or local path (default anushreeberlia/fashion-florence)"),
            Arg(("--device",), "device", target="init", choices=["cuda", "cpu"], help="Device (default cuda if available)"),
        ],
    ),
    "claude-haiku-5-5": ModelSpec(
        id="claude-haiku-5-5",
        label="Claude Haiku 5.5 (Anthropic multimodal understanding, fastest Claude)",
        import_path="tryon.api.claude", class_name="ClaudeUnderstandAdapter",
        method="understand", output_kind="text", env_hint="ANTHROPIC_API_KEY",
        notes="First-party Anthropic Messages API (released 2026-10-07). Text + image in, text out; "
        "no video. 1M context, 128K max output. Adaptive thinking on by default; --effort "
        "(default medium) controls depth and --no-thinking disables it (not allowed at xhigh/max). "
        "temperature/top_p/top_k are not exposed (non-default values return 400). "
        "Same ANTHROPIC_API_KEY the planner chat already uses.",
        args=[
            Arg(("--claude-model",), "claude_model", target="init", call_name="model",
                default="claude-haiku-5-5", choices=["claude-haiku-5-5"], help="Claude model id"),
            Arg(("--image", "-i"), "image", help="Optional image to understand (path or URL)"),
            Arg(("--prompt", "-p"), "prompt", help="Question/instruction for the model"),
            Arg(("--system",), "system", help="Optional system prompt"),
            Arg(("--effort",), "effort", choices=["low", "medium", "high", "xhigh", "max"],
                help="Effort level (API default medium)"),
            Arg(("--no-thinking",), "thinking", action="store_false", default=True,
                help="Disable thinking (only valid at high effort or below)"),
            Arg(("--max-tokens",), "max_tokens", type=int, default=4096, help="Max output tokens (includes thinking)"),
        ],
    ),
    "gemini-3.8-flash": ModelSpec(
        id="gemini-3.8-flash",
        label="Gemini 3.8 Flash (Google multimodal understanding: image, video, audio, PDF)",
        import_path="tryon.api.gemini", class_name="GeminiUnderstandAdapter",
        method="understand", output_kind="text", env_hint="GEMINI_API_KEY",
        notes="Google's most capable Flash model (stable since 2026-09-02). Text + image + video + audio + "
        "PDF in, text out; 1M-token context, 65,536 max output. --thinking-level low|medium|high "
        "('minimal' is rejected by the API). Media over ~18MB goes through the Files API; YouTube URLs are "
        "passed to Gemini directly. Same GEMINI_API_KEY as Nano Banana / Veo / Omni. "
        "For flagship reasoning / long decode use --model gemini-4-argon.",
        args=[
            Arg(("--gemini-model",), "gemini_model", target="init", call_name="model",
                default="gemini-3.8-flash", choices=["gemini-3.8-flash"], help="Gemini model id"),
            Arg(("--image", "-i"), "image", nargs="+", help="Image(s) to understand (path or URL)"),
            Arg(("--video",), "video", nargs="+", help="Video(s) (path, URL, or YouTube link)"),
            Arg(("--audio",), "audio", nargs="+", help="Audio clip(s) (path or URL)"),
            Arg(("--pdf",), "pdf", nargs="+", help="PDF document(s) (path or URL)"),
            Arg(("--prompt", "-p"), "prompt", help="Question/instruction for the model"),
            Arg(("--system",), "system", help="Optional system instruction"),
            Arg(("--thinking-level",), "thinking_level", choices=["low", "medium", "high"],
                help="Reasoning depth (API default if omitted)"),
            Arg(("--max-tokens",), "max_tokens", type=int, help="Max output tokens (<= 65536)"),
        ],
    ),
    "gemini-4-argon": ModelSpec(
        id="gemini-4-argon",
        label="Gemini 4 Argon (Google flagship reasoning, long decode, agentic video)",
        import_path="tryon.api.gemini", class_name="GeminiUnderstandAdapter",
        method="understand", output_kind="text", env_hint="GEMINI_API_KEY",
        notes=(
            "Gemini 4 Argon (stable gemini-4-argon): multimodal text + image + video + audio + PDF → text. "
            "Unified 1M token budget (input + thinking + output). Default thinking medium; paid tier only. "
            "Long decode: set --max-tokens above 65536 (generateContent automatic continuation) or "
            "--background with text-only input and --max-tokens > 65536 (Interactions API, polls up to 24h). "
            "--video-processing agentic for long-form video QA. Requires google-genai>=2.30.1. "
            "Fast/cheap multimodal: --model gemini-3.8-flash."
        ),
        args=[
            Arg(("--gemini-model",), "gemini_model", target="init", call_name="model",
                default="gemini-4-argon", choices=["gemini-4-argon"], help="Gemini model id"),
            Arg(("--image", "-i"), "image", nargs="+", help="Image(s) to understand (path or URL)"),
            Arg(("--video",), "video", nargs="+", help="Video(s) (path, URL, or YouTube link)"),
            Arg(("--video-processing",), "video_processing", default="static",
                choices=["static", "agentic"],
                help="Video timeline mode (agentic: dynamic navigation; Argon only)"),
            Arg(("--audio",), "audio", nargs="+", help="Audio clip(s) (path or URL)"),
            Arg(("--pdf",), "pdf", nargs="+", help="PDF document(s) (path or URL)"),
            Arg(("--prompt", "-p"), "prompt", help="Question/instruction for the model"),
            Arg(("--system",), "system", help="Optional system instruction"),
            Arg(("--thinking-level",), "thinking_level", choices=["low", "medium", "high"],
                help="Reasoning depth (Argon default medium if omitted)"),
            Arg(("--max-tokens",), "max_tokens", type=int,
                help="Max thinking+output tokens (up to 1048576; >65536 enables long decode)"),
            Arg(("--background",), "background", action="store_true",
                help="Text-only long decode via Interactions API (requires --max-tokens > 65536)"),
            Arg(("--poll-interval",), "poll_interval", type=float, default=5.0,
                help="Seconds between interaction status polls when --background"),
        ],
    ),
    "gemini-4-argon-cyber-permissive": ModelSpec(
        id="gemini-4-argon-cyber-permissive",
        label="Gemini 4 Argon Cyber Permissive (allowlist, defensive cyber)",
        import_path="tryon.api.gemini", class_name="GeminiUnderstandAdapter",
        method="understand", output_kind="text", env_hint="GEMINI_API_KEY",
        notes=(
            "Fairwind Program allowlist only (`gemini-4-argon-cyber-permissive`). Same multimodal "
            "understand surface as gemini-4-argon; default thinking HIGH; computer use not supported. "
            "Public Gemini API consumers without allowlist access should use gemini-4-argon."
        ),
        args=[
            Arg(("--gemini-model",), "gemini_model", target="init", call_name="model",
                default="gemini-4-argon-cyber-permissive",
                choices=["gemini-4-argon-cyber-permissive"], help="Gemini model id"),
            Arg(("--image", "-i"), "image", nargs="+", help="Image(s) to understand (path or URL)"),
            Arg(("--video",), "video", nargs="+", help="Video(s) (path, URL, or YouTube link)"),
            Arg(("--video-processing",), "video_processing", default="static",
                choices=["static", "agentic"], help="Video timeline mode (agentic on long clips)"),
            Arg(("--audio",), "audio", nargs="+", help="Audio clip(s) (path or URL)"),
            Arg(("--pdf",), "pdf", nargs="+", help="PDF document(s) (path or URL)"),
            Arg(("--prompt", "-p"), "prompt", help="Question/instruction for the model"),
            Arg(("--system",), "system", help="Optional system instruction"),
            Arg(("--thinking-level",), "thinking_level", choices=["low", "medium", "high"],
                help="Reasoning depth (Cyber Permissive default high if omitted)"),
            Arg(("--max-tokens",), "max_tokens", type=int,
                help="Max thinking+output tokens (up to 1048576; >65536 enables long decode)"),
            Arg(("--background",), "background", action="store_true",
                help="Text-only long decode via Interactions API (requires --max-tokens > 65536)"),
            Arg(("--poll-interval",), "poll_interval", type=float, default=5.0,
                help="Seconds between interaction status polls when --background"),
        ],
    ),
    "qwen3.8-max": ModelSpec(
        id="qwen3.8-max", label="Qwen3.8-Max (DashScope multimodal understanding)",
        import_path="tryon.api.qwen", class_name="QwenUnderstandAdapter",
        method="understand", output_kind="text", env_hint="DASHSCOPE_API_KEY",
        notes="Hosted Qwen3.8-Max via DashScope OpenAI-compatible API. Native text/image/video. "
        "Thinking on by default; use --no-thinking or --reasoning-effort to control. "
        "Need audio input too? --model qwen3.8-omni-flash.",
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
    "qwen3.8-omni-flash": ModelSpec(
        id="qwen3.8-omni-flash",
        label="Qwen3.8-Omni-Flash (DashScope native omni-modal understanding)",
        import_path="tryon.api.qwen", class_name="QwenUnderstandAdapter",
        method="understand", output_kind="text", env_hint="DASHSCOPE_API_KEY",
        notes="Native omni-modal Qwen (text/image/audio/video in, text-only out). 1M-token "
        "context, 131K max output. Same DASHSCOPE_API_KEY as qwen3.8-max. "
        "Audio input requires this model (qwen3.8-max rejects --audio).",
        args=[
            Arg(("--qwen-model",), "qwen_model", target="init", call_name="model",
                default="qwen3.8-omni-flash", choices=["qwen3.8-omni-flash"],
                help="Qwen DashScope model id"),
            Arg(("--image", "-i"), "image", help="Image to understand (path or URL)"),
            Arg(("--video",), "video", help="Video to understand (path or URL)"),
            Arg(("--audio",), "audio", help="Audio to understand (path or URL)"),
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
    "deepseek-vl2": ModelSpec(
        id="deepseek-vl2",
        label="DeepSeek-VL2 (open-weight, local)",
        import_path="tryon.models.deepseek_vl2", class_name="DeepSeekVL2Adapter",
        method="understand", output_kind="text", extra="local",
        notes="No first-party hosted API exists for DeepSeek-VL2 (deepseek-flash/deepseek-v4-pro are "
        "the only hosted DeepSeek models) -- local is the only path. Default deepseek-ai/deepseek-vl2-tiny "
        "(single-GPU friendly); pass a heavier variant via DEEPSEEK_VL2_MODEL_ID. Needs DeepSeek's own "
        "deepseek_vl2 package: pip install \"git+https://github.com/deepseek-ai/DeepSeek-VL2.git\" "
        "(not part of opentryon[local]).",
        args=[
            Arg(("--image", "-i"), "image", help="Image to understand (path or URL)"),
            Arg(("--video",), "video", help="Video to understand (path or URL, requires `pip install decord`)"),
            Arg(("--prompt", "-p"), "prompt", help="Question/instruction for the model"),
            Arg(("--num-frames",), "num_frames", type=int, default=8, help="Frames to sample from --video"),
            Arg(("--max-new-tokens",), "max_new_tokens", type=int, default=512, help="Max output tokens"),
            Arg(("--do-sample",), "do_sample", action="store_true", help="Enable sampling (default is greedy decoding)"),
            Arg(("--temperature",), "temperature", type=float, default=0.8, help="Sampling temperature (only with --do-sample)"),
        ],
    ),
    "deepseek-ocr": ModelSpec(
        id="deepseek-ocr",
        label="DeepSeek-OCR (open-weight, local document/image OCR)",
        import_path="tryon.models.deepseek_ocr", class_name="DeepSeekOCRAdapter",
        method="understand", output_kind="text", extra="local",
        notes="No first-party hosted API exists for DeepSeek-OCR -- local is the only path. "
        "'Contexts Optical Compression': reads scans/screenshots/photographed documents "
        "-- garment care labels, size tags, SKU sheets. Needs flash-attn; DeepSeek's model card pins "
        "torch==2.6.0/transformers==4.46.3/flash-attn==2.7.3, newer than opentryon[local]'s shared pin "
        "-- upgrade in a separate env if loading fails. DEEPSEEK_OCR_MODEL_ID overrides the HF id "
        "(e.g. deepseek-ai/DeepSeek-OCR-2 -- unverified against this adapter's model.infer() call shape).",
        args=[
            Arg(("--image", "-i"), "image", required=True, help="Image/document to OCR (path or URL)"),
            # NOT "--mode": argparse abbreviation-matches it to the reserved --model
            # flag ("--mode" is a 6-char prefix of "--model") in the probe parser
            # that resolves --model before this model's own args are registered.
            Arg(("--ocr-mode",), "mode", default="markdown", choices=["markdown", "free"],
                help="markdown: document -> markdown (default). free: plain free-form OCR text."),
            Arg(("--prompt", "-p"), "prompt", help="Raw DeepSeek-OCR prompt; overrides --mode if given"),
            Arg(("--base-size",), "base_size", type=int, default=1024, help="Base resolution"),
            Arg(("--image-size",), "image_size", type=int, default=640, help="Processing resolution"),
            Arg(("--no-crop-mode",), "crop_mode", action="store_false", default=True,
                help="Disable crop mode (large-image tiling)"),
        ],
    ),
    "ternary-bonsai-2-27b": ModelSpec(
        id="ternary-bonsai-2-27b",
        label="Ternary Bonsai 2 27B (PrismML, local llama.cpp/MLX server)",
        import_path="tryon.models.ternary_bonsai", class_name="TernaryBonsaiAdapter",
        method="understand", output_kind="text",
        notes="27B model ternary-quantized to {-1,0,+1} (Apache 2.0), built on Qwen3.8-27B; "
        "~98% of FP16 benchmark score at 5.9-8.5GB on disk. Does NOT run in-process — this is a "
        "thin OpenAI-compatible client for the llama.cpp fork (prism-b10658+) or MLX server the "
        "model ships with; start that server yourself (default http://127.0.0.1:8080/v1, "
        "override with BONSAI_BASE_URL). No opentryon[local]/torch needed for this adapter. "
        "Docs: https://docs.prismml.com/bonsai-2-27b",
        args=[
            Arg(("--image", "-i"), "image", help="Image to understand (path or URL)"),
            Arg(("--prompt", "-p"), "prompt", help="Question/instruction for the model"),
            Arg(("--thinking-budget-tokens",), "thinking_budget_tokens", type=int,
                help="Per-request thinking token budget (server also supports --reasoning-budget)"),
            Arg(("--max-tokens",), "max_tokens", type=int, help="Max output tokens"),
            Arg(("--temperature",), "temperature", type=float, help="Sampling temperature"),
            Arg(("--base-url",), "base_url", target="init",
                help="Override the local server URL (default http://127.0.0.1:8080/v1 / BONSAI_BASE_URL)"),
        ],
    ),
    "limite-1b-violetto": ModelSpec(
        id="limite-1b-violetto",
        label="Limite 1B - Violetto (Paradigma Inc, local math reasoning)",
        import_path="tryon.models.limite", class_name="LimiteAdapter",
        method="understand", output_kind="text", extra="local",
        notes="Out of OpenTryOn's fashion/media scope -- added as a reference point for a possible "
        "future generic model gateway, not roadmapped work. Text-only 1B math-reasoning model "
        "(no image/video); ~2.1GB, single-GPU/CPU friendly. No first-party hosted API exists. "
        "Single-turn use only (system + current message) -- may reinterpret multi-turn context as "
        "a different math problem. Apache-2.0.",
        args=[
            Arg(("--prompt", "-p"), "prompt", required=True, help="Math problem/question for the model"),
            Arg(("--system-prompt",), "system_prompt", help="Optional system prompt"),
            Arg(("--max-new-tokens",), "max_new_tokens", type=int, default=512, help="Max output tokens"),
            Arg(("--temperature",), "temperature", type=float,
                help="Sampling temperature (default from generation_config.json: 0.6)"),
            Arg(("--top-p",), "top_p", type=float,
                help="Nucleus sampling (default from generation_config.json: 0.95)"),
        ],
    ),
    "nemotron-omni": ModelSpec(
        id="nemotron-omni",
        label="NVIDIA Nemotron 3 Nano Omni (NIM multimodal understanding)",
        import_path="tryon.api.nvidia",
        class_name="NemotronOmniUnderstandAdapter",
        method="understand",
        output_kind="text",
        env_hint="NVIDIA_API_KEY",
        notes="Hosted NIM. OpenAI-compatible chat. Image + video + audio + text. "
        "Thinking on by default. Path A only (30B-A3B local is a later dual-path).",
        args=[
            Arg(("--image", "-i"), "image", help="Image to understand (path or URL)"),
            Arg(("--video",), "video", help="Video to understand (path or URL)"),
            Arg(("--audio",), "audio", help="Audio to understand (path or URL; wav/mp3)"),
            Arg(("--prompt", "-p"), "prompt", help="Question/instruction for the model"),
            Arg(("--no-thinking",), "enable_thinking", action="store_false", default=True,
                help="Disable Omni thinking (chat_template_kwargs.enable_thinking=false)"),
            Arg(("--reasoning-budget",), "reasoning_budget", type=int,
                help="Max reasoning tokens (-1 disables; NIM default 16384)"),
            Arg(("--max-tokens",), "max_tokens", type=int, help="Max output tokens"),
        ],
    ),
    "nemotron-3.5-super-vl": ModelSpec(
        id="nemotron-3.5-super-vl",
        label="NVIDIA Nemotron 3.5 Super VL (NIM, 120B MoE VLM)",
        import_path="tryon.api.nvidia",
        class_name="Nemotron35SuperVLUnderstandAdapter",
        method="understand",
        output_kind="text",
        env_hint="NVIDIA_API_KEY",
        notes=(
            "Hosted NIM chat on integrate.api.nvidia.com. Image + video + text; "
            "1M context; agentic reasoning via enable_thinking (default on). "
            "No native audio input (use nemotron-omni for audio). "
            "Model id nvidia/nemotron-3.5-super-vl-120b-a12b (GA Oct 2026)."
        ),
        args=[
            Arg(("--image", "-i"), "image", help="Image to understand (path or URL)"),
            Arg(("--video",), "video", help="Video to understand (path or URL)"),
            Arg(("--prompt", "-p"), "prompt", help="Question/instruction for the model"),
            Arg(("--no-thinking",), "enable_thinking", action="store_false", default=True,
                help="Disable reasoning (chat_template_kwargs.enable_thinking=false)"),
            Arg(("--max-tokens",), "max_tokens", type=int, help="Max output tokens"),
            Arg(("--temperature",), "temperature", type=float, help="Sampling temperature"),
            Arg(("--top-p",), "top_p", type=float, help="Nucleus sampling top_p"),
        ],
    ),
    "cosmos3-reasoner": ModelSpec(
        id="cosmos3-reasoner",
        label="NVIDIA Cosmos 3 Reasoner (NIM physical-world VLM)",
        import_path="tryon.api.nvidia",
        class_name="Cosmos3ReasonerAdapter",
        method="understand",
        output_kind="text",
        env_hint="NVIDIA_API_KEY",
        notes="World-model VLM for image/video QA. Same NVIDIA_API_KEY as Nemotron Omni.",
        args=[
            Arg(("--image", "-i"), "image", help="Image to understand (path or URL)"),
            Arg(("--video",), "video", help="Video to understand (path or URL)"),
            Arg(("--prompt", "-p"), "prompt", help="Question/instruction for the model"),
            Arg(("--thinking",), "enable_thinking", action="store_true", default=False,
                help="Prefix the documented Cosmos Reasoner reasoning hint"),
            Arg(("--max-tokens",), "max_tokens", type=int, help="Max output tokens"),
        ],
    ),
    "hy4-preview": ModelSpec(
        id="hy4-preview",
        label="Tencent Hy4 preview (TokenHub LLM, 770B MoE)",
        import_path="tryon.api.hy",
        class_name="Hy4Adapter",
        method="understand",
        output_kind="text",
        env_hint="TOKENHUB_API_KEY",
        notes=(
            "Tencent Cloud TokenHub OpenAI Chat Completions (model hy4-preview). "
            "Text LLM with 1M context; optional image as a vision part. Not VTON/video-gen. "
            "Local twin: --model hy4-preview-local (vLLM/SGLang). "
            "See https://hy.tencent.ai/research/hy4-preview"
        ),
        args=_hy4_understand_args(endpoint="tokenhub"),
    ),
    "hy4-preview-local": ModelSpec(
        id="hy4-preview-local",
        label="Tencent Hy4 preview (local vLLM/SGLang)",
        import_path="tryon.api.hy",
        class_name="Hy4Adapter",
        method="understand",
        output_kind="text",
        notes=(
            "OpenAI-compatible client for a self-hosted Hy4 server "
            "(official vLLM image vllm/vllm-openai:hy4-preview or SGLang). "
            "Weights tencent/Hy4-preview-FP8; TP=8, ~770GB+ FP8 — not in-process Transformers. "
            "Default HY4_BASE_URL=http://127.0.0.1:8000/v1. Hosted twin: --model hy4-preview."
        ),
        args=_hy4_understand_args(endpoint="local"),
    ),
    "flint-local": ModelSpec(
        id="flint-local",
        label="Recursive Flint (local SGLang coding agent)",
        import_path="tryon.api.recursive",
        class_name="FlintAdapter",
        method="understand",
        output_kind="text",
        notes=(
            "Serve RecursiveSI/flint with the bundled SGLang kit (default FLINT_BASE_URL="
            "http://127.0.0.1:30000/v1, model id flint). Text-only; ~80GB BF16 weights. "
            "Hosted alternative: --model flint-openrouter (OPENROUTER_API_KEY)."
        ),
        args=[
            Arg(("--prompt", "-p"), "prompt", required=True, help="Instruction for Flint"),
            Arg(("--system",), "system", help="Optional system message"),
            Arg(("--max-tokens",), "max_tokens", type=int, help="Max output tokens"),
            Arg(("--endpoint",), "endpoint", target="init", default="local",
                choices=["local"], help="Local SGLang server"),
            Arg(("--base-url",), "base_url", target="init", help="Override FLINT_BASE_URL"),
        ],
    ),
    "flint-openrouter": ModelSpec(
        id="flint-openrouter",
        label="Recursive Flint (OpenRouter free tier)",
        import_path="tryon.api.recursive",
        class_name="FlintAdapter",
        method="understand",
        output_kind="text",
        env_hint="OPENROUTER_API_KEY",
        notes="Third-party hosted Flint via OpenRouter (recursive/flint-v1.0:free). Text-only agent chat.",
        args=[
            Arg(("--prompt", "-p"), "prompt", required=True, help="Instruction for Flint"),
            Arg(("--system",), "system", help="Optional system message"),
            Arg(("--max-tokens",), "max_tokens", type=int, help="Max output tokens"),
            Arg(("--endpoint",), "endpoint", target="init", default="openrouter",
                choices=["openrouter"], help="OpenRouter API"),
        ],
    ),
    "sage-a1.5-local": ModelSpec(
        id="sage-a1.5-local",
        label="Sage-A1.5 (local SGLang/vLLM agent)",
        import_path="tryon.api.sage",
        class_name="SageA15Adapter",
        method="understand",
        output_kind="text",
        notes=(
            "InternScience/Sage-A1.5 — 35B MoE agentic model; serve with SGLang or vLLM "
            "(default SAGE_A15_BASE_URL=http://127.0.0.1:8000/v1). No first-party hosted API. "
            "Use --verification with a non-empty --system for verification mode."
        ),
        args=[
            Arg(("--prompt", "-p"), "prompt", required=True, help="User message"),
            Arg(("--system",), "system", help="System message (required when --verification)"),
            Arg(("--verification",), "verification", action="store_true",
                help="Enable Sage-A1.5 verification protocol (needs --system)"),
            Arg(("--max-tokens",), "max_tokens", type=int, help="Max output tokens"),
            Arg(("--base-url",), "base_url", target="init", help="Override SAGE_A15_BASE_URL"),
        ],
    ),
    "beam": ModelSpec(
        id="beam",
        label="Reflection Beam 1.0 (501B MoE, text chat)",
        import_path="tryon.api.reflection",
        class_name="BeamAdapter",
        method="understand",
        output_kind="text",
        env_hint="REFLECTION_API_KEY",
        notes=(
            "First-party Reflection chat (model Beam-1.0-501B-A23B). Text only — "
            "no image or video. 1M context; reasoning is always on "
            "(low|medium|high|xhigh|max; omit to use the org default). "
            "Apache-2.0 weights exist but the serve guide needs four B300s, so "
            "there is no local registry id. Named-model-only; not the understand default. "
            "See https://developers.reflection.ai/models"
        ),
        args=[
            Arg(("--prompt", "-p"), "prompt", required=True,
                help="Question or instruction"),
            Arg(("--system",), "system", help="Optional system prompt"),
            Arg(("--reasoning-effort",), "reasoning_effort",
                choices=["low", "medium", "high", "xhigh", "max"],
                help="Reasoning depth (omit to use the Reflection org default)"),
            Arg(("--max-tokens",), "max_tokens", type=int, help="Max output tokens"),
            Arg(("--temperature",), "temperature", type=float, help="Sampling temperature"),
            Arg(("--beam-model",), "beam_model", target="init", call_name="model",
                default="Beam-1.0-501B-A23B",
                choices=["Beam-1.0-501B-A23B"],
                help="Reflection model id"),
            Arg(("--base-url",), "base_url", target="init",
                help="Override REFLECTION_BASE_URL (default https://api.reflection.ai/openai/v1)"),
        ],
    ),
    "mercury-3": ModelSpec(
        id="mercury-3",
        label="Mercury 3 (Inception diffusion LLM, 1M context)",
        import_path="tryon.api.inception",
        class_name="InceptionUnderstandAdapter",
        method="understand",
        output_kind="text",
        env_hint="INCEPTION_API_KEY",
        notes=(
            "Inception Labs diffusion LLM on v1/chat/completions (OpenAI-compatible). "
            "Text in / text out; 1M context, up to 131K output tokens. "
            "reasoning_effort instant|low|medium|high; temperature 0.5–1.0. "
            "Tool calling and structured outputs supported upstream — not exposed on CLI yet. "
            "Image classification / routing: decide --model mercury-decide (v1/decisions). "
            "See https://www.inceptionlabs.ai/blog/introducing-mercury-3"
        ),
        args=[
            Arg(("--inception-model",), "inception_model", target="init", call_name="model",
                default="mercury-3",
                choices=["mercury-3", "mercury-2.5", "mercury-2", "mercury-voice"],
                help="Inception chat model id"),
            Arg(("--prompt", "-p"), "prompt", help="Question or instruction (required)"),
            Arg(("--system",), "system", help="Optional system prompt"),
            Arg(("--reasoning-effort",), "reasoning_effort",
                choices=["instant", "low", "medium", "high"],
                help="Reasoning depth (API default medium if omitted)"),
            Arg(("--max-tokens",), "max_tokens", type=int,
                help="Max output tokens (maps to max_completion_tokens)"),
            Arg(("--temperature",), "temperature", type=float,
                help="Sampling temperature (0.5–1.0 per Inception docs)"),
        ],
    ),
    **_moondream_understand_specs(),
}

# --------------------------------------------------------------------------
# video-generate
# --------------------------------------------------------------------------

_VIDEO_GENERATE = {
    "veo": ModelSpec(
        id="veo", label="Google Veo 3.1 (Generate / Fast / Lite)",
        import_path="tryon.api.veo", class_name="VeoAdapter",
        method="generate_text_to_video", output_kind="video_bytes",
        alt_method_on_image="generate_image_to_video", alt_image_dest="image",
        env_hint="GEMINI_API_KEY",
        notes=(
            "Veo 3.1 only (Veo 3.0 shut down 30 Jun 2026). --last-image switches to first+last "
            "frame interpolation; --reference-image (up to 3, 8s, 16:9, not Lite) steers style. "
            "1080p and 4k require --duration 8; Lite has no 4k and no reference images. "
            "Cloud-only: no open weights exist."
        ),
        args=[
            Arg(("--prompt", "-p"), "prompt", required=True, help="Text prompt"),
            Arg(("--image",), "image", help="Optional still image to animate (switches to image-to-video)", alt_only=True),
            Arg(("--last-image",), "last_image", help="Optional final frame (with --image; requires --duration 8)", alt_only=True),
            Arg(("--reference-image",), "reference_images", nargs="+",
                help="Up to 3 subject/style reference images (text-to-video only; 8s, 16:9)"),
            Arg(("--duration",), "duration_seconds", default="4", help='Clip length in seconds: "4", "6" or "8"'),
            Arg(("--aspect-ratio",), "aspect_ratio", default="16:9", choices=["16:9", "9:16"]),
            Arg(("--resolution",), "resolution", default="720p", choices=["720p", "1080p", "4k"]),
            Arg(("--negative-prompt",), "negative_prompt"),
            Arg(("--model-version",), "model_version", call_name="model", default="veo-3.1-generate-preview",
                choices=["veo-3.1-generate-preview", "veo-3.1-fast-generate-preview", "veo-3.1-lite-generate-preview"]),
        ],
    ),
    "sora": ModelSpec(
        id="sora", label="OpenAI Sora 2 (API REMOVED upstream 2026-09-24)",
        import_path="tryon.api.openAI.video_adapter", class_name="SoraVideoAdapter",
        method="generate_text_to_video", output_kind="video_bytes",
        alt_method_on_image="generate_image_to_video", alt_image_dest="image",
        env_hint="OPENAI_API_KEY",
        notes=(
            "DEPRECATED: OpenAI removed the Sora 2 / Sora 2 Pro video API on 24 Sep 2026; calls "
            "will fail against the live service. Kept for backward compatibility. "
            "Use veo, seedance, gemini-omni or minimax-h3 instead."
        ),
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
        label="Gemini Omni 1.1 Flash (video generation / editing / extension)",
        import_path="tryon.api.omni",
        class_name="GeminiOmniAdapter",
        method="generate_text_to_video",
        output_kind="video_bytes",
        alt_method_on_image="generate_image_to_video",
        alt_image_dest="image",
        env_hint="GEMINI_API_KEY",
        notes=(
            "Uses gemini-omni-1.1-flash via the Interactions API; the "
            "gemini-omni-flash-preview endpoint was deprecated 30 Sep 2026. "
            "--previous-interaction-id conversationally edits a prior clip; --video extends an "
            "existing clip (<=10s) by 3-10s. Cloud-only: no open weights exist."
        ),
        args=[
            Arg(("--prompt", "-p"), "prompt", required=True, help="Text prompt, edit instruction, or how to continue --video"),
            Arg(("--image",), "image", help="Optional still image to animate (switches to image-to-video)", alt_only=True),
            Arg(("--reference-image",), "reference_images", nargs="+",
                help="Optional extra subject/style reference images (image-to-video only)", alt_only=True),
            Arg(("--aspect-ratio",), "aspect_ratio", default="16:9", choices=["16:9", "9:16"]),
            Arg(("--resolution",), "resolution", choices=["360p", "720p", "1080p", "4k"],
                help="Output resolution (API default 720p)"),
            Arg(("--previous-interaction-id",), "previous_interaction_id",
                help="Prior Omni interaction id for conversational video editing"),
            Arg(("--video",), "video",
                help="Existing clip (<=10s; local path or Files/http(s) URI) to extend by 3-10s"),
        ],
    ),
    "flux3-video": ModelSpec(
        id="flux3-video",
        label="FLUX 3 Video",
        import_path="tryon.api.flux3_video",
        class_name="Flux3VideoAdapter",
        method="generate_text_to_video",
        output_kind="video_bytes",
        alt_method_on_image="generate_image_to_video",
        alt_image_dest="image",
        env_hint="BFL_API_KEY",
        notes=(
            "BFL unified video endpoint (t2v / i2v / v2v / draft_enhance). "
            "Use --video to continue a clip, --draft for a fast preview, then "
            "--draft-cache for full quality. For the Max speed/quality tier see "
            "flux3-max (version=max). Conversational video edit is a separate "
            "BFL tool (/v1/flux-tools/video-edit-v1), not this adapter."
        ),
        args=_flux3_video_args(),
    ),
    "flux3-max": ModelSpec(
        id="flux3-max",
        label="FLUX 3 Max",
        import_path="tryon.api.flux3_video",
        class_name="Flux3MaxVideoAdapter",
        method="generate_text_to_video",
        output_kind="video_bytes",
        alt_method_on_image="generate_image_to_video",
        alt_image_dest="image",
        env_hint="BFL_API_KEY",
        notes=(
            "BFL FLUX 3 Max video tier on POST /v1/flux-3-video with version=max "
            "(fastest render path per BFL). Same modes as flux3-video. Override pin "
            "with BFL_FLUX3_MAX_VERSION if BFL renames the tag."
        ),
        args=[a for a in _flux3_video_args() if a.dest != "version"],
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
            "--reference-image/--reference-video/--reference-audio enable multimodal "
            "reference-to-video (mutually exclusive with --image/--end-image). "
            "Cloud-only: no open weights. "
            "See https://seed.bytedance.com/en/seedance2_5"
        ),
        args=[
            Arg(("--prompt", "-p"), "prompt", help="Text prompt"),
            Arg(("--image",), "image", help="Optional first-frame image (switches to image-to-video)", alt_only=True),
            Arg(("--end-image",), "end_image", help="Optional last-frame image (I2V only)", alt_only=True),
            Arg(("--reference-image",), "reference_images", nargs="+",
                help="Reference-to-video: subject/style images (not combinable with --image)"),
            Arg(("--reference-video",), "reference_videos", nargs="+",
                help="Reference-to-video: motion/camera reference clips (URL or local path)"),
            Arg(("--reference-audio",), "reference_audios", nargs="+",
                help="Reference-to-video: voice/music references (needs a reference image or video)"),
            Arg(("--duration",), "duration", type=int, default=5, help="Clip length in seconds (Seedance 2.5: 4-30)"),
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
                    "dreamina-seedance-2-5-260628",
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
    "kling-v4": ModelSpec(
        id="kling-v4",
        label="Kling 4.0 video",
        import_path="tryon.api.kling_video",
        class_name="KlingVideoAdapter",
        method="generate_text_to_video",
        output_kind="video_bytes",
        alt_method_on_image="generate_image_to_video",
        alt_image_dest="image",
        env_hint="KLING_AI_API_KEY / KLING_AI_SECRET_KEY",
        notes=(
            "Kling 4.0 on the 2026 Open Platform REST API (/text-to-video/kling-4.0, "
            "/image-to-video/kling-4.0, /tasks poll). Uses API-key Bearer auth. "
            "Native 3–30s, 720p/1080p/4K, multi-shot prompts. Legacy JWT still used for Kling 3.x ids."
        ),
        args=[
            Arg(("--prompt", "-p"), "prompt", help="Text prompt (required for T2V)"),
            Arg(("--image",), "image", help="Start image (switches to I2V)", alt_only=True),
            Arg(("--end-image",), "end_image", help="Optional end frame (I2V)", alt_only=True),
            Arg(("--duration",), "duration", default="10", help="3–30 seconds"),
            Arg(("--resolution",), "resolution", default="1080p", choices=["720p", "1080p", "4k"]),
            Arg(("--aspect-ratio",), "aspect_ratio", default="16:9",
                choices=["21:9", "16:9", "1:1", "9:16", "auto"]),
            Arg(("--negative-prompt",), "negative_prompt"),
            Arg(("--model-version",), "model_version", target="init", call_name="model",
                default="kling-v4", choices=["kling-v4"]),
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
        notes="T2V / I2V with optional audio conditioning, draft mode, and prompt upsampling. "
        "Faster MiniMax H3-based sibling (no audio input): --model p-video-2-pro.",
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
    "p-video-2-pro": ModelSpec(
        id="p-video-2-pro",
        label="Pruna P-Video-2-Pro (fast, MiniMax H3-based)",
        import_path="tryon.api.pruna",
        class_name="PVideo2ProAdapter",
        method="generate_text_to_video",
        output_kind="video_bytes",
        alt_method_on_image="generate_image_to_video",
        alt_image_dest="image",
        env_hint="PRUNA_API_KEY",
        notes=(
            "Pruna's optimized MiniMax H3-based endpoint (launched 17 Sep 2026). "
            "T2V / I2V with always-on generated audio (no audio *input*, unlike --model p-video). "
            "480p/768p, 5-15s, fixed 24fps. Same PRUNA_API_KEY."
        ),
        args=[
            Arg(("--prompt", "-p"), "prompt", required=True, help="Text prompt"),
            Arg(("--image",), "image", help="Optional start image (switches to image-to-video)", alt_only=True),
            Arg(("--last-frame-image",), "last_frame_image", help="Optional last-frame reference image"),
            Arg(("--duration",), "duration", type=int, default=5, help="Duration in seconds (5-15)"),
            Arg(("--resolution",), "resolution", default="768p", choices=["480p", "768p"]),
            Arg(("--aspect-ratio",), "aspect_ratio", default="16:9",
                choices=["16:9", "9:16", "4:3", "3:4", "3:2", "2:3", "1:1"]),
            Arg(("--mode",), "mode", default="speed", choices=["speed", "quality"]),
            Arg(("--prompt-upsampler",), "prompt_upsampler", default="turbo",
                choices=["off", "turbo", "max"]),
            Arg(("--seed",), "seed", type=int),
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
    "cosmos3-local": ModelSpec(
        id="cosmos3-local",
        label="NVIDIA Cosmos 3 Nano (local Diffusers)",
        import_path="tryon.models.cosmos3",
        class_name="Cosmos3LocalAdapter",
        method="generate_text_to_video",
        output_kind="video_bytes",
        alt_method_on_image="generate_image_to_video",
        alt_image_dest="image",
        extra="local",
        notes=(
            "Open weights (nvidia/Cosmos3-Nano, 16B, OpenMDW 1.1) via Diffusers "
            "Cosmos3OmniPipeline; BF16 + large CUDA GPU only. Hosted twin is --model cosmos3 (NIM). "
            "Upstream examples use structured JSON captions; plain text also works."
        ),
        args=[
            Arg(("--prompt", "-p"), "prompt", help="Text (or JSON caption) prompt"),
            Arg(("--image",), "image", help="First-frame image (switches to image-to-video)", alt_only=True),
            Arg(("--negative-prompt",), "negative_prompt", help="Optional negative prompt"),
            Arg(("--width",), "width", type=int, default=1280),
            Arg(("--height",), "height", type=int, default=720),
            Arg(("--num-frames",), "num_frames", type=int, default=189, help="Frame count (default 189 = ~7.9s @ 24fps)"),
            Arg(("--fps",), "fps", type=int, default=24, help="Output FPS"),
            Arg(("--steps",), "num_inference_steps", type=int, default=35),
            Arg(("--guidance-scale",), "guidance_scale", type=float, default=6.0),
            Arg(("--seed",), "seed", type=int, help="RNG seed"),
            Arg(("--model-id",), "model_id", target="init",
                help="HF repo id or local path (default nvidia/Cosmos3-Nano)"),
            Arg(("--cpu-offload",), "cpu_offload", target="init", action="store_true",
                help="Enable model CPU offload to reduce VRAM"),
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
            "First-party MiniMax Hailuo 2.3 T2V/I2V. No open weights for 2.3. "
            "Camera moves via [Tracking shot] style commands in the prompt. "
            "H3 dual-path is --model minimax-h3 / minimax-h3-max / minimax-h3-local."
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
    "minimax-h3": ModelSpec(
        id="minimax-h3",
        label="MiniMax H3 (official API)",
        import_path="tryon.api.minimax",
        class_name="MiniMaxH3Adapter",
        method="generate_text_to_video",
        output_kind="video_bytes",
        alt_method_on_image="generate_image_to_video",
        alt_image_dest="image",
        env_hint="MINIMAX_API_KEY",
        notes=(
            "First-party MiniMax H3 (Hailuo 3) via V2 video_generation. "
            "T2V / first-last I2V with native stereo audio, 4–15s, 768P/2K. "
            "Same MINIMAX_API_KEY as hailuo-2.3. Fast variant: --model minimax-h3-max. "
            "Local twin: --model minimax-h3-local."
        ),
        args=[
            Arg(("--prompt", "-p"), "prompt", required=True, help="Text prompt (required, max 7000 chars)"),
            Arg(("--image",), "image", help="First-frame image (switches to I2V)", alt_only=True),
            Arg(
                ("--last-frame",),
                "last_frame",
                help="Last-frame image (I2V last-only, or pair with --image)",
            ),
            Arg(
                ("--duration",),
                "duration",
                type=int,
                default=5,
                choices=list(range(4, 16)),
                help="Seconds 4-15",
            ),
            Arg(
                ("--resolution",),
                "resolution",
                default="2K",
                choices=["768P", "2K"],
            ),
            Arg(
                ("--ratio",),
                "ratio",
                default="16:9",
                choices=["21:9", "16:9", "4:3", "1:1", "3:4", "9:16"],
                help="Required for T2V (cannot be adaptive). Ignored for I2V.",
            ),
        ],
    ),
    "minimax-h3-max": ModelSpec(
        id="minimax-h3-max",
        label="MiniMax H3 Max (official API, fast)",
        import_path="tryon.api.minimax",
        class_name="MiniMaxH3Adapter",
        method="generate_text_to_video",
        output_kind="video_bytes",
        alt_method_on_image="generate_image_to_video",
        alt_image_dest="image",
        env_hint="MINIMAX_API_KEY",
        notes=(
            "First-party MiniMax H3 Max (fast V2 variant). T2V / first-last I2V only — "
            "no reference-to-video. 480P/768P (no 2K), 5–15s. Same MINIMAX_API_KEY. "
            "Quality/2K/R2V on MiniMax: --model minimax-h3. Fal R2V twin: --model fal-h3-max."
        ),
        args=[
            Arg(("--prompt", "-p"), "prompt", required=True, help="Text prompt (required, max 7000 chars)"),
            Arg(("--image",), "image", help="First-frame image (switches to I2V)", alt_only=True),
            Arg(
                ("--last-frame",),
                "last_frame",
                help="Last-frame image (I2V last-only, or pair with --image)",
            ),
            Arg(
                ("--h3-model",),
                "h3_model",
                target="init",
                call_name="model",
                default="MiniMax-H3-Max",
                choices=["MiniMax-H3-Max"],
                help="MiniMax V2 model id",
            ),
            Arg(
                ("--duration",),
                "duration",
                type=int,
                default=5,
                choices=list(range(5, 16)),
                help="Seconds 5-15",
            ),
            Arg(
                ("--resolution",),
                "resolution",
                default="768P",
                choices=["480P", "768P"],
            ),
            Arg(
                ("--ratio",),
                "ratio",
                default="16:9",
                choices=["21:9", "16:9", "4:3", "1:1", "3:4", "9:16"],
                help="Required for T2V (cannot be adaptive). Ignored for I2V.",
            ),
        ],
    ),
    "fal-h3-max": ModelSpec(
        id="fal-h3-max",
        label="MiniMax H3 Max (Fal, T2V / I2V / R2V)",
        import_path="tryon.api.fal",
        class_name="FalH3MaxAdapter",
        method="generate_text_to_video",
        output_kind="video_bytes",
        alt_method_on_image="generate_image_to_video",
        alt_image_dest="image",
        env_hint="FAL_KEY",
        notes=(
            "Third-party Fal hoster for MiniMax H3 Max (joint MiniMax + fal.ai release). "
            "T2V, first/last I2V, and reference-to-video. 480P/768P, 5–15s. "
            "First-party MiniMax (no R2V): --model minimax-h3-max. "
            "Dedicated lip-sync/dubbing endpoint: --model fal-h3-max-lipsync. "
            "Video relighting from a lighting sphere: --model fal-h3-max-relight."
        ),
        args=[
            Arg(("--prompt", "-p"), "prompt", required=True, help="Text prompt (required)"),
            Arg(("--image",), "image", help="First-frame image (switches to I2V)", alt_only=True),
            Arg(
                ("--last-frame",),
                "last_frame",
                help="Last-frame image (I2V last-only, or pair with --image)",
            ),
            Arg(
                ("--reference-image",),
                "reference_image",
                nargs="+",
                help="Reference images for R2V (prompt as Image 1, Image 2, …). Max 12 files with video/audio.",
            ),
            Arg(
                ("--reference-video",),
                "reference_video",
                nargs="+",
                help="Reference videos for R2V (prompt as Video 1, …)",
            ),
            Arg(
                ("--reference-audio",),
                "reference_audio",
                nargs="+",
                help="Reference audio for R2V (cannot be the only reference)",
            ),
            Arg(
                ("--duration",),
                "duration",
                type=int,
                default=5,
                choices=list(range(5, 16)),
                help="Seconds 5-15",
            ),
            Arg(
                ("--resolution",),
                "resolution",
                default="768P",
                choices=["480P", "768P"],
            ),
            Arg(
                ("--ratio",),
                "ratio",
                default="16:9",
                choices=["adaptive", "21:9", "16:9", "4:3", "1:1", "3:4", "9:16"],
                help="T2V cannot be adaptive. R2V default on Fal is adaptive if you pass it. I2V ignores ratio.",
            ),
            Arg(
                ("--prompt-expansion",),
                "prompt_expansion_mode",
                default="balanced",
                choices=["balanced", "quality"],
                help="Fal prompt rewrite: balanced (~1s) or quality (up to ~30s)",
            ),
            Arg(
                ("--no-safety-checker",),
                "enable_safety_checker",
                action="store_false",
                default=True,
                help="Disable Fal safety checker",
            ),
            Arg(("--seed",), "seed", type=int, help="Optional RNG seed"),
        ],
    ),
    "fal-h3-max-lipsync": ModelSpec(
        id="fal-h3-max-lipsync",
        label="MiniMax H3 Max Lip Sync (Fal, image + audio -> video)",
        import_path="tryon.api.fal",
        class_name="FalH3MaxAdapter",
        method="generate_lip_sync",
        output_kind="video_bytes",
        env_hint="FAL_KEY",
        notes=(
            "Fal-hosted H3 Max lip-sync/dubbing endpoint — portrait + audio track in, "
            "video with matched mouth movement out. No prompt; not T2V/I2V/R2V. "
            "480P-2K (higher ceiling than fal-h3-max's 768P cap). Audio clipped to ~14.8s. "
            "Same FAL_KEY as --model fal-h3-max."
        ),
        args=[
            _img(("--image", "-i"), "image", "Portrait / face image to animate (aspect ratio 0.4-2.5)", required=True),
            Arg(("--audio",), "audio", required=True,
                help="Audio track to lip-sync to (>=5s, clipped at ~14.8s)"),
            Arg(("--resolution",), "resolution", default="768P",
                choices=["480P", "768P", "1080P", "2K"]),
            Arg(("--enable-transcription",), "enable_transcription", action="store_true",
                help="Transcribe the audio to guide lip sync accuracy"),
            Arg(("--no-safety-checker",), "enable_safety_checker", action="store_false",
                default=True, help="Disable Fal safety checker"),
            Arg(("--seed",), "seed", type=int, help="Optional RNG seed"),
        ],
    ),
    "fal-h3-max-relight": ModelSpec(
        id="fal-h3-max-relight",
        label="MiniMax H3 Max Relight (Fal, video + lighting sphere -> video)",
        import_path="tryon.api.fal",
        class_name="FalH3MaxAdapter",
        method="generate_relight",
        output_kind="video_bytes",
        env_hint="FAL_KEY",
        notes=(
            "Fal-hosted H3 Max video relighting (minimax/h3-max/relight): re-lights an existing clip "
            "(<=15s) from a lighting-sphere reference image while keeping subjects, motion, camera "
            "and audio. No prompt field. 480P-2K ($0.05-$0.32/s on Fal). Same FAL_KEY as "
            "--model fal-h3-max. Cloud-only: Fal-hosted post-trained endpoint, no open weights."
        ),
        args=[
            Arg(("--video",), "video", required=True, help="Source video to relight (path or URL, <=15s)"),
            Arg(("--reference-image",), "reference_image", required=True,
                help="Lighting-sphere render that defines the target lighting"),
            Arg(("--resolution",), "resolution", default="768P",
                choices=["480P", "768P", "1080P", "2K"]),
            Arg(("--aspect-ratio",), "aspect_ratio", default="16:9",
                choices=["adaptive", "21:9", "16:9", "4:3", "1:1", "3:4", "9:16"]),
            Arg(("--no-safety-checker",), "enable_safety_checker", action="store_false",
                default=True, help="Disable Fal safety checker"),
            Arg(("--seed",), "seed", type=int, help="Optional RNG seed"),
        ],
    ),
    "minimax-h3-local": ModelSpec(
        id="minimax-h3-local",
        label="MiniMax H3 (local Diffusers)",
        import_path="tryon.models.minimax_h3",
        class_name="MiniMaxH3LocalAdapter",
        method="generate_text_to_video",
        output_kind="video_bytes",
        alt_method_on_image="generate_image_to_video",
        alt_image_dest="image",
        extra="local",
        notes=(
            "Open weights via Hugging Face Diffusers ModularPipeline (CUDA + diffusers from main). "
            "768p H3-Base only — 2K regenerate is not open-sourced. "
            "Community License excludes US/EU/UK/South Korea for local weights."
        ),
        args=[
            Arg(("--prompt", "-p"), "prompt", required=True, help="Text prompt"),
            Arg(("--image",), "image", help="Optional first-frame still (switches to I2V)", alt_only=True),
            Arg(
                ("--last-frame",),
                "last_frame",
                call_name="last_image",
                help="Optional last-frame still",
            ),
            Arg(("--width",), "width", type=int, default=960, help="Width (divisible by 32)"),
            Arg(("--height",), "height", type=int, default=544, help="Height (divisible by 32)"),
            Arg(
                ("--num-frames",),
                "num_frames",
                type=int,
                default=124,
                help="Frame count; snapped to 17*n+5 in the ~5–15s window at 24fps (e.g. 124)",
            ),
            Arg(("--seed",), "seed", type=int, help="RNG seed"),
            Arg(
                ("--model-id",),
                "model_id",
                target="init",
                help="HF repo id or local path (default MiniMaxAI/MiniMax-H3)",
            ),
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
    "cosmos3": ModelSpec(
        id="cosmos3",
        label="NVIDIA Cosmos 3 Generator nano (NIM T2V/I2V)",
        import_path="tryon.api.nvidia",
        class_name="Cosmos3VideoAdapter",
        method="generate_text_to_video",
        output_kind="video_bytes",
        alt_method_on_image="generate_image_to_video",
        alt_image_dest="image",
        env_hint="NVIDIA_API_KEY",
        notes="NIM POST infer. T2V when prompt only; I2V when --image is set. "
        "Self-host: COSMOS3_INFER_URL=http://127.0.0.1:8000/v1/infer.",
        args=[
            Arg(("--prompt", "-p"), "prompt", help="Text prompt (required for T2V; optional for I2V)"),
            Arg(("--image",), "image", help="First-frame image (switches to I2V)", alt_only=True),
            Arg(
                ("--resolution",),
                "resolution",
                default="720",
                choices=[
                    "256", "480", "720",
                    "256_16_9", "480_16_9", "720_16_9",
                    "256_1_1", "480_1_1", "720_1_1",
                    "256_9_16", "480_9_16", "720_9_16",
                    "256_4_3", "480_4_3", "720_4_3",
                    "256_3_4", "480_3_4", "720_3_4",
                ],
                help="Tier + optional aspect (default 720 = 720_16_9)",
            ),
            Arg(("--num-output-frames",), "num_output_frames", type=int, default=121,
                help="Frame count (720p max 197)"),
            Arg(("--fps",), "fps", type=float, default=24.0),
            Arg(("--steps",), "steps", type=int, default=35),
            Arg(("--guidance-scale",), "guidance_scale", type=float, default=6.0),
            Arg(("--negative-prompt",), "negative_prompt"),
            Arg(("--seed",), "seed", type=int),
        ],
    ),
    "fashn-image-to-video": ModelSpec(
        id="fashn-image-to-video", label="FASHN Image to Video (animate a fashion still)",
        import_path="tryon.api.fashn", class_name="FashnAdapter",
        method="generate_image_to_video", output_kind="video_bytes", env_hint="FASHN_API_KEY",
        notes=_FASHN_NOTE + "5 or 10 s MP4; credits 5s = 1/3/6 and 10s = 2/6/12 at 480p/720p/1080p. Leave --prompt "
        "empty for automatic motion (FASHN advises short guidance only). --end-image sets the final frame.",
        args=[
            _img(("--image", "-i"), "image", "Source image (path or URL, min 301x301)", required=True),
            Arg(("--prompt", "-p"), "prompt", help="Optional short motion guidance"),
            Arg(("--duration",), "duration", type=int, default=5, choices=[5, 10], help="Clip length in seconds"),
            Arg(("--resolution",), "resolution", default="1080p", choices=["480p", "720p", "1080p"]),
            Arg(("--end-image",), "end_image", help="Optional final frame"),
        ],
    ),
    "cosmos3-nano-v2v": ModelSpec(
        id="cosmos3-nano-v2v",
        label="Cosmos 3 Nano video-to-video (certified NIM)",
        import_path="tryon.api.nvidia.cosmos_nano",
        class_name="Cosmos3NanoNimAdapter",
        method="generate_video_to_video",
        output_kind="video_bytes",
        notes=(
            "Self-hosted Cosmos3 certified NIM, NIM_MODEL_VARIANT=nano, model_mode=video2video. "
            "Hosted cosmos3 remains T2V/I2V only. COSMOS3_NIM_URL default http://127.0.0.1:8010/v1/infer."
        ),
        args=[
            Arg(("--video",), "video", required=True, help="Conditioning video (path or data URL)"),
            Arg(("--prompt", "-p"), "prompt", help="Optional edit instruction"),
            Arg(("--resolution",), "resolution", help="NIM resolution key"),
            Arg(("--num-inference-steps",), "num_inference_steps", type=int),
            Arg(("--guidance-scale",), "guidance_scale", type=float),
            Arg(("--seed",), "seed", type=int),
            Arg(("--infer-url",), "infer_url", target="init", help="Override COSMOS3_NIM_URL"),
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
    "fashn-bg-remove": ModelSpec(
        id="fashn-bg-remove", label="FASHN Background Remove (hosted, 1 credit)",
        import_path="tryon.api.fashn", class_name="FashnAdapter",
        method="remove_background", output_kind="images", env_hint="FASHN_API_KEY",
        notes=_FASHN_NOTE + "Transparent-background PNG in 1-3 s (min 128x128). Local alternative: --model ben2.",
        args=[
            _img(("--image", "-i"), "image", "Input image (path or URL)", required=True),
        ],
    ),
}

_GEMINI_TTS_VOICES = ["Zephyr", "Puck", "Charon", "Kore", "Fenrir", "Leda", "Orus", "Aoede", "Callirrhoe", "Autonoe", "Enceladus", "Iapetus", "Umbriel", "Algieba", "Despina", "Erinome", "Algenib", "Rasalgethi", "Laomedeia", "Achernar", "Alnilam", "Schedar", "Gacrux", "Pulcherrima", "Achird", "Zubenelgenubi", "Vindemiatrix", "Sadachbia", "Sadaltager", "Sulafat"]

_GEMINI_TTS_NOTES = (
    "Google Gemini 3.8 TTS over the Interactions API (GEMINI_API_KEY). Text in, WAV out (24 kHz mono "
    "16-bit by default; --audio-format audio/l16|audio/mulaw|audio/alaw with --sample-rate). 30 prebuilt "
    "voices or a custom voice_... id; --style sets delivery (not spoken); inline tags like <sigh> or "
    "<short pause> go in --text (the transcript is read verbatim). Two-speaker dialogue: --dialogue "
    "turns.json --speaker Joe=Puck Jane=Kore (exactly two prebuilt voices per request)."
)


def _gemini_tts_args(default_model: str) -> List[Arg]:
    return [
        Arg(("--text", "-t"), "text", help="Text to speak (required unless --dialogue is set)"),
        Arg(("--voice",), "voice", default="Kore",
            help="Prebuilt voice name (" + ", ".join(_GEMINI_TTS_VOICES[:6]) + ", ...) or a custom voice_... id"),
        Arg(("--style",), "style", help='Delivery direction, e.g. "cheerful and friendly" (not spoken)'),
        Arg(("--dialogue",), "dialogue",
            help='Two-speaker mode: JSON string or file of [{"speaker","text","style"?}] turns'),
        Arg(("--speaker",), "speakers", nargs="+", help="With --dialogue: exactly two Name=Voice entries"),
        Arg(("--audio-format",), "mime_type", default="audio/wav",
            choices=["audio/wav", "audio/l16", "audio/mulaw", "audio/alaw"], help="Output encoding"),
        Arg(("--sample-rate",), "sample_rate", type=int, choices=[8000, 16000, 24000], help="Sample rate in Hz"),
        Arg(("--tts-model",), "tts_model", target="init", call_name="model", default=default_model,
            choices=["gemini-3.8-flash-tts", "gemini-3.8-flash-lite-tts"], help="Gemini TTS model id"),
    ]


_TTS = {
    "gemini-3.8-flash-tts": ModelSpec(
        id="gemini-3.8-flash-tts",
        label="Gemini 3.8 Flash TTS (Google text-to-speech, most expressive, 130+ languages)",
        import_path="tryon.api.gemini", class_name="GeminiTTSAdapter",
        method="generate_speech", output_kind="audio_bytes", env_hint="GEMINI_API_KEY",
        notes=_GEMINI_TTS_NOTES + " Faster/cheaper sibling: --model gemini-3.8-flash-lite-tts. "
        "Other TTS vendor: --model eleven-v4.",
        args=_gemini_tts_args("gemini-3.8-flash-tts"),
    ),
    "gemini-3.8-flash-lite-tts": ModelSpec(
        id="gemini-3.8-flash-lite-tts",
        label="Gemini 3.8 Flash-Lite TTS (Google text-to-speech, fast/low-cost, 100+ languages)",
        import_path="tryon.api.gemini", class_name="GeminiTTSAdapter",
        method="generate_speech", output_kind="audio_bytes", env_hint="GEMINI_API_KEY",
        notes=_GEMINI_TTS_NOTES + " Most expressive / complex multi-speaker: --model gemini-3.8-flash-tts.",
        args=_gemini_tts_args("gemini-3.8-flash-lite-tts"),
    ),
    "eleven-v4": ModelSpec(
        id="eleven-v4",
        label="ElevenLabs Eleven v4 (text-to-speech, expressive)",
        import_path="tryon.api.elevenlabs", class_name="ElevenLabsAdapter",
        method="generate_speech", output_kind="audio_bytes", env_hint="ELEVENLABS_API_KEY",
        notes="Most emotionally rich/expressive TTS model. 90+ languages, 10,000 char limit. "
        "Default voice is ElevenLabs' premade 'Rachel' (--voice-id to override). "
        "Real-time/low-latency sibling: --model eleven-v4-turbo.",
        args=[
            Arg(("--text", "-t"), "text", required=True, help="Text to speak"),
            Arg(("--voice-id",), "voice_id", default="21m00Tcm4TlvDq8ikWAM",
                help="ElevenLabs voice id (default: premade 'Rachel')"),
            Arg(("--eleven-model",), "eleven_model", target="init", call_name="model",
                default="eleven_v4", choices=["eleven_v4"], help="ElevenLabs model id"),
            Arg(("--output-format",), "output_format", default="mp3_44100_128",
                choices=["mp3_44100_128", "mp3_44100_192", "mp3_44100_96", "mp3_44100_64",
                         "mp3_44100_32", "mp3_24000_48", "mp3_22050_32",
                         "wav_44100", "wav_48000", "wav_24000", "wav_16000",
                         "pcm_44100", "pcm_48000", "pcm_24000", "pcm_16000",
                         "opus_48000_128", "ulaw_8000", "alaw_8000"],
                help="Audio codec/sample-rate/bitrate"),
            Arg(("--language-code",), "language_code", help="ISO 639-1 code to force text normalization"),
            Arg(("--stability",), "stability", type=float, default=0.5, help="Emotional range (0-1)"),
            Arg(("--similarity-boost",), "similarity_boost", type=float, default=0.75,
                help="Adherence to the original voice (0-1)"),
            Arg(("--style",), "style", type=float, default=0.0, help="Style exaggeration (0-1)"),
            Arg(("--speed",), "speed", type=float, default=1.0, help="Speech rate multiplier"),
            Arg(("--no-speaker-boost",), "use_speaker_boost", action="store_false", default=True,
                help="Disable enhanced speaker similarity"),
            Arg(("--seed",), "seed", type=int, help="Deterministic sampling seed (0-4294967295)"),
        ],
    ),
    "eleven-v4-turbo": ModelSpec(
        id="eleven-v4-turbo",
        label="ElevenLabs Eleven v4 Turbo (text-to-speech, low-latency)",
        import_path="tryon.api.elevenlabs", class_name="ElevenLabsAdapter",
        method="generate_speech", output_kind="audio_bytes", env_hint="ELEVENLABS_API_KEY",
        notes="Real-time-oriented sibling of eleven-v4 (~100ms median latency); adds audio tags "
        "for delivery control (e.g. '[whispers]', '[laughs]') inside --text. "
        "Same ELEVENLABS_API_KEY. Most expressive/highest quality: --model eleven-v4.",
        args=[
            Arg(("--text", "-t"), "text", required=True,
                help="Text to speak; supports audio tags like [whispers], [laughs]"),
            Arg(("--voice-id",), "voice_id", default="21m00Tcm4TlvDq8ikWAM",
                help="ElevenLabs voice id (default: premade 'Rachel')"),
            Arg(("--eleven-model",), "eleven_model", target="init", call_name="model",
                default="eleven_v4_turbo", choices=["eleven_v4_turbo"], help="ElevenLabs model id"),
            Arg(("--output-format",), "output_format", default="mp3_44100_128",
                choices=["mp3_44100_128", "mp3_44100_192", "mp3_44100_96", "mp3_44100_64",
                         "mp3_44100_32", "mp3_24000_48", "mp3_22050_32",
                         "wav_44100", "wav_48000", "wav_24000", "wav_16000",
                         "pcm_44100", "pcm_48000", "pcm_24000", "pcm_16000",
                         "opus_48000_128", "ulaw_8000", "alaw_8000"],
                help="Audio codec/sample-rate/bitrate"),
            Arg(("--language-code",), "language_code", help="ISO 639-1 code to force text normalization"),
            Arg(("--stability",), "stability", type=float, default=0.5, help="Emotional range (0-1)"),
            Arg(("--similarity-boost",), "similarity_boost", type=float, default=0.75,
                help="Adherence to the original voice (0-1)"),
            Arg(("--style",), "style", type=float, default=0.0, help="Style exaggeration (0-1)"),
            Arg(("--speed",), "speed", type=float, default=1.0, help="Speech rate multiplier"),
            Arg(("--no-speaker-boost",), "use_speaker_boost", action="store_false", default=True,
                help="Disable enhanced speaker similarity"),
            Arg(("--seed",), "seed", type=int, help="Deterministic sampling seed (0-4294967295)"),
        ],
    ),
}

# --------------------------------------------------------------------------
# decide  ("System One" decision models: state + typed questions -> calibrated answers)
# --------------------------------------------------------------------------

_DECIDE_QUESTIONS_HELP = (
    "Questions as a JSON string or path to a JSON file: "
    '{"name": {"type": "noul|choice|score", "instructions": "...", "criteria": {...}|[...]}}'
)

_DECIDE = {
    "d1-3b": ModelSpec(
        id="d1-3b",
        label="Liquid AI d1-3B (open-weight decision model, text + images)",
        import_path="tryon.models.liquid_d1", class_name="LiquidD1Adapter",
        method="decide", output_kind="text", extra="local",
        notes="Not a chat model: returns typed, calibrated answers (noul yes/no, choice, score) in one "
        "forward pass with zero output tokens. Text/JSON state and/or images. 3.12B, bfloat16, "
        "32K context, needs transformers>=5.14 (separate env; the shared opentryon[local] pin is older). "
        "LFM Open License v1.0. Use for garment attribute classification, try-on QC gating, routing. "
        "Audio too: --model d1-omni-600m. Hosted twin: --model jev (text only).",
        args=[
            Arg(("--questions", "-q"), "questions", required=True, help=_DECIDE_QUESTIONS_HELP),
            Arg(("--state", "-s"), "state", help="Text or JSON (or path to a file) to judge; optional when --image is set"),
            Arg(("--image", "-i"), "image", nargs="+", help="Image(s) to judge (path or URL)"),
            Arg(("--variant",), "variant", target="init", default="d1-3B", choices=["d1-3B"], help="d1 variant"),
            Arg(("--model-id",), "model_id", target="init", help="HF repo id or local path (default LiquidAI/d1-3B)"),
            Arg(("--device",), "device", target="init", choices=["cuda", "mps", "cpu"], help="Device (default best available)"),
        ],
    ),
    "d1-omni-600m": ModelSpec(
        id="d1-omni-600m",
        label="Liquid AI d1-omni-600M (open-weight decision model, text + images + speech)",
        import_path="tryon.models.liquid_d1", class_name="LiquidD1Adapter",
        method="decide", output_kind="text", extra="local",
        notes="Small (587M, float16, 16K context) decision model that also accepts one 16 kHz mono "
        "speech clip (<=30s) via --audio; images and audio cannot be combined. Needs "
        "transformers>=5.15. Lower quality than d1-3B (Decision Index 15.95 vs 48.57) but far lighter. "
        "LFM Open License v1.0.",
        args=[
            Arg(("--questions", "-q"), "questions", required=True, help=_DECIDE_QUESTIONS_HELP),
            Arg(("--state", "-s"), "state", help="Text or JSON (or path to a file) to judge"),
            Arg(("--image", "-i"), "image", nargs="+", help="Image(s) to judge (path or URL); not with --audio"),
            Arg(("--audio",), "audio", help="16 kHz mono audio file (<=30s); not with --image"),
            Arg(("--variant",), "variant", target="init", default="d1-omni-600M", choices=["d1-omni-600M"], help="d1 variant"),
            Arg(("--model-id",), "model_id", target="init", help="HF repo id or local path (default LiquidAI/d1-omni-600M)"),
            Arg(("--device",), "device", target="init", choices=["cuda", "mps", "cpu"], help="Device (default best available)"),
        ],
    ),
    "jev": ModelSpec(
        id="jev",
        label="Typesafe AI Jev (hosted decision model, text/JSON)",
        import_path="tryon.api.typesafe", class_name="JevAdapter",
        method="decide", output_kind="text", env_hint="TYPESAFE_API_KEY",
        notes="First-party Typesafe System One API (POST /v1/systemone): calibrated choice/score/yes-no "
        "answers in 70-500ms, output tokens free. Text/JSON state only (no image/audio/video, no "
        "streaming). Early access: TypeSafe paused new sign-ups on 2026-09-22 -- check "
        "console.typesafe.ai. Also served via OpenRouter / Vercel AI Gateway / DigitalOcean; set "
        "TYPESAFE_BASE_URL for a compatible gateway. Open-weight image-capable alternative: --model d1-3b.",
        args=[
            Arg(("--questions", "-q"), "questions", required=True, help=_DECIDE_QUESTIONS_HELP),
            Arg(("--state", "-s"), "state", required=True, help="Text or JSON (or path to a file) to judge"),
            Arg(("--jev-model",), "jev_model", target="init", call_name="model", default="jev-latest",
                choices=["jev-latest", "jev-preview", "jev-1.13.0"], help="Jev model id/alias"),
        ],
    ),
    "mercury-decide": ModelSpec(
        id="mercury-decide",
        label="Mercury Decide (Inception classification / scoring, text + images)",
        import_path="tryon.api.inception",
        class_name="MercuryDecideAdapter",
        method="decide",
        output_kind="text",
        env_hint="INCEPTION_API_KEY",
        notes=(
            "Inception Labs POST /v1/decisions (model mercury-decide). Typed noul/choice/score "
            "answers with calibrated probabilities; text/JSON state and optional images as base64 "
            "content parts (local paths converted; remote image URLs rejected). Input tokens billed; "
            "output tokens reported but free. No streaming or chat completions. Same INCEPTION_API_KEY "
            "as understand mercury-3. See https://docs.inceptionlabs.ai/capabilities/decisions"
        ),
        args=[
            Arg(("--questions", "-q"), "questions", required=True, help=_DECIDE_QUESTIONS_HELP),
            Arg(("--state", "-s"), "state",
                help="Text or JSON (or path to a file) to judge; optional when --image is set"),
            Arg(("--image", "-i"), "image", nargs="+",
                help="Image(s) as OpenAI-style parts in state (path → base64 data URL; no remote URLs)"),
            Arg(("--inception-model",), "inception_model", target="init", call_name="model",
                default="mercury-decide", choices=["mercury-decide"], help="Mercury Decide model id"),
        ],
    ),
    "thx-01": ModelSpec(
        id="thx-01",
        label="HAL-X THX-01 (hosted decision model)",
        import_path="tryon.api.hal_x", class_name="Thx01Adapter",
        method="decide", output_kind="text", env_hint="HALX_API_KEY",
        notes="First-party HAL-X System One API (POST https://api.hal-x.ai/v1/systemone): "
        "322M Apache-2.0 decision model; choice/noul/score plus native number/excerpt/citations. "
        "TypeSafe/Jev-compatible request shape. Open-weight local twin: --model thx-01-local.",
        args=[
            Arg(("--questions", "-q"), "questions", required=True, help=_DECIDE_QUESTIONS_HELP),
            Arg(("--state", "-s"), "state", required=True, help="Text or JSON (or path to a file) to judge"),
        ],
    ),
    "thx-01-local": ModelSpec(
        id="thx-01-local",
        label="THX-01 (open-weight local decision model, Apache-2.0)",
        import_path="tryon.models.thx01", class_name="Thx01LocalAdapter",
        method="decide", output_kind="text", extra="local",
        notes="HF doofz/THX-01 via pip install thx01. Hosted twin: --model thx-01 (HALX_API_KEY).",
        args=[
            Arg(("--questions", "-q"), "questions", required=True, help=_DECIDE_QUESTIONS_HELP),
            Arg(("--state", "-s"), "state", required=True, help="Text or JSON (or path to a file) to judge"),
            Arg(("--model-id",), "model_id", target="init", default="doofz/THX-01",
                help="HF repo id or local path"),
            Arg(("--device",), "device", target="init", help="Device override passed to thx01.load"),
        ],
    ),
}

_D3_QUESTIONS_HELP = (
    _DECIDE_QUESTIONS_HELP.rstrip(".")
    + '; Decision 3.0 (d3) also supports "box" and "track" types — see docs/docs/api-reference/vllm-sr-d3.md.'
)

_D3_CATALOG = [
    ("turbo", "vllm-sr/d3-turbo", "27B", "Read-once multimodal tier; box + track"),
    ("flash", "vllm-sr/d3-flash", "9B", "Per-question read; strong vision scores"),
    ("mini", "vllm-sr/d3-mini", "4B", "Mid-size open weights"),
    ("nano", "vllm-sr/d3-nano", "2B", "Small multimodal decision model"),
    ("lite", "vllm-sr/d3-lite", "0.8B", "Edge-friendly"),
    ("edge", "vllm-sr/d3-edge", "0.6B", "Smallest d3 variant"),
]


def _d3_decide_args(*, local: bool, hf_id: str, variant: str) -> List[Arg]:
    args: List[Arg] = [
        Arg(("--questions", "-q"), "questions", required=True, help=_D3_QUESTIONS_HELP),
        Arg(("--state", "-s"), "state", help="Text or JSON (or path) describing the situation"),
        Arg(("--image", "-i"), "image", nargs="+", help="Image(s) in the input (path or URL)"),
        Arg(("--video",), "video", help="Video clip (path or URL; one clip on hosted API)"),
        Arg(
            ("--assets",),
            "assets",
            help="JSON map of placeholder -> image specs for images inside questions/options",
        ),
        Arg(
            ("--long-context",),
            "long_context",
            action="store_true",
            help="Allow up to 131072 tokens per question (local + API when supported)",
        ),
        Arg(("--model-id",), "model_id", target="init", default=hf_id, help="HF repo id override"),
    ]
    if local:
        args.append(
            Arg(
                ("--variant",),
                "variant",
                target="init",
                default=variant,
                choices=[slug for slug, *_ in _D3_CATALOG],
                help="d3 size tier (selects default HF repo when --model-id omitted)",
            )
        )
        args.append(
            Arg(("--device",), "device", target="init", choices=["cuda", "cpu"], help="Device (CUDA strongly recommended)")
        )
    return args


for _slug, _hf_id, _size, _blurb in _D3_CATALOG:
    _DECIDE[f"d3-{_slug}"] = ModelSpec(
        id=f"d3-{_slug}",
        label=f"vLLM-SR d3-{_slug} ({_size}, hosted Decision 3.0)",
        import_path="tryon.api.vllm_sr",
        class_name="D3ApiAdapter",
        method="decide",
        output_kind="text",
        env_hint="DECISION_API_KEY",
        notes=(
            f"First-party Decision 3.0 API ({_blurb}). POST https://decision.vllm-sr.ai/v1/systemone "
            f"with model {_hf_id}. Free key on the site. Local twin: d3-{_slug}-local."
        ),
        args=_d3_decide_args(local=False, hf_id=_hf_id, variant=_slug),
    )
    _DECIDE[f"d3-{_slug}-local"] = ModelSpec(
        id=f"d3-{_slug}-local",
        label=f"vLLM-SR d3-{_slug} ({_size}, local Decision 3.0)",
        import_path="tryon.models.d3",
        class_name="D3LocalAdapter",
        method="decide",
        output_kind="text",
        extra="local",
        notes=(
            f"Apache-2.0 weights {_hf_id} via transformers>=5.17 trust_remote_code. "
            f"Multimodal System One (box/track). Hosted twin: d3-{_slug} (DECISION_API_KEY)."
        ),
        args=_d3_decide_args(local=True, hf_id=_hf_id, variant=_slug),
    )

_VIDEOJEV_QUESTIONS_HELP = (
    "JSON array (or path): [{\"id\": \"...\", \"task\": \"grounding|choice\", "
    "\"query\": \"...\", \"options\": [\"A.\", \"B.\"] (choice only)}]. "
    "See docs/docs/local-models/videojev.md."
)


def _videojev_decide_args(*, variant: str, default_context: int) -> List[Arg]:
    return [
        Arg(("--questions", "-q"), "questions", required=True, help=_VIDEOJEV_QUESTIONS_HELP),
        Arg(("--video",), "video", required=True, help="Video file path or http(s) URL"),
        Arg(("--fps",), "fps", type=float, default=2.0, help="Frame sampling rate"),
        Arg(("--max-frames",), "max_frames", type=int, default=2048, help="Max frames sampled from video"),
        Arg(
            ("--context",),
            "context",
            type=int,
            default=default_context,
            help="Model context length (8192 for 4B; 262144 for 35B QA)",
        ),
        Arg(
            ("--threshold",),
            "threshold",
            type=float,
            default=0.25,
            help="Grounding probability threshold",
        ),
        Arg(
            ("--variant",),
            "variant",
            target="init",
            default=variant,
            choices=["4b", "35b-a3b"],
            help="VideoJev size tier",
        ),
        Arg(("--model-id",), "model_id", target="init", help="HF repo id or local checkpoint path"),
        Arg(("--device",), "device", target="init", choices=["cuda", "cpu"], help="Device (CUDA recommended)"),
    ]


_DECIDE.update(
    {
        "videojev-4b": ModelSpec(
            id="videojev-4b",
            label="VideoJev-4B (local video System One, grounding + MC QA)",
            import_path="tryon.models.videojev",
            class_name="VideoJevAdapter",
            method="decide",
            output_kind="text",
            extra="local",
            notes=(
                "Open-weight video decision model (MCG-NJU / Apache-2.0). Temporal grounding and "
                "multiple-choice video QA via predict_video — not chat text generation. "
                "No hosted VideoJev API; Typesafe Jev remains text-only. Needs CUDA, "
                "transformers trust_remote_code, FlashAttention 2 recommended. "
                "Larger tier: --model videojev-35b-a3b."
            ),
            args=_videojev_decide_args(variant="4b", default_context=8192),
        ),
        "videojev-35b-a3b": ModelSpec(
            id="videojev-35b-a3b",
            label="VideoJev-35B-A3B (local video System One, grounding + MC QA)",
            import_path="tryon.models.videojev",
            class_name="VideoJevAdapter",
            method="decide",
            output_kind="text",
            extra="local",
            notes=(
                "MoE-backed VideoJev on Qwen3.6-35B-A3B. Same question schema as videojev-4b; "
                "defaults to 262144 context for QA. Heavy VRAM; see VideoJev repo for base-model env vars "
                "VIDEOJEV_BASE_35B."
            ),
            args=_videojev_decide_args(variant="35b-a3b", default_context=262144),
        ),
    }
)

# --------------------------------------------------------------------------
# embed  (multimodal embeddings; vectors saved to .npz)
# --------------------------------------------------------------------------

_PPLX_EMBED_ARGS = [
    Arg(("--text", "-t"), "text", nargs="+", help="Text passage(s) to index"),
    Arg(("--image", "-i"), "image", nargs="+", help="Image(s)/rendered page(s) to index (path or URL)"),
    Arg(("--query", "-q"), "query", help="Optional text query; returns MaxSim scores against every input"),
    Arg(("--model-id",), "model_id", target="init", help="HF repo id or local path override"),
    Arg(("--device",), "device", target="init", help="Device (default cuda if available, else cpu)"),
]

_FASHION_EMBED_COMMON = [
    Arg(("--text", "-t"), "text", nargs="+", help="Product titles / descriptions to embed (text-capable models)"),
    Arg(("--image", "-i"), "image", nargs="+", help="Product photos to embed (path or URL)"),
    Arg(("--query", "-q"), "query", help="Text query; returns cosine scores against every input"),
    Arg(("--query-image",), "query_image", help='Image query ("more like this"); returns cosine scores'),
    Arg(("--model-id",), "model_id", target="init", help="HF repo id or local path override"),
    Arg(("--device",), "device", target="init", help="Device (default cuda if available, else cpu)"),
]

_EMBED = {
    "marqo-fashionsiglip": ModelSpec(
        id="marqo-fashionsiglip",
        label="Marqo-FashionSigLIP (fashion image + text retrieval, 768-d)",
        import_path="tryon.models.fashion_embed", class_name="FashionOpenCLIPAdapter",
        method="embed", output_kind="embeddings", extra="local",
        notes="Fashion-specific SigLIP (ViT-B/16, ~0.2B, Apache-2.0) fine-tuned on 1M+ fashion products; Marqo "
        "reports up to +57% MRR/recall over FashionCLIP (vendor-reported). Text + image in one 768-d space, "
        "L2-normalised. pip install open_clip_torch. Search by text (--query) or by photo (--query-image).",
        args=[*_FASHION_EMBED_COMMON,
              Arg(("--variant",), "variant", target="init", default="marqo-fashionsiglip",
                  choices=["marqo-fashionsiglip"], help="Checkpoint")],
    ),
    "moda-fashion-distilled": ModelSpec(
        id="moda-fashion-distilled",
        label="MODA fashion-distilled (HopitAI, image-to-image fashion retrieval)",
        import_path="tryon.models.fashion_embed", class_name="FashionOpenCLIPAdapter",
        method="embed", output_kind="embeddings", extra="local",
        notes="MIT. Distilled from a 3-model ensemble; reports 67.63 fine R@1 on LookBench vs 63.84 for "
        "FashionSigLIP (vendor-reported). IMAGE-ONLY here (the card documents no text usage): use --image / "
        "--query-image. Text search: --model moda-pro-lite or marqo-fashionsiglip. pip install open_clip_torch.",
        args=[*_FASHION_EMBED_COMMON,
              Arg(("--variant",), "variant", target="init", default="moda-fashion-distilled",
                  choices=["moda-fashion-distilled"], help="Checkpoint")],
    ),
    "moda-pro-lite": ModelSpec(
        id="moda-pro-lite",
        label="MODA Pro Lite (HopitAI, 213M fashion text-to-image encoder)",
        import_path="tryon.models.fashion_embed", class_name="FashionOpenCLIPAdapter",
        method="embed", output_kind="embeddings", extra="local",
        notes="Apache-2.0, 213M, catalogue/title search. Bare encoder via open_clip (the 'Plus' multi-view recipe "
        "and ANN helpers from the model card are not wired). pip install open_clip_torch.",
        args=[*_FASHION_EMBED_COMMON,
              Arg(("--variant",), "variant", target="init", default="moda-pro-lite",
                  choices=["moda-pro-lite"], help="Checkpoint")],
    ),
    "zooclaw-fashionsiglip2": ModelSpec(
        id="zooclaw-fashionsiglip2",
        label="ZooClaw-FashionSigLIP2 (fashion SigLIP2 retrieval encoder, 768-d)",
        import_path="tryon.models.fashion_embed", class_name="ZooClawFashionSigLIP2Adapter",
        method="embed", output_kind="embeddings", extra="local",
        notes="Apache-2.0 SigLIP2-base fine-tune (~375M; 384px images, 64 text tokens), arXiv 2606.27708. "
        "Benchmarks are in the paper (the card lists none). Plain transformers (AutoModel/AutoProcessor).",
        args=list(_FASHION_EMBED_COMMON),
    ),
    "nemotron-3.5-embed-1b": ModelSpec(
        id="nemotron-3.5-embed-1b",
        label="Nemotron 3.5 Embed 1B (NVIDIA NIM, text + document image)",
        import_path="tryon.api.nvidia",
        class_name="Nemotron35EmbedAdapter",
        method="embed",
        output_kind="embeddings",
        env_hint="NVIDIA_API_KEY",
        notes=(
            "Hosted NIM nvidia/nemotron-3.5-embed-1b (integrate.api.nvidia.com). "
            "Text and/or image inputs; --input-type query|passage. Local NIM twin: "
            "nemotron-3.5-embed-1b-local (NEMOTRON_EMBED_BASE_URL)."
        ),
        args=[
            Arg(("--text", "-t"), "text", nargs="+", help="Text passage(s) to embed"),
            Arg(("--image", "-i"), "image", nargs="+", help="Document/page image(s)"),
            Arg(("--query", "-q"), "query", help="Text query for cosine scores"),
            Arg(("--query-image",), "query_image", help="Image query for cosine scores"),
            Arg(("--input-type",), "input_type", default="passage", choices=["query", "passage"]),
            Arg(("--modality",), "modality", choices=["text", "image", "text_image"],
                help="Force modality when mixing text and images"),
            Arg(("--dim",), "dimensions", type=int, help="Optional dynamic embedding size"),
            Arg(("--longest-edge",), "longest_edge", type=int,
                help="Image longest edge 256–1540 (default 1120)"),
            Arg(("--endpoint",), "endpoint", target="init", default="nim", choices=["nim"]),
        ],
    ),
    "nemotron-3.5-embed-1b-local": ModelSpec(
        id="nemotron-3.5-embed-1b-local",
        label="Nemotron 3.5 Embed 1B (local NeMo Retriever / vLLM NIM)",
        import_path="tryon.api.nvidia",
        class_name="Nemotron35EmbedAdapter",
        method="embed",
        output_kind="embeddings",
        notes=(
            "Self-hosted OpenAI /v1/embeddings server (NeMo Retriever Embedding NIM or vLLM). "
            "Default NEMOTRON_EMBED_BASE_URL=http://127.0.0.1:8000/v1. "
            "Hosted twin: nemotron-3.5-embed-1b (NVIDIA_API_KEY)."
        ),
        args=[
            Arg(("--text", "-t"), "text", nargs="+", help="Text passage(s) to embed"),
            Arg(("--image", "-i"), "image", nargs="+", help="Document/page image(s)"),
            Arg(("--query", "-q"), "query", help="Text query for cosine scores"),
            Arg(("--query-image",), "query_image", help="Image query for cosine scores"),
            Arg(("--input-type",), "input_type", default="passage", choices=["query", "passage"]),
            Arg(("--modality",), "modality", choices=["text", "image", "text_image"]),
            Arg(("--dim",), "dimensions", type=int, help="Optional dynamic embedding size"),
            Arg(("--longest-edge",), "longest_edge", type=int, help="Image resize longest edge"),
            Arg(("--endpoint",), "endpoint", target="init", default="local", choices=["local"]),
            Arg(("--base-url",), "base_url", target="init", help="Override NEMOTRON_EMBED_BASE_URL"),
        ],
    ),
    "gemini-embedding-2": ModelSpec(
        id="gemini-embedding-2",
        label="Gemini Embedding 2 (Google hosted multimodal embeddings, 3072-d)",
        import_path="tryon.api.gemini", class_name="GeminiEmbeddingAdapter",
        method="embed", output_kind="embeddings", env_hint="GEMINI_API_KEY",
        notes="Hosted (GEMINI_API_KEY): text, images (PNG/JPEG, <=6), audio (MP3/WAV <=180 s), video (MP4/MOV "
        "<=120 s, no audio track) and PDF (1 file, <=6 pages) in ONE embedding space, 100+ languages. Default "
        "3072-d; --dim 128-3072 (768/1536/3072 recommended) is re-normalised. One vector per input by default; "
        "--aggregate fuses all inputs into one (e.g. title + product photo; text then left unprefixed). Text is "
        "task-prefixed for you (--task, --role; the model has no task_type). Not comparable with "
        "gemini-embedding-001 or other models. Vectors saved to .npz; --query / --query-image add cosine scores.",
        args=[
            Arg(("--text", "-t"), "text", nargs="+", help="Text(s) to embed (task-prefixed per --task/--role)"),
            Arg(("--image", "-i"), "image", nargs="+", help="Image(s) to embed (PNG/JPEG; path or URL)"),
            Arg(("--audio",), "audio", nargs="+", help="Audio file(s) (MP3/WAV, <=180 s)"),
            Arg(("--video",), "video", nargs="+", help="Video file(s) (MP4/MOV, <=120 s)"),
            Arg(("--pdf",), "pdf", nargs="+", help="PDF file(s) (<=6 pages each)"),
            Arg(("--query", "-q"), "query", help="Text query; returns cosine scores against every input"),
            Arg(("--query-image",), "query_image", help='Image query ("more like this"); returns cosine scores'),
            Arg(("--task",), "task", default="search result",
                choices=["search result", "question answering", "fact checking", "code retrieval",
                         "classification", "clustering", "sentence similarity"],
                help="Text task prefix (images/audio/video/PDF are never prefixed)"),
            Arg(("--role",), "role", default="document", choices=["document", "query"],
                help="Whether --text items are documents or queries (retrieval tasks only)"),
            Arg(("--dim",), "output_dimensionality", type=int,
                help="Output dimensionality 128-3072 (default 3072; 768/1536/3072 recommended)"),
            Arg(("--aggregate",), "aggregate", action="store_true",
                help="Fuse all inputs into ONE embedding instead of one per input"),
        ],
    ),
    "embeddinggemma-2": ModelSpec(
        id="embeddinggemma-2",
        label="Google EmbeddingGemma 2 (open-weight multimodal embeddings, 768-d)",
        import_path="tryon.models.embeddinggemma", class_name="EmbeddingGemma2Adapter",
        method="embed", output_kind="embeddings", extra="local",
        notes="740M open model (google/embeddinggemma-2): text, code, images, video and audio in one "
        "shared 768-d space, Matryoshka 512/256/128 via --dim. 8,192-token shared context; use "
        "bfloat16/float32, not float16. --modalities loads only needed encoders (text 270M, "
        "text+image 440M, text+audio 570M, full 740M). Vectors saved to .npz; --query adds cosine "
        "scores. Needs sentence-transformers. Apache-2.0 tag (card also links Gemma terms). "
        "Late-interaction alternative: --model pplx-embed-v2-late-0.6b.",
        args=[
            Arg(("--text", "-t"), "text", nargs="+", help="Text(s) to embed (prompted with --task)"),
            Arg(("--image", "-i"), "image", nargs="+", help="Image(s) to embed (path or URL)"),
            Arg(("--audio",), "audio", nargs="+", help="Audio file(s) to embed (mono 16 kHz)"),
            Arg(("--video",), "video", nargs="+", help="Video file(s) to embed (sampled at 1 fps)"),
            Arg(("--query", "-q"), "query", help="Optional search query; returns cosine scores against every input"),
            Arg(("--task",), "task", default="Document",
                choices=["SearchQuery", "Document", "QuestionAnswering", "FactChecking",
                         "CodeRetrieval", "Classification", "Clustering", "SentenceSimilarity"],
                help="Text prompt name (images/audio/video are unprefixed)"),
            Arg(("--dim",), "dim", type=int, choices=[768, 512, 256, 128], help="Matryoshka truncation (re-normalised)"),
            Arg(("--modalities",), "modalities", target="init", default="full",
                choices=["text", "text+image", "text+audio", "full"], help="Which encoders to load"),
            Arg(("--model-id",), "model_id", target="init", help="HF repo id or local path (default google/embeddinggemma-2)"),
            Arg(("--device",), "device", target="init", help="Device override"),
        ],
    ),
    "pplx-embed-v2-late-0.6b": ModelSpec(
        id="pplx-embed-v2-late-0.6b",
        label="Perplexity pplx-embed-v2-late 0.6B (open-weight multi-vector retriever)",
        import_path="tryon.models.pplx_embed", class_name="PplxEmbedLateAdapter",
        method="embed", output_kind="embeddings", extra="local",
        notes="MIT-licensed late-interaction (ColBERT-style) retriever: one 128-d vector per token, "
        "MaxSim scoring, text + images + rendered pages with no OCR. 0.6B shares an embedding space "
        "with the 9B, so a 0.6B query encoder can search a 9B index. No Perplexity-hosted API for "
        "v2-late (their hosted Embeddings API serves the v1 dense models only). Needs "
        "sentence-transformers>=6.0.0. Encode text and images in separate runs for large corpora.",
        args=[
            *_PPLX_EMBED_ARGS,
            Arg(("--variant",), "variant", target="init", default="0.6b", choices=["0.6b"], help="Model size"),
        ],
    ),
    "pplx-embed-v2-late-9b": ModelSpec(
        id="pplx-embed-v2-late-9b",
        label="Perplexity pplx-embed-v2-late 9B (open-weight multi-vector retriever)",
        import_path="tryon.models.pplx_embed", class_name="PplxEmbedLateAdapter",
        method="embed", output_kind="embeddings", extra="local",
        notes="Higher-accuracy 9B (7.4B active) sibling of pplx-embed-v2-late-0.6b (ViDoRe v3 nDCG@10 "
        "65.2 vs 62.3, vendor-reported). Same MaxSim/128-d multi-vector output and shared "
        "embedding space. Large GPU needed (F32 safetensors). MIT.",
        args=[
            *_PPLX_EMBED_ARGS,
            Arg(("--variant",), "variant", target="init", default="9b", choices=["9b"], help="Model size"),
        ],
    ),
}

# --------------------------------------------------------------------------
# classify  (fixed-label image classifiers: safety gating, garment attributes, QC)
# --------------------------------------------------------------------------

_AUDIO_TO_VIDEO = {
    "nvidia-lipsync": ModelSpec(
        id="nvidia-lipsync",
        label="NVIDIA Maxine LipSync NIM (self-hosted gRPC)",
        import_path="tryon.api.nvidia.lipsync_adapter",
        class_name="LipSyncAdapter",
        method="generate_audio_to_video",
        output_kind="video_bytes",
        env_hint="NVIDIA_API_KEY",
        notes=(
            "Lip-sync/dub existing video to new speech audio. No hosted REST — run the LipSync NIM "
            "container and set LIPSYNC_GRPC_TARGET (default 127.0.0.1:8001) plus LIPSYNC_CLIENT_SCRIPT "
            "to nim-clients/lipsync/python/scripts/lipsync.py. Input video: CFR H.264 MP4; audio: WAV/MP3. "
            "Cloud alternative without self-hosting: video-generate --model fal-h3-max-lipsync."
        ),
        args=[
            Arg(("--video",), "video", required=True, help="Source video (local CFR H.264 MP4 path)"),
            Arg(("--audio",), "audio", required=True, help="Speech audio (local WAV or MP3 path)"),
            Arg(
                ("--grpc-target",),
                "grpc_target",
                target="init",
                help="LipSync NIM gRPC host:port (default 127.0.0.1:8001)",
            ),
            Arg(
                ("--client-script",),
                "client_script",
                target="init",
                help="Path to NVIDIA nim-clients lipsync.py script",
            ),
        ],
    ),
}

_GENERATE_3D = {
    "trellis": ModelSpec(
        id="trellis",
        label="Microsoft TRELLIS (NVIDIA NIM, text/image → 3D)",
        import_path="tryon.api.nvidia.trellis_adapter",
        class_name="TrellisMeshAdapter",
        method="generate_text_to_3d",
        output_kind="mesh_bytes",
        alt_method_on_image="generate_image_to_3d",
        alt_image_dest="image",
        env_hint="NVIDIA_API_KEY",
        notes=(
            "Hosted infer: POST ai.api.nvidia.com/v1/genai/microsoft/trellis (NVCF async). "
            "Self-hosted NIM: TRELLIS_INFER_URL=http://127.0.0.1:8000/v1/infer. "
            "Prompt max 77 chars; outputs GLB or STL."
        ),
        args=[
            Arg(("--prompt", "-p"), "prompt", help="Text prompt (≤77 chars; required unless --image)"),
            Arg(("--image", "-i"), "image", help="Reference image (switches to image-to-3D)", alt_only=True),
            Arg(
                ("--output-format",),
                "output_format",
                default="glb",
                choices=["glb", "stl"],
                help="Mesh format",
            ),
            Arg(("--seed",), "seed", type=int, default=0),
            Arg(("--no-texture",), "no_texture", action="store_true", help="Skip texture baking (GLB only)"),
            Arg(("--slat-cfg-scale",), "slat_cfg_scale", type=float),
            Arg(("--ss-cfg-scale",), "ss_cfg_scale", type=float),
            Arg(("--slat-sampling-steps",), "slat_sampling_steps", type=int),
            Arg(("--ss-sampling-steps",), "ss_sampling_steps", type=int),
        ],
    ),
}

_MEASURE = {
    "clad-body-photo": ModelSpec(
        id="clad-body-photo",
        label="Clad body from photo (ISO 8559-1 measurements)",
        import_path="tryon.api.clad",
        class_name="CladBodyApiAdapter",
        method="measure_from_photo",
        output_kind="text",
        env_hint="CLAD_API_KEY",
        notes=(
            "Clad api.clad.you — one photo + height → async body job → ~25 ISO 8559-1 measurements "
            "and optional GLB mesh (--include-mesh). Free tier; key at clad.you/developers."
        ),
        args=[
            _img(("--photo", "-i"), "photo", "Full-body photo (path)", required=True),
            Arg(
                ("--height-cm",),
                "height_cm",
                type=float,
                required=True,
                help="Person height in cm (140–220)",
            ),
            Arg(
                ("--max-wait-time",),
                "max_wait_time",
                type=int,
                default=300,
                help="Seconds to poll async photo job",
            ),
            Arg(
                ("--include-mesh",),
                "include_mesh",
                action="store_true",
                help="Include base64 GLB mesh in JSON (large)",
            ),
        ],
    ),
    "clad-body-questionnaire": ModelSpec(
        id="clad-body-questionnaire",
        label="Clad body from questionnaire (ISO 8559-1 measurements)",
        import_path="tryon.api.clad",
        class_name="CladBodyApiAdapter",
        method="measure_from_questionnaire",
        output_kind="text",
        env_hint="CLAD_API_KEY",
        notes="Eight-question Clad sizing flow → synchronous mesh + measurements (no photo).",
        args=[
            Arg(("--height-cm",), "height_cm", type=float, required=True),
            Arg(("--mass-kg",), "mass_kg", type=float, required=True),
            Arg(
                ("--gender",),
                "gender",
                required=True,
                choices=["female", "male"],
            ),
            Arg(
                ("--body-shape",),
                "body_shape",
                required=True,
                choices=["hourglass", "rectangle", "inverted_triangle", "pear", "apple"],
            ),
            Arg(("--belly",), "belly", type=int, required=True, choices=[1, 2, 3]),
            Arg(("--build",), "build", type=int, required=True, choices=[1, 2, 3]),
            Arg(("--legs",), "legs", type=int, default=2, choices=[1, 2, 3]),
            Arg(("--arms",), "arms", type=int, default=2, choices=[1, 2, 3]),
            Arg(("--cupsize",), "cupsize", help="A–F (female only)"),
            Arg(("--ancestry",), "ancestry", default="mixed"),
            Arg(
                ("--include-mesh",),
                "include_mesh",
                action="store_true",
                help="Include base64 GLB mesh in JSON (large)",
            ),
        ],
    ),
    "clad-body-local": ModelSpec(
        id="clad-body-local",
        label="Clad body local (measure Anny/MHR params)",
        import_path="tryon.models.clad_body",
        class_name="CladBodyLocalAdapter",
        method="measure",
        output_kind="text",
        extra="local",
        notes=(
            "Apache-2.0 clad-body library on existing Anny or MHR param JSON — not photo reconstruction. "
            "Install pip install 'clad-body[anny]' or 'clad-body[mhr]'. Hosted twin: clad-body-photo."
        ),
        args=[
            Arg(
                ("--params",),
                "params",
                required=True,
                help="Path to Anny/MHR params JSON or inline JSON string",
            ),
            Arg(
                ("--preset",),
                "preset",
                choices=["core", "standard", "enhanced", "fitted", "tops", "bottoms", "dresses", "outerwear"],
                help="Measurement preset (cumulative tiers / garment tags)",
            ),
            Arg(
                ("--only",),
                "only",
                nargs="+",
                help="Specific measurement keys (e.g. bust_cm waist_cm hip_cm)",
            ),
            Arg(
                ("--body-backend",),
                "body_backend",
                target="init",
                default="anny",
                choices=["anny", "mhr"],
            ),
        ],
    ),
}

_CLASSIFY = {
    "tryon-safety-classifier": ModelSpec(
        id="tryon-safety-classifier",
        label="Genlook try-on safety classifier (gate garments before try-on, local)",
        import_path="tryon.models.tryon_safety", class_name="TryOnSafetyAdapter",
        method="classify", output_kind="text", extra="local",
        notes="Apache-2.0 SigLIP2-so400m classifier: from ALL photos of ONE product, what a try-on would show -- "
        "level ok/revealing/lingerie/adult, subject, swimwear coverage, ravewear tag, and `blocked` "
        "(P(adult) >= --adult-threshold, default 0.3; use it for the gate). Reported 94.6% four-level accuracy "
        "(5-fold CV, 2,596 products); hardest: sheer lingerie vs adult, festival wear; trained on western "
        "e-commerce photos. Classifies products, not people. Re-implements the model's inference (no remote code "
        "executed); weights pinned to tag v1.0. pip install open_clip_torch safetensors.",
        args=[
            Arg(("--image", "-i"), "image", nargs="+", required=True,
                help="ALL photos of one product (path or URL); more photos -> steadier score"),
            Arg(("--adult-threshold",), "adult_threshold", type=float,
                help="Override the blocked threshold (variant default 0.3)"),
            Arg(("--variant",), "variant", target="init", default="finetuned", choices=["finetuned", "frozen"],
                help="finetuned (~0.9GB, best at catching adult) or frozen (~120KB heads on public SigLIP2)"),
            Arg(("--revision",), "revision", target="init", default="v1.0", help="Hub tag/revision to pin"),
            Arg(("--model-id",), "model_id", target="init",
                help="Hub repo id or local folder (default Genlook/tryon-safety-classifier)"),
            Arg(("--device",), "device", target="init", choices=["cuda", "mps", "cpu"], help="Device (default cuda if available)"),
        ],
    ),
}

_DREAM1_FRAMES_HELP = (
    "Camera frames JSON (path or inline): map each video.* window key to one base64 JPEG "
    "(no data: prefix), e.g. video.overhead, video.wrist_l, video.wrist_r."
)
_DREAM1_OBS_HELP = (
    "Robot observation JSON (path or inline): state.* float arrays, prompt, etc. "
    "See dreamlabs-client docs and docs/docs/api-reference/dream-1.md."
)


def _dream1_robot_act_args(*, checkpoint: str) -> List[Arg]:
    return [
        Arg(("--frames",), "frames", required=True, help=_DREAM1_FRAMES_HELP),
        Arg(("--observation",), "observation", required=True, help=_DREAM1_OBS_HELP),
        Arg(
            ("--policy-config",),
            "policy_config",
            help="Optional JSON (path or inline) merged into policy(): ik, embodiment, strict, timeout_ms, …",
        ),
        Arg(
            ("--checkpoint",),
            "checkpoint",
            target="init",
            default=checkpoint,
            help="Dream checkpoint id (from DreamClient.get_models())",
        ),
    ]


_ROBOT_ACT = {
    "dream-1": ModelSpec(
        id="dream-1",
        label="Dream Labs Dream-1 (World Action Model)",
        import_path="tryon.api.dream_labs",
        class_name="Dream1Adapter",
        method="get_action",
        output_kind="text",
        env_hint="DREAM_API_KEY",
        notes=(
            "Hosted bimanual robot policy API (~1.6s action chunks; $3/hr). Requires pip install "
            "dreamlabs-client. No open weights for this policy — API only. Faster tier: dream-1-flash."
        ),
        args=_dream1_robot_act_args(checkpoint="dreamlabs/dream-1"),
    ),
    "dream-1-flash": ModelSpec(
        id="dream-1-flash",
        label="Dream Labs Dream-1-flash (World Action Model)",
        import_path="tryon.api.dream_labs",
        class_name="Dream1Adapter",
        method="get_action",
        output_kind="text",
        env_hint="DREAM_API_KEY",
        notes="Lighter/faster Dream-1 tier ($2/hr on Dream Labs pricing). Same API contract as dream-1.",
        args=_dream1_robot_act_args(checkpoint="dreamlabs/dream-1-flash"),
    ),
    "cosmos3-nano-droid": ModelSpec(
        id="cosmos3-nano-droid",
        label="Cosmos 3 Nano-DROID policy (certified NIM)",
        import_path="tryon.api.nvidia.cosmos_nano",
        class_name="Cosmos3NanoNimAdapter",
        method="get_action",
        output_kind="text",
        notes=(
            "Self-hosted Cosmos3 NIM with NIM_MODEL_VARIANT=nano-droid, model_mode=policy. "
            "Action-only response (32x8). Image is a 640x540 composed DROID observation. "
            "COSMOS3_NIM_URL default http://127.0.0.1:8010/v1/infer. Not the hosted cosmos3 video API."
        ),
        args=[
            Arg(("--image", "-i"), "image", required=True, help="Composed DROID observation image"),
            Arg(("--prompt", "-p"), "prompt", required=True, help="Task instruction"),
            Arg(("--observation",), "observation", required=True,
                help="JSON with observation/joint_position (7) and observation/gripper_position"),
            Arg(("--action-chunk-size",), "action_chunk_size", type=int, default=32,
                help="Positive multiple of 4 (Nano-DROID default 32)"),
            Arg(("--seed",), "seed", type=int),
            Arg(("--infer-url",), "infer_url", target="init", help="Override COSMOS3_NIM_URL"),
        ],
    ),
}

_DETECT = _moondream_detect_specs()

_PARSE = {
    "nemotron-parse": ModelSpec(
        id="nemotron-parse",
        label="Nemotron Parse (NVIDIA NIM document OCR)",
        import_path="tryon.api.nvidia",
        class_name="NemotronParseAdapter",
        method="parse_document",
        output_kind="text",
        env_hint="NVIDIA_API_KEY",
        notes=(
            "Document/page images → markdown (+ bounding boxes with --tool markdown_bbox). "
            "Model nvidia/nemotron-parse on integrate.api.nvidia.com. "
            "Local NIM: nemotron-parse-local."
        ),
        args=[
            Arg(("--image", "-i"), "image", required=True, help="Document page image (path or URL)"),
            Arg(("--tool",), "tool", default="markdown_bbox",
                choices=["markdown_bbox", "markdown_no_bbox", "detection_only"]),
            Arg(("--max-tokens",), "max_tokens", type=int, help="Max output tokens"),
            Arg(("--endpoint",), "endpoint", target="init", default="nim", choices=["nim"]),
        ],
    ),
    "nemotron-parse-local": ModelSpec(
        id="nemotron-parse-local",
        label="Nemotron Parse (local NIM Docker)",
        import_path="tryon.api.nvidia",
        class_name="NemotronParseAdapter",
        method="parse_document",
        output_kind="text",
        notes=(
            "Nemotron Parse NIM container (default NEMOTRON_PARSE_BASE_URL=http://127.0.0.1:8000/v1). "
            "Hosted twin: nemotron-parse (NVIDIA_API_KEY)."
        ),
        args=[
            Arg(("--image", "-i"), "image", required=True, help="Document page image (path or URL)"),
            Arg(("--tool",), "tool", default="markdown_bbox",
                choices=["markdown_bbox", "markdown_no_bbox", "detection_only"]),
            Arg(("--max-tokens",), "max_tokens", type=int, help="Max output tokens"),
            Arg(("--endpoint",), "endpoint", target="init", default="local", choices=["local"]),
            Arg(("--base-url",), "base_url", target="init", help="Override NEMOTRON_PARSE_BASE_URL"),
        ],
    ),
}

SERVICES: Dict[str, Dict[str, ModelSpec]] = {
    "vton": _VTON,
    "generate": _GENERATE,
    "edit": _EDIT,
    "understand": _UNDERSTAND,
    "video-generate": _VIDEO_GENERATE,
    "audio-to-video": _AUDIO_TO_VIDEO,
    "generate-3d": _GENERATE_3D,
    "bg-remove": _BG_REMOVE,
    "tts": _TTS,
    "decide": _DECIDE,
    "embed": _EMBED,
    "classify": _CLASSIFY,
    "measure": _MEASURE,
    "robot-act": _ROBOT_ACT,
    "detect": _DETECT,
    "parse": _PARSE,
}

SERVICE_HELP = {
    "vton": "Virtual try-on: compose a garment onto a person image",
    "generate": "Text-to-image generation",
    "edit": "Image editing (image + instruction -> image)",
    "understand": "Image understanding / captioning",
    "video-generate": "Text/image-to-video generation",
    "audio-to-video": "Audio-driven video (lip-sync / dubbing)",
    "generate-3d": "Text/image-to-3D mesh generation",
    "bg-remove": "Background removal",
    "tts": "Text-to-speech",
    "decide": "Typed, calibrated decisions (yes/no, choice, score, box, track) via System One models",
    "embed": "Multimodal embeddings (dense or multi-vector) saved to .npz",
    "classify": "Fixed-label image classification (try-on safety gating, garment attributes) with calibrated probabilities",
    "measure": "Body measurements (ISO 8559-1) from photo, questionnaire, or parametric mesh",
    "robot-act": "Robot policy actions from camera frames + proprioception (Dream Labs World Action Models)",
    "detect": "Open-vocabulary detection, pointing, and SVG segmentation",
    "parse": "Document and page image parsing (markdown, layout boxes)",
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
