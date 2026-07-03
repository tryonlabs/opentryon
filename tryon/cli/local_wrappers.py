"""
Thin adapter-shaped wrappers around local-inference helpers that don't
already expose an adapter class, so the CLI registry can treat every
model uniformly as "a class with a method to call".
"""

DEFAULT_UNDERSTAND_PROMPT = (
    "You're a fashion expert. Describe the outfit shown in the image, "
    "including color, pattern, style, fit, type, and material."
)


class LlavaNextUnderstandAdapter:
    """
    CLI-friendly wrapper around ``tryon.preprocessing.captioning``'s
    LLaVA-NeXT pipeline for image understanding / captioning.

    Requires a CUDA GPU (the underlying pipeline hard-codes ``cuda:0``)
    and the ``local`` extra (``pip install opentryon[local]``).
    """

    def __init__(self):
        from tryon.preprocessing.captioning import create_llava_next_pipeline

        self.model, self.processor = create_llava_next_pipeline()

    def understand(self, image, prompt: str = None, json_only: bool = False) -> dict:
        from PIL import Image as PILImage

        from tryon.preprocessing.captioning import caption_image

        if isinstance(image, str):
            image = PILImage.open(image)

        json_data, caption = caption_image(
            image,
            prompt or DEFAULT_UNDERSTAND_PROMPT,
            self.model,
            self.processor,
            json_only=json_only,
        )
        return {"caption": caption, "json": json_data}
