# Virtual Try-On Demo

A modern, full-stack virtual try-on application featuring a Next.js frontend and FastAPI backend. Generate realistic virtual try-on images using state-of-the-art AI models including Nano Banana, Nano Banana Pro, FLUX 2 Pro, and FLUX 2 Flex.

## 🎯 Features

- **🖼️ Modern UI**: Beautiful, responsive Next.js interface with drag & drop support
- **🤖 Multiple AI Models**: Choose from 4 powerful image generation models
  - **Nano Banana**: Fast, efficient (Gemini 2.5 Flash) - 1024px
  - **Nano Banana Pro**: Advanced (Gemini 3 Pro) - up to 4K with search grounding
  - **FLUX 2 Pro**: High-quality professional results
  - **FLUX 2 Flex**: Flexible with advanced controls (guidance, steps, prompt upsampling)
- **📤 Multi-Image Upload**: Upload model image + multiple garment images
- **💰 Cost Estimation**: Real-time credit calculation based on resolution and image count
- **🔄 Live Processing**: View generation progress and results
- **📱 Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices

## 🏗️ Architecture

The demo consists of two components:

1. **Frontend (Next.js 15)**
   - Located in `demo/virtual-tryon/`
   - Modern React/TypeScript application
   - Tailwind CSS for styling
   - Real-time API communication

2. **Backend (FastAPI)**
   - Located in project root: `api_server.py`
   - Uses OpenTryOn API SDK (`tryon.api`)
   - Supports 4 model providers
   - Automatic image processing and storage

## 🚀 Quick Start

### Prerequisites

- **Backend Requirements**:
  - Python 3.10+
  - FastAPI 0.124.0
  - Uvicorn 0.38.0
  - OpenTryOn installed (`pip install -e .`)
  
- **Frontend Requirements**:
  - Node.js 18+
  - npm or yarn

- **API Keys** (at least one required):
  - `GEMINI_API_KEY` for Nano Banana models
  - `BFL_API_KEY` for FLUX 2 models

### Step 1: Set Up Environment

Create a `.env` file in the project root:

```bash
# Google Gemini (for Nano Banana models)
GEMINI_API_KEY=your_gemini_api_key

# Black Forest Labs (for FLUX 2 models)
BFL_API_KEY=your_bfl_api_key
```

### Step 2: Start the Backend

From the project root:

```bash
# Activate your environment
conda activate opentryon  # or source venv/bin/activate

# Start the FastAPI server
python api_server.py
```

The API server will start at `http://localhost:8000`

**API Health Check**:
```bash
curl http://localhost:8000/health
```

### Step 3: Start the Frontend

In a new terminal:

```bash
cd demo/virtual-tryon
npm install
npm run dev
```

The frontend will start at `http://localhost:3000`

### Step 4: Try It Out!

1. Open `http://localhost:3000` in your browser
2. Select a model (Nano Banana, Nano Banana Pro, FLUX 2 Pro, or FLUX 2 Flex)
3. Upload a model/person image
4. Upload garment images (shirts, pants, accessories, etc.)
5. Click "Generate" and wait for the AI-generated result!

## 📁 Project Structure

```
demo/virtual-tryon/
├── app/
│   ├── layout.tsx              # Root layout with metadata
│   ├── page.tsx                # Main UI component with generation logic
│   └── globals.css             # Global styles and Tailwind config
├── components/
│   ├── ui/                     # Reusable UI components
│   │   ├── button.tsx
│   │   └── card.tsx
│   ├── image-upload.tsx        # Single image upload
│   └── multi-image-upload.tsx  # Multiple image upload
├── lib/
│   └── utils.ts                # Utility functions
├── pricing_config.json         # Credit pricing configuration
└── README.md                   # This file

../../api_server.py              # FastAPI backend server
```

## 🎨 Tech Stack

### Frontend
- **Next.js 15** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS 3.4** - Utility-first CSS
- **React Dropzone** - Drag & drop uploads
- **React Icons** - Icon library

### Backend
- **FastAPI 0.124.0** - Modern Python web framework
- **Uvicorn 0.38.0** - ASGI server
- **OpenTryOn SDK** - AI model adapters
  - `NanoBananaAdapter`
  - `NanoBananaProAdapter`
  - `Flux2ProAdapter`
  - `Flux2FlexAdapter`

## 🔧 API Server Details

The backend (`api_server.py`) provides a REST API for virtual try-on generation.

### Endpoints

#### `POST /api/v1/virtual-tryon`

Generate virtual try-on images.

