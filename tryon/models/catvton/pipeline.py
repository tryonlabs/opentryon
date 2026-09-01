"""
CatVTON inference pipeline (SD 1.5 inpainting + skipped cross-attention).

Derived from Zheng-Chong/CatVTON (ICLR 2025), CC BY-NC-SA 4.0:
https://github.com/Zheng-Chong/CatVTON
https://huggingface.co/zhengchong/CatVTON

Used for local OpenTryOn try-on only. Do not use commercially without a
separate license from the CatVTON authors.
"""

from __future__ import annotations

import inspect
import os
from typing import List, Optional, Union

import numpy as np
import PIL.Image
import torch
from torch.nn import functional as F

ATTN_VERSION_FOLDERS = {
    "mix": "mix-48k-1024",
    "vitonhd": "vitonhd-16k-512",
    "dresscode": "dresscode-16k-512",
}


class SkipAttnProcessor(torch.nn.Module):
    def __call__(
        self,
        attn,
        hidden_states,
        encoder_hidden_states=None,
        attention_mask=None,
        temb=None,
        **kwargs,
    ):
        return hidden_states


class AttnProcessor2_0(torch.nn.Module):
    def __init__(self, hidden_size=None, cross_attention_dim=None, **kwargs):
        super().__init__()
        if not hasattr(F, "scaled_dot_product_attention"):
            raise ImportError("CatVTON requires PyTorch 2.0+ (scaled_dot_product_attention).")

    def __call__(
        self,
        attn,
        hidden_states,
        encoder_hidden_states=None,
        attention_mask=None,
        temb=None,
        **kwargs,
    ):
        residual = hidden_states
        if attn.spatial_norm is not None:
            hidden_states = attn.spatial_norm(hidden_states, temb)
        input_ndim = hidden_states.ndim
        if input_ndim == 4:
            batch_size, channel, height, width = hidden_states.shape
            hidden_states = hidden_states.view(batch_size, channel, height * width).transpose(1, 2)
        batch_size, sequence_length, _ = (
            hidden_states.shape if encoder_hidden_states is None else encoder_hidden_states.shape
        )
        if attention_mask is not None:
            attention_mask = attn.prepare_attention_mask(attention_mask, sequence_length, batch_size)
            attention_mask = attention_mask.view(batch_size, attn.heads, -1, attention_mask.shape[-1])
        if attn.group_norm is not None:
            hidden_states = attn.group_norm(hidden_states.transpose(1, 2)).transpose(1, 2)
        query = attn.to_q(hidden_states)
        if encoder_hidden_states is None:
            encoder_hidden_states = hidden_states
        elif attn.norm_cross:
            encoder_hidden_states = attn.norm_encoder_hidden_states(encoder_hidden_states)
        key = attn.to_k(encoder_hidden_states)
        value = attn.to_v(encoder_hidden_states)
        inner_dim = key.shape[-1]
        head_dim = inner_dim // attn.heads
        query = query.view(batch_size, -1, attn.heads, head_dim).transpose(1, 2)
        key = key.view(batch_size, -1, attn.heads, head_dim).transpose(1, 2)
        value = value.view(batch_size, -1, attn.heads, head_dim).transpose(1, 2)
        hidden_states = F.scaled_dot_product_attention(
            query, key, value, attn_mask=attention_mask, dropout_p=0.0, is_causal=False
        )
        hidden_states = hidden_states.transpose(1, 2).reshape(batch_size, -1, attn.heads * head_dim)
        hidden_states = hidden_states.to(query.dtype)
        hidden_states = attn.to_out[0](hidden_states)
        hidden_states = attn.to_out[1](hidden_states)
        if input_ndim == 4:
            hidden_states = hidden_states.transpose(-1, -2).reshape(batch_size, channel, height, width)
        if attn.residual_connection:
            hidden_states = hidden_states + residual
        return hidden_states / attn.rescale_output_factor


def _init_adapter(unet) -> torch.nn.ModuleList:
    cross_attn_dim = unet.config.cross_attention_dim
    attn_procs = {}
    for name in unet.attn_processors.keys():
        is_self = name.endswith("attn1.processor")
        if name.startswith("mid_block"):
            hidden_size = unet.config.block_out_channels[-1]
        elif name.startswith("up_blocks"):
            block_id = int(name[len("up_blocks.")])
            hidden_size = list(reversed(unet.config.block_out_channels))[block_id]
        elif name.startswith("down_blocks"):
            block_id = int(name[len("down_blocks.")])
            hidden_size = unet.config.block_out_channels[block_id]
        else:
            hidden_size = unet.config.block_out_channels[-1]
        if is_self:
            attn_procs[name] = AttnProcessor2_0(
                hidden_size=hidden_size, cross_attention_dim=None
            )
        else:
            attn_procs[name] = SkipAttnProcessor()
    unet.set_attn_processor(attn_procs)
    return torch.nn.ModuleList(unet.attn_processors.values())


