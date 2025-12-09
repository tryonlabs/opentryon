# Fashion Model Prompt Builder - Next.js Application

A modern, responsive web application for generating prompts for fashion model generation. Built with Next.js 14, Tailwind CSS, and TypeScript.

## Quick Start

```bash
cd demo/fashion-prompt-builder
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to see the application.

## Features

### 🎨 Prompt Builder
- **Template-based generation**: Choose from multiple templates for different fashion styles
- **Dynamic parameters**: Fill in model attributes (age, gender, appearance, pose, outfit, etc.)
- **Real-time preview**: See your generated prompt as you fill in parameters
- **Parameter validation**: Get warnings for missing required fields
- **Model selection**: Support for multiple AI models (Google Nano Banana, Flux.1-Kontext Pro, etc.)

### 🖼️ Prompt Gallery
- **Example prompts**: Browse through pre-made fashion model prompts
- **Interactive selection**: Click any example to load it into the editor
- **Visual feedback**: See selected prompts highlighted with checkmarks
- **Metadata display**: View word count and character count for each prompt
- **Grid layout**: Responsive 2-column grid for easy browsing

### ✍️ Raw Prompt Editor
- **Advanced mode**: Full control over prompt creation
- **Live statistics**: Real-time word and character count
- **Rich placeholder**: Example prompt included in placeholder text
- **Tips & best practices**: Expandable accordion with comprehensive guidance
- **Load from builder**: Import prompts generated from the builder

### 🎯 Additional Features
- **Toast notifications**: Beautiful, non-intrusive notifications for user feedback
- **Responsive design**: Optimized for desktop, tablet, and mobile devices
- **Modern UI**: Gradient backgrounds, smooth animations, and professional styling
- **Accessibility**: Proper focus states, keyboard navigation, and screen reader support

## Project Structure

```
fashion-prompt-builder/
├── app/
│   ├── layout.tsx          # Root layout with metadata
│   ├── page.tsx            # Main page component with all tabs
│   └── globals.css         # Global styles and Tailwind configuration
├── components/
│   └── ui/                 # Reusable UI components
│       ├── button.tsx      # Button component with variants
│       ├── input.tsx       # Input, Textarea, and Select components
│       ├── card.tsx        # Card components (Card, CardHeader, CardTitle, CardContent)
│       ├── tabs.tsx        # Tab navigation component
│       ├── accordion.tsx   # Accordion component for collapsible sections
│       └── toast.tsx       # Toast notification component
├── lib/
│   └── utils.ts            # Utility functions (cn helper)
└── public/
    ├── prompt_templates.json  # Template definitions for different models
    └── prompts.json           # Example prompts for gallery
```

## Tech Stack

- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first CSS framework with custom color palette
- **React 18** - UI library
- **React Icons** - Icon library (Heroicons v2)

## UI Components

### Custom Components
- **Button**: Primary, secondary, and outline variants
- **Input/Textarea/Select**: Styled form inputs with focus states
- **Card**: Container component with header and content sections
- **Tabs**: Tab navigation with active state styling
- **Accordion**: Collapsible sections for organizing content
- **Toast**: Notification system with success, warning, and error types

### Design System
- **Color Palette**: Custom colors defined in Tailwind config
- **Typography**: Inter font family with responsive sizing
- **Spacing**: Consistent spacing system using Tailwind utilities
- **Animations**: Smooth transitions and hover effects

## Color Palette

- **Primary**: `#1FA08F` (Teal) - Main brand color
- **Secondary**: `#486876` (Blue-gray) - Secondary accents
- **Neutral Dark**: `#131E32` - Text and dark elements
- **Neutral Light**: `#BDB7C0` - Subtle backgrounds

## Development

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Run linter
npm run lint
```

## Data Files

### `prompt_templates.json`
Contains template definitions organized by model:
- Each model has multiple template styles
- Templates include placeholders for dynamic parameters
- Each template has a name, description, and template string

### `prompts.json`
Contains example prompts for the gallery:
- Array of prompt objects with metadata
- Used to populate the Prompt Gallery tab
- Can be extended with more examples

## Usage

### Prompt Builder Flow
1. Select a model (e.g., "Google Nano Banana")
2. Choose a template style
3. Fill in the required parameters (age, gender, appearance, etc.)
4. Click "Generate Prompt" to create your prompt
5. Review and edit the generated prompt
6. Click "Use This Prompt" to proceed

### Prompt Gallery Flow
1. Browse through example prompts
2. Click on any prompt to load it into the editor
3. Edit the prompt if needed
4. Click "Use This Prompt" to proceed

### Raw Prompt Flow
1. Type your custom prompt directly
2. Use the tips accordion for guidance
3. Monitor word and character count
4. Optionally load a prompt from the builder
5. Click "Use This Prompt" to proceed

## Features in Detail

### Parameter Groups
The Prompt Builder organizes parameters into logical groups:
1. **Basic Information**: Age, Gender
2. **Appearance**: Complexion, Hair, Eyes, Face Shape
3. **Pose & Styling**: Pose, Outfit
4. **Scene Settings**: Lighting, Background, Fabric Description

### Toast Notifications
- **Success**: Green toast for successful actions
- **Warning**: Yellow toast for warnings and missing fields
- **Error**: Red toast for errors
- Auto-dismisses after 4 seconds
- Manual close button available

### Responsive Design
- Mobile-first approach
- Breakpoints: sm (640px), md (768px), lg (1024px)
- Adaptive layouts for all screen sizes
- Touch-friendly interactive elements

## Future Enhancements

- Backend API integration for actual image generation
- Prompt history and favorites
- Export/import prompts
- Share prompts via URL
- Advanced prompt editing tools
- Template customization

## License

MIT
