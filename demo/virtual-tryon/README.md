# TryOn AI: Virtual Try-On Demo

A modern Next.js application for virtual try-on of fashion garments. Built with Next.js 15, Tailwind CSS, and TypeScript.

## Features

- 🖼️ **Model Image Upload**: Upload and preview a single model/person image
- 👕 **Multiple Garment Upload**: Upload multiple garment images (top, jeans, scarf, hat, glasses, etc.) with drag & drop support
- ✨ **Virtual Try-On Result**: View the generated try-on result
- 🎨 **Modern UI**: Beautiful, responsive design matching the fashion-prompt-builder style
- 📱 **Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices

## Tech Stack

- **Next.js 15** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS 3.4** - Utility-first CSS framework
- **React Dropzone** - Drag & drop file upload functionality
- **React Icons** - Icon library

## Getting Started

### Prerequisites

- Node.js 18+ installed
- npm or yarn package manager

### Installation

1. Navigate to the project directory:
```bash
cd demo/virtual-tryon
```

2. Install dependencies:
```bash
npm install
```

3. Run the development server:
```bash
npm run dev
```

4. Open [http://localhost:3000](http://localhost:3000) in your browser

## Project Structure

```
virtual-tryon/
├── app/
│   ├── layout.tsx          # Root layout with metadata
│   ├── page.tsx            # Main page component
│   └── globals.css         # Global styles and Tailwind configuration
├── components/
│   ├── ui/                 # Reusable UI components
│   │   ├── button.tsx      # Button component
│   │   └── card.tsx        # Card components
│   ├── image-upload.tsx    # Single image upload component
│   └── multi-image-upload.tsx # Multiple image upload component
├── lib/
│   └── utils.ts            # Utility functions (cn helper)
└── public/                  # Static assets
```

## Usage

1. **Upload Model Image**: Click or drag & drop a model/person image in the first section
2. **Upload Garments**: Click or drag & drop multiple garment images in the second section
3. **Generate**: Click the "Generate Try-On" button to process the images
4. **View Result**: The result will appear in the third section

## Design System

The application uses the same design system as the fashion-prompt-builder:

- **Primary Color**: `#1FA08F` (Teal)
- **Secondary Color**: `#486876` (Slate)
- **Font**: Inter
- **Components**: Consistent card, button, and input styling

## Future Enhancements

- [ ] Integrate with FastAPI backend for actual try-on processing
- [ ] Add image preview zoom functionality
- [ ] Support for more image formats
- [ ] Add image editing capabilities (crop, rotate)
- [ ] Save and load previous try-on sessions
- [ ] Share try-on results

## Development

### Build for Production

```bash
npm run build
npm start
```

### Linting

```bash
npm run lint
```

## License

This project is part of the OpenTryOn repository.

