from pathlib import Path

from setuptools import setup, find_packages

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="opentryon",
    version="0.0.1",
    description="Open-source AI toolkit for fashion tech and virtual try-on",
    long_description=long_description,
    long_description_content_type='text/markdown',
    author="TryOn Labs",
    author_email="contact@tryonlabs.ai",
    url='https://github.com/tryonlabs/opentryon',
    license='Creative Commons BY-NC 4.0',
    packages=find_packages(),
    python_requires='>=3.10',
    install_requires=[
        "torch==2.1.2",
        "torchvision==0.16.2",
        "numpy==1.26.4",
        "opencv-python==4.8.1.78",
        "pillow==10.1.0",
        "tqdm==4.66.1",
        "scikit-image==0.22.0",
        "python-dotenv==1.0.1",
        "transformers==4.42.4",
        "boto3==1.40.64",
        "requests>=2.31.0",
        "PyJWT>=2.10.1",
        "google-genai>=1.52.0",
        "fastapi==0.124.0",
        "uvicorn[standard]==0.38.0",
        "python-multipart==0.0.20",
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
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: Free for non-commercial use",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Image Processing",
    ],
)
