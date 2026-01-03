import torch
from PIL import Image
import io
import os
import requests
import warnings
import huggingface_hub
from typing import Union, List
from tryon.api.ben2.modeling_ben2 import BEN_Base


DEFAULT_WEIGHTS_PATH = "tryon/api/ben2/BEN2_Base.pth"
HF_REPO = "PramaLLC/BEN2"
HF_FILENAME = "BEN2_Base.pth"


def configure_device_and_warnings():
    """
    Ensures:
      - CUDA used only if available
      - autocast safe on CPU (no warnings)
      - harmless deprecation warnings silenced
    """
    use_cuda = torch.cuda.is_available()
    device = "cuda" if use_cuda else "cpu"

    warnings.filterwarnings("ignore", message="TypedStorage is deprecated")

    if use_cuda:
        from torch.cuda.amp import autocast
    else:
        # dummy autocast for CPU
        from contextlib import contextmanager
        @contextmanager
        def autocast(*args, **kwargs):
            yield

    return device, autocast


class BEN2BackgroundRemoverAdapter:
    def __init__(self, weights_path=None, device=None):
        configured_device, self.autocast = configure_device_and_warnings()
        self.device = device or configured_device

        self.weights_path = weights_path or DEFAULT_WEIGHTS_PATH
        self.ensure_weights()

        self.model = BEN_Base().to(self.device).eval()
        self.model.loadcheckpoints(self.weights_path)

    def ensure_weights(self):
        os.makedirs(os.path.dirname(self.weights_path), exist_ok=True)

        if not os.path.exists(self.weights_path):
            print("Downloading BEN2 weights... This may take a while.")
            huggingface_hub.hf_hub_download(
                repo_id=HF_REPO,
                filename=HF_FILENAME,
                local_dir=os.path.dirname(self.weights_path),
                local_dir_use_symlinks=False
            )
            print("Download complete.")

    def load_image(self, input_data: Union[str, io.BytesIO, Image.Image]) -> Image.Image:
        """
        Normalizes ANY supported input into a valid PIL Image (RGB).
        Supports:
            - URL (http/https)
            - Local file path
            - BytesIO / file-like
            - PIL Image
        """
        # URL
        if isinstance(input_data, str) and input_data.startswith(("http://", "https://")):
            resp = requests.get(input_data, timeout=10)
            resp.raise_for_status()
            image = Image.open(io.BytesIO(resp.content))

        # Local file
        elif isinstance(input_data, str) and os.path.exists(input_data):
            image = Image.open(input_data)

        # BytesIO / file-like
        elif hasattr(input_data, "read"):
            input_data.seek(0)
            image = Image.open(input_data)

        # Already PIL
        elif isinstance(input_data, Image.Image):
            image = input_data

        else:
            raise ValueError("Unsupported image input type")

        if image.mode != "RGB":
            image = image.convert("RGB")

        return image


    def remove_background(
        self,
        image: Union[str, io.BytesIO, Image.Image],
        refine: bool = False
    ) -> List[Image.Image]:

        pil = self.load_image(image)

        with self.autocast():
            result = self.model.inference(pil, refine_foreground=refine)

        return [result]


    def remove_background_batch(
        self,
        images: List[Union[str, io.BytesIO, Image.Image]],
        refine: bool = False
    ) -> List[Image.Image]:

        if not isinstance(images, (list, tuple)) or len(images) == 0:
            raise ValueError("images must be a non-empty list")

        results = []

        for img in images:
            pil = self.load_image(img)
            with self.autocast():
                out = self.model.inference(pil, refine_foreground=refine)
            results.append(out)

        return results