def _attn_modules(unet) -> torch.nn.ModuleList:
    blocks = torch.nn.ModuleList()
    for name, module in unet.named_modules():
        if "attn1" in name:
            blocks.append(module)
    return blocks


def _resize_and_crop(image: PIL.Image.Image, size):
    w, h = image.size
    target_w, target_h = size
    if w / h < target_w / target_h:
        new_w, new_h = w, w * target_h // target_w
    else:
        new_h, new_w = h, h * target_w // w
    image = image.crop(((w - new_w) // 2, (h - new_h) // 2, (w + new_w) // 2, (h + new_h) // 2))
    return image.resize(size, PIL.Image.LANCZOS)


def _resize_and_padding(image: PIL.Image.Image, size):
    w, h = image.size
    target_w, target_h = size
    if w / h < target_w / target_h:
        new_h = target_h
        new_w = w * target_h // h
    else:
        new_w = target_w
        new_h = h * target_w // w
    image = image.resize((new_w, new_h), PIL.Image.LANCZOS)
    padding = PIL.Image.new("RGB", size, (255, 255, 255))
    padding.paste(image, ((target_w - new_w) // 2, (target_h - new_h) // 2))
    return padding


def _prepare_image(image) -> torch.Tensor:
    if isinstance(image, torch.Tensor):
        if image.ndim == 3:
            image = image.unsqueeze(0)
        return image.to(dtype=torch.float32)
    if isinstance(image, PIL.Image.Image):
        image = [image]
    arr = np.concatenate([np.array(i.convert("RGB"))[None, :] for i in image], axis=0)
    tensor = torch.from_numpy(arr.transpose(0, 3, 1, 2)).to(dtype=torch.float32) / 127.5 - 1.0
    return tensor


def _prepare_mask(mask_image) -> torch.Tensor:
    if isinstance(mask_image, torch.Tensor):
        mask = mask_image.float()
        if mask.ndim == 2:
            mask = mask.unsqueeze(0).unsqueeze(0)
        elif mask.ndim == 3:
            mask = mask.unsqueeze(1) if mask.shape[0] != 1 else mask.unsqueeze(0)
        mask = (mask >= 0.5).float()
        return mask
    if isinstance(mask_image, PIL.Image.Image):
        mask_image = [mask_image]
    arr = np.concatenate([np.array(m.convert("L"))[None, None, :] for m in mask_image], axis=0)
    arr = (arr.astype(np.float32) / 255.0 >= 0.5).astype(np.float32)
    return torch.from_numpy(arr)


def _numpy_to_pil(images: np.ndarray) -> List[PIL.Image.Image]:
    if images.ndim == 3:
        images = images[None, ...]
    images = (images * 255).round().astype("uint8")
    return [PIL.Image.fromarray(image) for image in images]


def _vae_encode(image: torch.Tensor, vae) -> torch.Tensor:
    pixel_values = image.to(memory_format=torch.contiguous_format).float()
    pixel_values = pixel_values.to(vae.device, dtype=vae.dtype)
    with torch.no_grad():
        latents = vae.encode(pixel_values).latent_dist.sample()
    return latents * vae.config.scaling_factor


class CatVTONPipeline:
    """Official CatVTON concatenation pipeline (person || garment, skip text)."""

    def __init__(
        self,
        base_ckpt: str,
        attn_ckpt: str,
        attn_ckpt_version: str = "mix",
        weight_dtype=None,
        device: str = "cuda",
        use_tf32: bool = True,
    ):
        from accelerate import load_checkpoint_in_model
        from diffusers import AutoencoderKL, DDIMScheduler, UNet2DConditionModel
        from huggingface_hub import snapshot_download

        if weight_dtype is None:
            weight_dtype = torch.float16
        self.device = device
        self.weight_dtype = weight_dtype
        self.noise_scheduler = DDIMScheduler.from_pretrained(base_ckpt, subfolder="scheduler")
        self.vae = AutoencoderKL.from_pretrained("stabilityai/sd-vae-ft-mse").to(
            device, dtype=weight_dtype
        )
        self.unet = UNet2DConditionModel.from_pretrained(base_ckpt, subfolder="unet").to(
            device, dtype=weight_dtype
        )
        _init_adapter(self.unet)
        attn_modules = _attn_modules(self.unet)
        if attn_ckpt_version not in ATTN_VERSION_FOLDERS:
            raise ValueError(
                f"Unknown attn version '{attn_ckpt_version}'. "
                f"Use one of {sorted(ATTN_VERSION_FOLDERS)}"
            )
        sub_folder = ATTN_VERSION_FOLDERS[attn_ckpt_version]
        if os.path.isdir(attn_ckpt):
            ckpt_dir = os.path.join(attn_ckpt, sub_folder, "attention")
        else:
            repo_path = snapshot_download(repo_id=attn_ckpt)
            ckpt_dir = os.path.join(repo_path, sub_folder, "attention")
        load_checkpoint_in_model(attn_modules, ckpt_dir)
        if use_tf32 and torch.cuda.is_available():
            torch.set_float32_matmul_precision("high")
            torch.backends.cuda.matmul.allow_tf32 = True

    def _extra_step_kwargs(self, generator, eta: float):
        extra = {}
        params = inspect.signature(self.noise_scheduler.step).parameters
        if "eta" in params:
            extra["eta"] = eta
        if "generator" in params:
            extra["generator"] = generator
        return extra

    @torch.no_grad()
    def __call__(
        self,
        image: Union[PIL.Image.Image, torch.Tensor],
        condition_image: Union[PIL.Image.Image, torch.Tensor],
        mask: Union[PIL.Image.Image, torch.Tensor],
        num_inference_steps: int = 50,
        guidance_scale: float = 2.5,
        height: int = 1024,
        width: int = 768,
        generator: Optional[torch.Generator] = None,
        eta: float = 1.0,
    ) -> List[PIL.Image.Image]:
        from diffusers.utils.torch_utils import randn_tensor

        concat_dim = -2
        if not isinstance(image, torch.Tensor):
            image = _resize_and_crop(image.convert("RGB"), (width, height))
            mask = _resize_and_crop(mask.convert("L"), (width, height))
            condition_image = _resize_and_padding(condition_image.convert("RGB"), (width, height))
        image_t = _prepare_image(image).to(self.device, dtype=self.weight_dtype)
        cloth_t = _prepare_image(condition_image).to(self.device, dtype=self.weight_dtype)
        mask_t = _prepare_mask(mask).to(self.device, dtype=self.weight_dtype)
        masked_image = image_t * (mask_t < 0.5)
        masked_latent = _vae_encode(masked_image, self.vae)
        condition_latent = _vae_encode(cloth_t, self.vae)
        mask_latent = torch.nn.functional.interpolate(
            mask_t, size=masked_latent.shape[-2:], mode="nearest"
        )
        masked_latent_concat = torch.cat([masked_latent, condition_latent], dim=concat_dim)
        mask_latent_concat = torch.cat([mask_latent, torch.zeros_like(mask_latent)], dim=concat_dim)
        latents = randn_tensor(
            masked_latent_concat.shape,
            generator=generator,
            device=masked_latent_concat.device,
            dtype=self.weight_dtype,
        )
        self.noise_scheduler.set_timesteps(num_inference_steps, device=self.device)
        latents = latents * self.noise_scheduler.init_noise_sigma
        do_cfg = guidance_scale > 1.0
        if do_cfg:
            masked_latent_concat = torch.cat(
                [
                    torch.cat([masked_latent, torch.zeros_like(condition_latent)], dim=concat_dim),
                    masked_latent_concat,
                ]
            )
            mask_latent_concat = torch.cat([mask_latent_concat] * 2)
        extra_step_kwargs = self._extra_step_kwargs(generator, eta)
        for t in self.noise_scheduler.timesteps:
            latent_in = torch.cat([latents] * 2) if do_cfg else latents
            latent_in = self.noise_scheduler.scale_model_input(latent_in, t)
            unet_in = torch.cat([latent_in, mask_latent_concat, masked_latent_concat], dim=1)
            noise_pred = self.unet(
                unet_in,
                t.to(self.device),
                encoder_hidden_states=None,
                return_dict=False,
            )[0]
            if do_cfg:
                noise_uncond, noise_text = noise_pred.chunk(2)
                noise_pred = noise_uncond + guidance_scale * (noise_text - noise_uncond)
            latents = self.noise_scheduler.step(
                noise_pred, t, latents, **extra_step_kwargs
            ).prev_sample
        latents = latents.split(latents.shape[concat_dim] // 2, dim=concat_dim)[0]
        latents = 1 / self.vae.config.scaling_factor * latents
        decoded = self.vae.decode(latents.to(self.device, dtype=self.weight_dtype)).sample
        decoded = (decoded / 2 + 0.5).clamp(0, 1)
        decoded = decoded.cpu().permute(0, 2, 3, 1).float().numpy()
        return _numpy_to_pil(decoded)
