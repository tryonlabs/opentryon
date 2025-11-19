import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'OpenTryOn',
  tagline: 'Open-source AI toolkit for fashion tech and virtual try-on',
  favicon: 'img/favicon.ico',

  // Set the production url of your site here
  url: 'https://tryonlabs.github.io',
  // Set the /<baseUrl>/ pathname under which your site is served
  // For local development, use '/' - for GitHub Pages, use '/opentryon/'
  // Change this to '/opentryon/' when building for production deployment
  baseUrl: '/',
  
  // SEO Configuration
  trailingSlash: false, // Better for SEO - no trailing slashes
  
  // Additional head tags for SEO and GEO
  headTags: [
    // Structured Data (JSON-LD) for better search engine understanding
    {
      tagName: 'script',
      attributes: {
        type: 'application/ld+json',
      },
      innerHTML: JSON.stringify({
        '@context': 'https://schema.org',
        '@type': 'SoftwareApplication',
        name: 'OpenTryOn',
        applicationCategory: 'DeveloperApplication',
        operatingSystem: 'Any',
        offers: {
          '@type': 'Offer',
          price: '0',
          priceCurrency: 'USD',
        },
        description: 'Open-source AI toolkit for fashion technology and virtual try-on applications. Provides tools for garment segmentation, human parsing, pose estimation, and virtual try-on using state-of-the-art diffusion models.',
        url: 'https://tryonlabs.github.io',
        author: {
          '@type': 'Organization',
          name: 'TryOn Labs',
          url: 'https://tryonlabs.ai',
        },
        codeRepository: 'https://github.com/tryonlabs/opentryon',
        license: 'https://creativecommons.org/licenses/by-nc/4.0/',
        keywords: 'virtual try-on, fashion AI, AI toolkit, virtual try-on API, fashion technology, garment segmentation, TryOnDiffusion, open source AI',
        programmingLanguage: 'Python',
        runtimePlatform: 'Python 3.10+',
      }),
    },
    {
      tagName: 'script',
      attributes: {
        type: 'application/ld+json',
      },
      innerHTML: JSON.stringify({
        '@context': 'https://schema.org',
        '@type': 'WebSite',
        name: 'OpenTryOn',
        url: 'https://tryonlabs.github.io',
        description: 'Open-source AI toolkit for fashion technology and virtual try-on applications',
        publisher: {
          '@type': 'Organization',
          name: 'TryOn Labs',
          url: 'https://tryonlabs.ai',
          logo: {
            '@type': 'ImageObject',
            url: 'https://tryonlabs.github.io/img/logo.png',
          },
        },
        potentialAction: {
          '@type': 'SearchAction',
          target: {
            '@type': 'EntryPoint',
            urlTemplate: 'https://tryonlabs.github.io/search?q={search_term_string}',
          },
          'query-input': 'required name=search_term_string',
        },
      }),
    },
    {
      tagName: 'script',
      attributes: {
        type: 'application/ld+json',
      },
      innerHTML: JSON.stringify({
        '@context': 'https://schema.org',
        '@type': 'TechArticle',
        headline: 'OpenTryOn Documentation',
        description: 'Complete documentation for OpenTryOn - an open-source AI toolkit for fashion technology and virtual try-on applications',
        author: {
          '@type': 'Organization',
          name: 'TryOn Labs',
        },
        publisher: {
          '@type': 'Organization',
          name: 'TryOn Labs',
          logo: {
            '@type': 'ImageObject',
            url: 'https://tryonlabs.github.io/img/logo.png',
          },
        },
        datePublished: '2024-01-01',
        dateModified: '2025-11-19',
      }),
    },
    // Additional meta tags for GEO (Generative Engine Optimization)
    {
      tagName: 'meta',
      attributes: {
        name: 'description',
        content: 'OpenTryOn is an open-source AI toolkit for fashion technology and virtual try-on. Features virtual try-on APIs (Amazon Nova Canvas, Kling AI, Segmind), datasets (Fashion-MNIST, VITON-HD), garment segmentation, pose estimation, and TryOnDiffusion implementation.',
      },
    },
    {
      tagName: 'meta',
      attributes: {
        name: 'generator',
        content: 'Docusaurus',
      },
    },
    {
      tagName: 'link',
      attributes: {
        rel: 'canonical',
        href: 'https://tryonlabs.github.io',
      },
    },
    {
      tagName: 'link',
      attributes: {
        rel: 'alternate',
        type: 'application/rss+xml',
        title: 'OpenTryOn Documentation',
        href: 'https://tryonlabs.github.io/feed.xml',
      },
    },
  ],

  // GitHub pages deployment config.
  organizationName: 'tryonlabs',
  projectName: 'opentryon',

  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',

  // Markdown configuration
  markdown: {
    format: 'mdx',
  },

  // Even if you don't use internationalization, you can use this field to set
  // useful metadata like html lang. For example, if your site is Chinese, you
  // will set "zh-Hans".
  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          editUrl: 'https://github.com/tryonlabs/opentryon/tree/main/docs/',
          routeBasePath: '/', // Serve docs at root instead of /docs/
          // The first document in the sidebar (intro.md) will be the home page
          remarkPlugins: [],
          rehypePlugins: [],
          // SEO configuration for docs
          showLastUpdateAuthor: false,
          showLastUpdateTime: false,
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    // SEO and Social Media Configuration
    metadata: [
      {name: 'keywords', content: 'virtual try-on, fashion AI, AI toolkit, virtual try-on API, fashion technology, garment segmentation, TryOnDiffusion, open source AI, fashion tech, virtual fitting, AI fashion, computer vision, diffusion models, fashion datasets, VITON-HD, Fashion-MNIST, Amazon Nova Canvas, Kling AI, Segmind'},
      {name: 'author', content: 'TryOn Labs'},
      {name: 'robots', content: 'index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1'},
      {name: 'googlebot', content: 'index, follow'},
      {name: 'bingbot', content: 'index, follow'},
      {name: 'language', content: 'English'},
      {name: 'revisit-after', content: '7 days'},
      {name: 'theme-color', content: '#1FA08F'},
      {name: 'apple-mobile-web-app-capable', content: 'yes'},
      {name: 'apple-mobile-web-app-status-bar-style', content: 'black-translucent'},
      {property: 'og:type', content: 'website'},
      {property: 'og:site_name', content: 'OpenTryOn'},
      {property: 'og:locale', content: 'en_US'},
      {property: 'og:image:width', content: '1200'},
      {property: 'og:image:height', content: '630'},
      {property: 'og:image:type', content: 'image/jpeg'},
      {name: 'twitter:card', content: 'summary_large_image'},
      {name: 'twitter:site', content: '@tryonlabs'},
      {name: 'twitter:creator', content: '@tryonlabs'},
      {name: 'twitter:image:alt', content: 'OpenTryOn - Open-source AI toolkit for fashion tech and virtual try-on'},
    ],
    image: '/img/opentryon-social-card.jpg',
    navbar: {
      title: 'OpenTryOn',
      logo: {
        alt: 'OpenTryOn Logo',
        src: '/img/logo.png',
        href: '/', // Make logo clickable, links to home page (intro.md)
      },
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'tutorialSidebar',
          position: 'left',
          label: 'Docs',
        },
        {
          type: 'html',
          position: 'right',
          value: '<a href="https://github.com/tryonlabs/opentryon" target="_blank" rel="noopener noreferrer" class="navbar__item navbar__link navbar__link-with-icon" aria-label="GitHub"><svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg><span>GitHub</span></a>',
        },
        {
          type: 'html',
          position: 'right',
          value: '<a href="https://discord.gg/T5mPpZHxkY" target="_blank" rel="noopener noreferrer" class="navbar__item navbar__link navbar__link-with-icon" aria-label="Discord"><svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028c.462-.63.874-1.295 1.226-1.994a.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z"/></svg><span>Discord</span></a>',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Documentation',
          items: [
            {
              label: 'Getting Started',
              to: '/getting-started/installation',
            },
            {
              label: 'API Reference',
              to: '/api-reference/overview',
            },
            {
              label: 'Examples',
              to: '/examples/basic-usage',
            },
          ],
        },
        {
          title: 'Community',
          items: [
            {
              label: 'Discord',
              href: 'https://discord.gg/T5mPpZHxkY',
            },
            {
              label: 'GitHub',
              href: 'https://github.com/tryonlabs/opentryon',
            },
            {
              label: 'Twitter',
              href: 'https://twitter.com/tryonlabs',
            },
          ],
        },
        {
          title: 'More',
          items: [
            {
              label: 'License',
              to: '/community/license',
            },
            {
              label: 'Contributing',
              to: '/community/contributing',
            },
            {
              label: 'Roadmap',
              to: '/community/roadmap',
            },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} TryOn Labs. Built with Docusaurus.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ['python', 'bash', 'yaml', 'json'],
    },
  } satisfies Preset.ThemeConfig,

  plugins: [
    [
      require.resolve('docusaurus-plugin-search-local'),
      {
        // Options for the local search plugin
        indexBlog: true, // Set to true if you have a blog
        indexPages: true, // Set to true to index pages
        hashed: true,
        highlightSearchTermsOnTargetPage: true, // Highlight search terms on target page
        searchResultLimits: 8, // Limit search results
        searchResultContextMaxLength: 50, // Context length for search results
      },
    ],
    [
      '@docusaurus/plugin-sitemap',
      {
        changefreq: 'weekly',
        priority: 0.5,
        ignorePatterns: ['/tags/**'],
        filename: 'sitemap.xml',
      },
    ],
    // Note: Client-side redirects only work in production builds
    // If you need redirects, uncomment and test with: npm run build && npm run serve
    [
      '@docusaurus/plugin-client-redirects',
      {
        redirects: [
          {
            from: ['/preprocessing'],
            to: '/preprocessing/overview',
          },
          {
            from: ['/api-reference'],
            to: '/api-reference/overview',
          },
          {
            from: ['/getting-started'],
            to: '/getting-started/installation',
          },
          {
            from: ['/tryondiffusion'],
            to: '/tryondiffusion/overview',
          },
          {
            from: ['/examples'],
            to: '/examples/basic-usage',
          },
          {
            from: ['/demos'],
            to: '/demos/overview',
          },
          {
            from: ['/advanced'],
            to: '/advanced/custom-models',
          },
          {
            from: ['/community'],
            to: '/community/contributing',
          }
        ],
      },
    ],
  ],
};

export default config;