**Parameters**:
- `model_image` (file, required): Model/person image
- `garment_images` (files, required): One or more garment images
- `provider` (string, optional): Model to use
  - `nano-banana` (default) - Fast, 1024px
  - `nano-banana-pro` - Advanced, up to 4K
  - `flux-2-pro` - High quality
  - `flux-2-flex` - Advanced controls
- `prompt` (string, optional): Custom generation prompt
- `resolution` (string, optional): For nano-banana-pro: `1K`, `2K`, or `4K`
- `aspect_ratio` (string, optional): e.g., `16:9`, `1:1`
- Additional FLUX 2 parameters: `width`, `height`, `seed`, `guidance`, `steps`, `safety_tolerance`

**Response**:
```json
{
  "success": true,
  "image": "data:image/png;base64,...",
  "provider": "nano-banana",
  "num_garments": 2,
  "saved_path": "outputs/virtual_tryon/tryon_nano-banana_20250119_143022.png",
  "filename": "tryon_nano-banana_20250119_143022.png",
  "model_dimensions": {"width": 838, "height": 1176}
}
```

#### `GET /health`

Health check endpoint.

**Response**:
```json
{
  "status": "healthy"
}
```

### CORS Configuration

The API server allows requests from:
- `http://localhost:3000` (Next.js dev server)
- `http://127.0.0.1:3000`

## 💳 Pricing Configuration

Credits are calculated dynamically based on:
- **Model provider** (different pricing strategies)
- **Image resolution** (higher resolution = more credits)
- **Number of images** (model image + garment images)

Edit `pricing_config.json` to customize pricing for each model.

## 🔍 Usage Example

### Using curl:

```bash
curl -X POST "http://localhost:8000/api/v1/virtual-tryon" \
  -F "model_image=@person.jpg" \
  -F "garment_images=@shirt.jpg" \
  -F "garment_images=@jeans.jpg" \
  -F "provider=nano-banana-pro" \
  -F "resolution=2K"
```

### Using Python:

```python
import requests

url = "http://localhost:8000/api/v1/virtual-tryon"

files = {
    'model_image': open('person.jpg', 'rb'),
    'garment_images': [
        open('shirt.jpg', 'rb'),
        open('jeans.jpg', 'rb')
    ]
}

data = {
    'provider': 'flux-2-pro'
}

response = requests.post(url, files=files, data=data)
result = response.json()

if result['success']:
    print(f"Image saved to: {result['saved_path']}")
```

## 🎯 Model Comparison

| Model | Speed | Quality | Max Resolution | Special Features |
|-------|-------|---------|----------------|------------------|
| **Nano Banana** | ⚡⚡⚡ Fast | ⭐⭐⭐ Good | 1024px | Efficient, low cost |
| **Nano Banana Pro** | ⚡⚡ Medium | ⭐⭐⭐⭐ Great | 4K | Search grounding, high resolution |
| **FLUX 2 Pro** | ⚡ Slow | ⭐⭐⭐⭐⭐ Excellent | Custom | Professional quality |
| **FLUX 2 Flex** | ⚡ Slow | ⭐⭐⭐⭐⭐ Excellent | Custom | Advanced controls, fine-tuning |

## 🐛 Troubleshooting

### "Failed to fetch" Error

**Cause**: Frontend cannot connect to backend

**Solutions**:
1. Ensure API server is running: `python api_server.py`
2. Check if port 8000 is available: `lsof -i :8000`
3. Verify API URL in frontend (should be `http://localhost:8000`)
4. Check browser console (F12) for detailed errors

### API Key Errors

**Error**: `No API key provided` or `Invalid API key`

**Solution**: 
1. Add API keys to `.env` file in project root
2. Restart the API server to load new environment variables

### Import Errors

**Error**: `ModuleNotFoundError: No module named 'tryon'`

**Solution**: Install OpenTryOn in development mode:
```bash
pip install -e .
```

## 📚 Learn More

- **[OpenTryOn Documentation](https://tryonlabs.github.io/opentryon/)** - Full documentation
- **[API Reference](../../README_API_SERVER.md)** - Detailed API server documentation
- **[Main README](../../README.md)** - OpenTryOn overview and installation

## 🚀 Production Deployment

### Backend (API Server)

Deploy using uvicorn or gunicorn:

```bash
# Using uvicorn
uvicorn api_server:app --host 0.0.0.0 --port 8000 --workers 4

# Using gunicorn with uvicorn workers
gunicorn api_server:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Frontend (Next.js)

Build and deploy:

```bash
npm run build
npm start
```

Or deploy to Vercel:

```bash
vercel deploy
```

Don't forget to set `NEXT_PUBLIC_API_URL` environment variable to your production API URL.

## 📄 License

This project is part of the OpenTryOn repository and follows the same license (CC BY-NC 4.0).

