# Demos

OpenTryOn includes in-repo **Gradio** demos for quick experiments. The current web playground is **TryOn Studio**, which talks to OpenTryOn over MCP — it is not in this repository.

## TryOn Studio (recommended UI)

[TryOn Studio](https://github.com/tryonlabs/tryon-studio) is a Next.js MCP client: Agent chat, Connect, Image generate/edit, VTON, Understand, Video, and background removal.

**Quick start** (two processes):

1. Start the MCP server from this repo:

```bash
cd mcp-server
python server.py --transport http --host 127.0.0.1 --port 8000
```

2. In another terminal, start Studio:

```bash
cd tryon-studio
cp .env.local.example .env.local
npm install
npm run dev
```

Open [http://localhost:3000/connect](http://localhost:3000/connect) first.

**[Full setup and screen tour →](../getting-started/tryon-studio)** · **[MCP Server →](../getting-started/mcp)**

---

## Gradio demos (in this repo)

### Extract Garment

Interactive Gradio demo for garment extraction.

```bash
python run_demo.py --name extract_garment
```

**[Read More →](./extract-garment)**

### Model Swap

Interactive Gradio demo for swapping garments between models.

```bash
python run_demo.py --name model_swap
```

**[Read More →](./model-swap)**

### Outfit Generator

Interactive Gradio demo for generating outfits from text prompts.

```bash
python run_demo.py --name outfit_generator
```

**[Read More →](./outfit-generator)**

---

## Demo comparison

| Demo | Type | Where | Use case |
|------|------|-------|----------|
| **TryOn Studio** | Next.js MCP client | [tryon-studio](https://github.com/tryonlabs/tryon-studio) | Agent + all registry capabilities |
| **Extract Garment** | Gradio | `demo/extract_garment` | Quick garment extraction |
| **Model Swap** | Gradio | `demo/model_swap` | Garment swapping experiments |
| **Outfit Generator** | Gradio | `demo/outfit_generator` | Text-to-outfit generation |

