# GitHub Pages Deployment Guide

This guide explains how to deploy the Docusaurus documentation site to GitHub Pages.

## Prerequisites

- GitHub repository: `tryonlabs/opentryon`
- GitHub Pages enabled in repository settings
- GitHub Actions enabled

## Setup Steps

### 1. Enable GitHub Pages

1. Go to your repository on GitHub: `https://github.com/tryonlabs/opentryon`
2. Navigate to **Settings** → **Pages**
3. Under **Source**, select **GitHub Actions**
4. Save the settings

### 2. Configure Repository Settings

The GitHub Actions workflow (`.github/workflows/deploy-docs.yml`) is already set up and will:
- Build the Docusaurus site automatically on push to `main` or `master`
- Deploy to GitHub Pages
- Work on pull requests for preview deployments

### 3. Deployment Configuration

The site is configured to deploy to:
- **URL**: `https://tryonlabs.github.io`
- **Base URL**: `/opentryon/`
- **Full URL**: `https://tryonlabs.github.io/opentryon/`

### 4. Manual Deployment (Optional)

If you want to deploy manually:

```bash
cd docs
npm install
npm run build
```

The built files will be in `docs/build/` directory.

## Automatic Deployment

Once GitHub Pages is enabled with GitHub Actions as the source:

1. **Push to main/master**: Automatically triggers deployment
2. **Pull Requests**: Creates preview deployments (if configured)
3. **Deployment Status**: Check the "Actions" tab in your repository

## Troubleshooting

### Build Fails

- Check the Actions tab for error logs
- Ensure Node.js version matches (currently set to 20)
- Verify all dependencies are installed correctly

### Site Not Updating

- Wait a few minutes for GitHub Pages to update
- Check the Actions tab to ensure deployment completed
- Clear browser cache

### Wrong Base URL

If you need to change the base URL:
1. Edit `docs/docusaurus.config.ts`
2. Update the `baseUrl` field
3. Push changes to trigger rebuild

## Custom Domain (Optional)

To use a custom domain:

1. Add a `CNAME` file in `docs/static/` with your domain
2. Configure DNS settings for your domain
3. Update `url` in `docusaurus.config.ts` to your custom domain

## Local Development

For local development, the base URL is automatically handled. Run:

```bash
cd docs
npm start
```

The site will be available at `http://localhost:3000/opentryon/`

