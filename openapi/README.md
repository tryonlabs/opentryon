# OpenTryOn Media OpenAPI / Swagger

This folder holds an OpenAPI 3 snapshot of the **upstream** media endpoints
wired into OpenTryOn adapters (as of **v0.0.3**):

- BytePlus ModelArk — Seedance video + Seedream image
- Kling AI Open Platform — video 3.0 / Omni / Turbo
- Luma Agents API — Ray 3.2
- xAI — Grok Imagine Image + Video 1.5
- Ideogram — 4.0 generate
- Pruna — `/v1/predictions` + `/v1/files` (p-image, p-image-edit, p-image-upscale, p-video, p-video-replace, p-video-avatar, p-video-animate, p-image-try-on)

Companion Postman collection: [`../postman/opentryon-media.postman_collection.json`](../postman/opentryon-media.postman_collection.json).

Docs page: [OpenAPI & Postman](https://tryonlabs.github.io/opentryon/docs/getting-started/openapi-swagger).

## View in Swagger UI

```bash
npx @redocly/cli preview-docs openapi/opentryon-media.openapi.yaml
# or import into https://editor.swagger.io /
# or Postman: File → Import → openapi/opentryon-media.openapi.yaml
```

The FastAPI demo server (`api_server.py`) still exposes its own `/docs`
Swagger UI for the legacy VTON demo endpoint. The CLI/MCP registry is the
source of truth for all models; this OpenAPI file is a convenience for
provider-level debugging and Postman/Swagger dashboards.
