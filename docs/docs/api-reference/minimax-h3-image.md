---
title: MiniMax H3 Image
---

Generate images from a text prompt with `MiniMaxH3ImageAdapter`. Set
`MINIMAX_API_KEY` for your region. The default host is `https://api.minimax.io`.
For a mainland China key, set `MINIMAX_API_BASE_URL=https://api.minimax.cn`.

```bash
opentryon generate --model minimax-h3-image --prompt "A linen jacket on a hanger"
opentryon generate --model minimax-h3-image --model-version MiniMax-H3-Image-Highspeed \
  --prompt "A handwoven scarf" --size 2720x1536 --n 2
```

The default model is `MiniMax-H3-Image`. With the default URL response, the
adapter downloads successful images before their links expire. Use
`--response-format b64_json` to receive image bytes in the generation response.
The CLI saves the images as PNG files in the output directory. For a mixed
result, it saves successful images and warns about each failed image.

Generation waits up to 600 seconds for a response. Each submitted request can
incur a charge, even if the client disconnects. The adapter sends it once.

See the [global API reference](https://platform.minimax.io/docs/api-reference/image-generation-h3-generations)
or the [mainland China reference](https://platform.minimax.cn/docs/api-reference/image-generation-h3-generations).
