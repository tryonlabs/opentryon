from pathlib import Path

from setuptools import setup, find_packages

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

# Heavy, GPU-oriented stack needed only for local/on-device inference
# (BEN2 background removal, LLaVA-NeXT understanding, FLUX.2-dev Turbo) and
# for training via tryondiffusion. Kept out of the core install so
# `pip install opentryon` (cloud API adapters + CLI) stays light.
LOCAL_INFERENCE_DEPS = [
    "torch==2.1.2",
    "torchvision==0.16.2",
    "opencv-python==4.8.1.78",
    "scikit-image==0.22.0",
    "transformers==4.42.4",
    "timm>=1.0.22",
    "einops>=0.8.1",
    "scipy>=1.15.0",
    "huggingface-hub>=0.36.0",
    "nest-asyncio>=1.5.0",
]

setup(
    name="opentryon",
    version="0.0.2",
    description="Open-source AI toolkit for fashion tech and virtual try-on",
    long_description=long_description,
    long_description_content_type='text/markdown',
    author="TryOn Labs",
    author_email="contact@tryonlabs.ai",
    url='https://github.com/tryonlabs/opentryon',
    license='CC-BY-NC-4.0',
    packages=find_packages(include=['tryon', 'tryon.*', 'tryondiffusion', 'tryondiffusion.*']),
    python_requires='>=3.10',
    # Core install stays light: it only covers the cloud API adapters (tryon.api,
    # minus BEN2) and the `opentryon` CLI. Local/on-device inference (BEN2
    # background removal, LLaVA-NeXT understanding, FLUX.2-dev Turbo, and
    # tryondiffusion training) needs `pip install opentryon[local]`.
    install_requires=[
        "numpy==1.26.4",
        "pillow==10.1.0",
        "tqdm==4.66.1",
        "python-dotenv==1.0.1",
        "boto3==1.40.64",
        "requests>=2.31.0",
        "PyJWT>=2.10.1",
        "google-genai>=1.52.0",
        "openai>=2.9.0",
        "fastapi==0.124.0",
        "uvicorn[standard]==0.38.0",
        "python-multipart==0.0.20",
        "lumaai>=1.18.1",
        "langchain>=1.0.0",
        "langchain-openai>=0.2.0",
        "langchain-anthropic>=0.2.0",
        "langchain-google-genai>=2.0.0",
        "pydantic>=2.0.0",
    ],
    keywords=[
        "virtual try-on",
        "fashion tech",
        "diffusion models",
        "garment segmentation",
        "pose estimation",
        "outfit generation",
        "try-on diffusion",
        "computer vision",
        "deep learning",
        "artificial intelligence",
        "image generation",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: Free for non-commercial use",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Image Processing",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: Free For Home Use",
        "License :: Other/Proprietary License",
    ],
    project_urls={
        'Documentation': 'https://tryonlabs.github.io/opentryon/',
        'Source': 'https://github.com/tryonlabs/opentryon',
        'Bug Reports': 'https://github.com/tryonlabs/opentryon/issues',
        'Discord': 'https://discord.gg/T5mPpZHxkY',
    },
    entry_points={
        "console_scripts": [
            "opentryon=tryon.cli.main:cli_entry",
        ],
    },
    extras_require={
        'local': LOCAL_INFERENCE_DEPS,
        'demos': ['gradio>=6.0.0'],
        'training': LOCAL_INFERENCE_DEPS + ['diffusers>=0.21.0', 'accelerate>=0.20.0'],
        'all': LOCAL_INFERENCE_DEPS + ['gradio>=6.0.0', 'diffusers>=0.21.0', 'accelerate>=0.20.0'],
    },
)
