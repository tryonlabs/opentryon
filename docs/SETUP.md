# Setup Instructions

## Prerequisites

- Node.js 18+ and npm
- Python 3.10+ (for the main library)

## Installation

```bash
cd docs
npm install
```

## Development

Start the development server:

```bash
npm start
```

This starts a local development server at `http://localhost:3000`.

## Build

Build the static site:

```bash
npm run build
```

## Deployment

The site can be deployed to:

- **GitHub Pages**: Configure in `docusaurus.config.ts`
- **Netlify**: Connect repository and deploy
- **Vercel**: Connect repository and deploy
- **Any static hosting**: Upload `build/` directory

## Configuration

Edit `docusaurus.config.ts` to customize:

- Site URL and base URL
- Navigation items
- Footer links
- Theme colors (in `src/css/custom.css`)

## Adding Documentation

1. Add new `.md` files to `docs/docs/`
2. Update `sidebars.ts` to include new pages
3. Documentation supports Markdown and MDX

## Need Help?

See [Docusaurus Documentation](https://docusaurus.io/docs)

