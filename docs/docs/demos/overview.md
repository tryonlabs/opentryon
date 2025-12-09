# Demos

OpenTryOn includes interactive demos for easy experimentation and testing.

## Available Demos

### Virtual Try-On Demo (Full-Stack Web App) ⭐ NEW

A modern, production-ready virtual try-on web application with FastAPI backend and Next.js frontend.

**Features**:
- Support for 4 AI models (Nano Banana, Nano Banana Pro, FLUX 2 Pro, FLUX 2 Flex)
- Multi-image upload with drag & drop
- Real-time credit estimation
- Modern, responsive UI
- RESTful API

**Quick Start**:

1. Start the backend:
```bash
python api_server.py
```

2. In a new terminal, start the frontend:
```bash
cd demo/virtual-tryon
npm install
npm run dev
```

3. Open `http://localhost:3000` in your browser

**[Read Full Documentation →](./virtual-tryon)**

---

### Extract Garment Demo (Gradio)

Interactive Gradio demo for garment extraction.

```bash
python run_demo.py --name extract_garment
```

**[Read More →](./extract-garment)**

### Model Swap Demo (Gradio)

Interactive Gradio demo for swapping garments between models.

```bash
python run_demo.py --name model_swap
```

**[Read More →](./model-swap)**

### Outfit Generator Demo (Gradio)

Interactive Gradio demo for generating outfits from text prompts.

```bash
python run_demo.py --name outfit_generator
```

**[Read More →](./outfit-generator)**

---

## Demo Comparison

| Demo | Type | Tech Stack | Use Case |
|------|------|------------|----------|
| **Virtual Try-On** | Full-stack Web App | Next.js + FastAPI | Production-ready virtual try-on with multiple AI models |
| **Extract Garment** | Gradio | Python + Gradio | Quick garment extraction testing |
| **Model Swap** | Gradio | Python + Gradio | Garment swapping experiments |
| **Outfit Generator** | Gradio | Python + Gradio | Text-to-outfit generation |

