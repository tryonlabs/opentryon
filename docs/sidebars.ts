import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  tutorialSidebar: [
    'intro',
    {
      type: 'category',
      label: 'Getting Started',
      items: [
        'getting-started/installation',
        'getting-started/quickstart',
        'getting-started/configuration',
      ],
    },
    {
      type: 'category',
      label: 'Preprocessing',
      items: [
        'preprocessing/overview',
        'preprocessing/garment-segmentation',
        'preprocessing/garment-extraction',
        'preprocessing/human-segmentation',
        'preprocessing/pose-estimation',
        'preprocessing/image-captioning',
      ],
    },
    {
      type: 'category',
      label: 'TryOnDiffusion',
      items: [
        'tryondiffusion/overview',
        'tryondiffusion/architecture',
        'tryondiffusion/training',
        'tryondiffusion/inference',
        'tryondiffusion/preprocessing',
      ],
    },
    {
      type: 'category',
      label: 'Datasets',
      items: [
        'datasets/overview',
        'datasets/fashion-mnist',
        'datasets/viton-hd',
        'datasets/subjects200k',
      ],
    },
    {
      type: 'category',
      label: 'API Reference',
      items: [
        'api-reference/overview',
        'api-reference/preprocessing',
        'api-reference/diffusion',
        'api-reference/kling-ai',
        'api-reference/nova-canvas',
        'api-reference/segmind',
        'api-reference/flux2',
        'api-reference/nano-banana',
        'api-reference/gpt-image',
        'api-reference/sora-video',
        'api-reference/ben2',
        'api-reference/utils',
      ],
    },
    {
      type: 'category',
      label: 'Examples',
      items: [
        'examples/basic-usage',
        'examples/garment-pipeline',
        'examples/virtual-tryon',
        'examples/datasets',
        'examples/outfit-generation',
      ],
    },
    {
      type: 'category',
      label: 'Demos',
      items: [
        'demos/overview',
        'demos/virtual-tryon',
        'demos/fashion-prompt-builder',
        'demos/extract-garment',
        'demos/model-swap',
        'demos/outfit-generator',
      ],
    },
    {
      type: 'category',
      label: 'Advanced',
      items: [
        'advanced/custom-models',
        'advanced/training-guide',
        'advanced/performance-optimization',
        'advanced/troubleshooting',
      ],
    },
    {
      type: 'category',
      label: 'Agents',
      items: [
        'agents/agent-ideas-summary',
        'agents/agent-ideas',
        'agents/vton-agent',
        'agents/model-swap-agent',
      ],
    },
    {
      type: 'category',
      label: 'Community',
      items: [
        'community/contributing',
        'community/code-of-conduct',
        'community/roadmap',
        'community/license',
      ],
    },
  ],
};

export default sidebars;

