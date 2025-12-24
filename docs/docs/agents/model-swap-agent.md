---
title: Model Swap Agent
description: LangChain-based agent that intelligently replaces models/people in images while preserving outfits and styling using multiple AI models.
keywords:
  - model swap agent
  - langchain agent
  - nano banana
  - flux2
  - AI agent
  - model replacement
  - outfit preservation
---

# Model Swap Agent

A LangChain-based AI agent that intelligently replaces models/people in images while perfectly preserving outfits and styling. Perfect for e-commerce sellers and fashion brands to create professional product imagery with diverse models.

## Overview

The Model Swap Agent uses LangChain to analyze natural language prompts and extract detailed person attributes, then generates professional model-swapped images while maintaining the exact outfit, clothing details, patterns, and styling.

### Supported Models

The agent supports multiple AI models for model swapping:

- **Nano Banana** (Gemini 2.5 Flash Image): Fast generation at 1024px resolution, ideal for quick iterations
- **Nano Banana Pro** (Gemini 3 Pro Image Preview): High-quality 4K resolution with search grounding support (default)
- **FLUX 2 Pro**: Professional quality with custom width/height control
- **FLUX 2 Flex**: Advanced controls (guidance scale, steps) for fine-tuned generation

## Features

- **Intelligent Attribute Extraction**: Automatically extracts gender, age, ethnicity, body type, pose, and styling from natural language prompts
- **Perfect Outfit Preservation**: Maintains exact clothing details, colors, patterns, textures, and fit
- **Multi-Model Support**: Choose from 4 different AI models based on your needs
- **High-Resolution Output**: Up to 4K resolution for professional e-commerce quality
- **Natural Language Interface**: Simple prompts like "Replace with a professional Asian female model in her 30s"
- **Multiple LLM Support**: Works with OpenAI, Anthropic Claude, and Google Gemini
- **Professional Quality**: Maintains lighting, background, composition, and photography standards

## Installation

```bash
pip install langchain langchain-openai langchain-anthropic langchain-google-genai
```

**Note**: This agent uses LangChain 1.x API (`create_agent`). See [LangChain 1.x documentation](https://docs.langchain.com/oss/python/langchain/agents) for details.

## Quick Start

```python
from tryon.agents.model_swap import ModelSwapAgent

# Initialize agent with default Nano Banana Pro
agent = ModelSwapAgent(llm_provider="openai")

# Generate model swap
result = agent.generate(
    image="person_wearing_outfit.jpg",
    prompt="Replace with a professional Asian female model in her 30s, athletic build"
)

if result["status"] == "success":
    for idx, image in enumerate(result['images']):
        image.save(f"swapped_model_{idx}.png")
```

## Usage

### Command Line Interface

The Model Swap Agent includes a command-line interface for easy usage:

```bash
# Basic usage with default Nano Banana Pro
python model_swap_agent.py \
    --image model.jpg \
    --prompt "Replace with a professional male model in his 30s, athletic build"

# Use FLUX 2 Pro for high-quality results
python model_swap_agent.py \
    --image model.jpg \
    --prompt "Replace with a professional female model" \
    --model flux2_pro

# Use FLUX 2 Flex for advanced control
python model_swap_agent.py \
    --image model.jpg \
    --prompt "Replace with an athletic Asian model" \
    --model flux2_flex

# Use Nano Banana for fast generation
python model_swap_agent.py \
    --image model.jpg \
    --prompt "Replace with a professional model" \
    --model nano_banana

# Specify resolution for Nano Banana Pro
python model_swap_agent.py \
    --image model.jpg \
    --prompt "Male model in his 30s" \
    --model nano_banana_pro \
    --resolution 2K

# Use Google Search grounding (Nano Banana Pro only)
python model_swap_agent.py \
    --image model.jpg \
    --prompt "Model like professional fashion runway" \
    --model nano_banana_pro \
    --search-grounding

# Use different LLM provider
python model_swap_agent.py \
    --image model.jpg \
    --prompt "Plus-size woman, African American, 40s" \
    --llm-provider anthropic \
    --model flux2_pro

# Use URLs instead of file paths
python model_swap_agent.py \
    --image https://example.com/model.jpg \
    --prompt "Female model, 30s, professional" \
    --model flux2_pro

# Verbose output to see agent reasoning
python model_swap_agent.py \
    --image model.jpg \
    --prompt "Male model in 30s" \
    --verbose
```

#### CLI Arguments

- `--image`, `-i`: Path or URL to image of person wearing outfit (required)
- `--prompt`: Description of desired model/person (required)
- `--model`: Model to use for swapping (default: `nano_banana_pro`, options: `nano_banana`, `nano_banana_pro`, `flux2_pro`, `flux2_flex`)
- `--resolution`: Output resolution for Nano Banana Pro (default: `4K`, options: `1K`, `2K`, `4K`)
- `--search-grounding`: Use Google Search grounding for real-world references (Nano Banana Pro only)
- `--llm-provider`: LLM provider to use (default: `openai`, options: `openai`, `anthropic`, `google`)
- `--llm-model`: Specific LLM model name (optional, uses default for provider)
- `--llm-temperature`: Temperature for LLM (default: `0.0`)
- `--llm-api-key`: API key for LLM provider (optional, can use environment variables)
- `--output-dir`, `-o`: Directory to save generated images (default: `outputs/`)
- `--save-base64`: Also save Base64 encoded strings to .txt files
- `--verbose`: Print verbose output including agent reasoning steps

### Python API Usage

#### Basic Usage

```python
from tryon.agents.model_swap import ModelSwapAgent

# Initialize agent with default Nano Banana Pro
agent = ModelSwapAgent(llm_provider="openai")

# Generate model swap
result = agent.generate(
    image="person_wearing_outfit.jpg",
    prompt="Replace with a professional male model in his 30s, athletic build"
)

if result["status"] == "success":
    images = result['images']
    for idx, image in enumerate(images):
        image.save(f"result_{idx}.png")
```

#### Using Different Models

```python
# Nano Banana (fast, 1024px)
agent = ModelSwapAgent(llm_provider="openai", model="nano_banana")
result = agent.generate(
    image="model.jpg",
    prompt="Replace with a professional model"
)

# Nano Banana Pro (4K, default)
agent = ModelSwapAgent(llm_provider="openai", model="nano_banana_pro")
result = agent.generate(
    image="model.jpg",
    prompt="Replace with a professional model",
    resolution="4K",
    use_search_grounding=False
)

# FLUX 2 Pro (high quality)
agent = ModelSwapAgent(llm_provider="openai", model="flux2_pro")
result = agent.generate(
    image="model.jpg",
    prompt="Replace with a professional model"
)

# FLUX 2 Flex (advanced controls)
agent = ModelSwapAgent(llm_provider="openai", model="flux2_flex")
result = agent.generate(
    image="model.jpg",
    prompt="Replace with a professional model"
)
```

#### Using Different LLM Providers

```python
# OpenAI (default)
agent = ModelSwapAgent(llm_provider="openai", llm_model="gpt-4")

# Anthropic Claude
agent = ModelSwapAgent(llm_provider="anthropic", llm_model="claude-3-opus-20240229")

# Google Gemini
agent = ModelSwapAgent(llm_provider="google", llm_model="gemini-2.5-pro")
```

### Attribute Extraction

The agent automatically extracts the following attributes from your prompts:

- **Gender**: Male, female, non-binary, or unspecified
- **Age Range**: Teens, 20s, 30s, 40s, 50s+
- **Ethnicity/Appearance**: Asian, African, Caucasian, Hispanic, Middle Eastern, mixed, diverse, or unspecified
- **Body Type**: Slim, athletic, average, curvy, plus-size, muscular
- **Facial Features**: Sharp features, soft features, distinctive characteristics
- **Pose/Expression**: Confident, casual, professional, friendly, serious, natural
- **Styling Preferences**: Professional, casual, editorial, commercial, lifestyle

### Example Prompts

**Basic Descriptions:**
```python
"Professional male model in his 30s"
"Female model, mid-20s, athletic build"
"Plus-size woman, friendly expression"
```

**Detailed Descriptions:**
```python
"Professional Asian female model in her early 30s, athletic build, 
confident posture, sharp features, editorial style photography"

"Athletic male model, African American, late 20s, muscular build,
casual confident pose, commercial photography style"

"Plus-size woman, Caucasian, 40s, warm friendly expression,
lifestyle photography, natural lighting"
```

**Style References:**
```python
"Professional fashion runway model style"
"Commercial lifestyle photography model"
"Editorial high-fashion model aesthetic"
```

## Model Comparison

| Model | Resolution | Speed | Quality | Best For |
|-------|-----------|-------|---------|----------|
| **Nano Banana** | 1024px | Fast ⚡ | Good | Quick iterations, testing |
| **Nano Banana Pro** | Up to 4K | Medium | Excellent | Professional e-commerce (default) |
| **FLUX 2 Pro** | Custom | Medium | High | Professional quality with custom dimensions |
| **FLUX 2 Flex** | Custom | Slower | Highest | Fine-tuned control, advanced parameters |

## Resolution Options (Nano Banana Pro)

- **1K (1024px)**: Draft quality, fast generation, testing
- **2K (2048px)**: High-quality, good for web use
- **4K (4096px)**: Professional e-commerce quality (default, recommended)

## Environment Variables

Set the following environment variables for API keys:

```bash
# For LLM providers (choose one)
export OPENAI_API_KEY="your-openai-api-key"
# OR
export ANTHROPIC_API_KEY="your-anthropic-api-key"
# OR
export GOOGLE_API_KEY="your-google-api-key"

# For model swapping APIs
export GEMINI_API_KEY="your-gemini-api-key"  # For Nano Banana models
export BFL_API_KEY="your-bfl-api-key"        # For FLUX 2 models
```

## API Reference

### ModelSwapAgent

#### `__init__(llm_provider, llm_model=None, temperature=0.0, api_key=None, model=None, **llm_kwargs)`

Initialize the Model Swap Agent.

**Parameters:**
- `llm_provider` (str): LLM provider to use. Options: "openai", "anthropic", "google"
- `llm_model` (str, optional): Specific model name. If None, uses default for provider
- `temperature` (float): Temperature for LLM (default: 0.0)
- `api_key` (str, optional): API key for LLM provider
- `model` (str, optional): Model to use for swapping. Options: "nano_banana", "nano_banana_pro", "flux2_pro", "flux2_flex". Default: "nano_banana_pro"
- `**llm_kwargs`: Additional keyword arguments for LLM initialization

#### `generate(image, prompt, resolution=None, use_search_grounding=False, verbose=False, **kwargs)`

Generate model-swapped images using the agent.

**Parameters:**
- `image` (str): Path or URL to the image of person wearing the outfit
- `prompt` (str): Natural language description of desired model/person
- `resolution` (str, optional): Resolution for Nano Banana Pro. Options: "1K", "2K", "4K" (default: "4K")
- `use_search_grounding` (bool): Whether to use Google Search grounding for real-world references (Nano Banana Pro only)
- `verbose` (bool): If True, print debug information about agent reasoning
- `**kwargs`: Additional parameters to pass to the agent

**Returns:**
- Dictionary containing:
  - `status`: "success" or "error"
  - `provider`: Model provider used (e.g., "nano_banana_pro", "flux2_pro")
  - `images`: List of generated images (PIL Images or base64 strings)
  - `model_description`: The detailed prompt used for generation
  - `result`: Full agent response
  - `error`: Error message (if status is "error")

## Examples

### Example 1: Basic Model Swap

```python
from tryon.agents.model_swap import ModelSwapAgent

agent = ModelSwapAgent(llm_provider="openai")

result = agent.generate(
    image="model_wearing_outfit.jpg",
    prompt="Replace with a professional Asian female model in her 30s, athletic build"
)

if result["status"] == "success":
    for idx, image in enumerate(result['images']):
        image.save(f"swapped_model_{idx}.png")
    print(f"Generated {len(result['images'])} images")
```

### Example 2: High-Quality with FLUX 2 Pro

```python
agent = ModelSwapAgent(
    llm_provider="openai",
    model="flux2_pro"
)

result = agent.generate(
    image="model.jpg",
    prompt="Professional male model in his 30s, athletic build, confident pose"
)

if result["status"] == "success":
    result['images'][0].save("high_quality_swap.png")
```

### Example 3: 4K Professional Quality

```python
agent = ModelSwapAgent(
    llm_provider="openai",
    model="nano_banana_pro"
)

result = agent.generate(
    image="outfit.jpg",
    prompt=(
        "Professional Asian female model in her early 30s, "
        "athletic build, confident posture, sharp features, "
        "editorial style photography"
    ),
    resolution="4K",
    use_search_grounding=False,
    verbose=True
)

if result["status"] == "success":
    for idx, image in enumerate(result['images']):
        image.save(f"professional_4k_{idx}.png")
    print(f"Model description: {result['model_description']}")
```

### Example 4: Advanced Control with FLUX 2 Flex

```python
agent = ModelSwapAgent(
    llm_provider="anthropic",
    model="flux2_flex"
)

result = agent.generate(
    image="model.jpg",
    prompt="Plus-size woman, African American, 40s, friendly expression"
)

if result["status"] == "success":
    result['images'][0].save("flex_result.png")
```

## How It Works

1. **Prompt Analysis**: LLM agent extracts person attributes (gender, age, ethnicity, body type, pose, styling) from natural language prompts
2. **Prompt Construction**: Agent builds detailed, professional prompt emphasizing outfit preservation and maintaining original lighting, background, and composition
3. **Model Selection**: Uses the specified model (or default Nano Banana Pro) to generate images
4. **Image Generation**: Selected model generates up to 4K resolution images with perfect outfit preservation

## Best Practices

1. **Be Specific**: Include age, gender, ethnicity, body type in prompts for better results
2. **Describe Pose**: Mention confident, casual, professional, etc. to guide the generation
3. **Mention Style**: Editorial, commercial, lifestyle photography helps set the tone
4. **Use 4K Resolution**: For professional e-commerce quality (Nano Banana Pro)
5. **Trust the Agent**: Outfit preservation is automatic - focus on describing the desired model
6. **Choose the Right Model**: 
   - Use Nano Banana for quick iterations
   - Use Nano Banana Pro for professional 4K quality (default)
   - Use FLUX 2 Pro for custom dimensions
   - Use FLUX 2 Flex for advanced control

## Use Cases

- **E-commerce Sellers**: Create professional product photos with diverse models
- **Fashion Brands**: Showcase clothing on different body types and demographics
- **Clothing Brands**: Generate consistent product imagery across model portfolios
- **Product Photography**: Maintain styling and composition while varying models

## Limitations

- Resolution options (1K, 2K, 4K) are only available for Nano Banana Pro
- Search grounding is only available for Nano Banana Pro
- FLUX models don't support resolution presets (use custom width/height via API)
- Agent output parsing may need refinement for complex scenarios

## Future Enhancements

- Add support for more image generation models
- Improve prompt understanding for better attribute extraction
- Add support for batch processing
- Implement result caching
- Add support for video model swapping

## Related Documentation

- [Agent Ideas](./agent-ideas.md) - Overview of Fashion AI Agents ecosystem
- [Virtual Try-On Agent](./vton-agent.md) - Virtual try-on agent documentation
- [API Reference - Nano Banana](../api-reference/nano-banana.md) - Nano Banana adapter documentation
- [API Reference - FLUX 2](../api-reference/flux2.md) - FLUX 2 adapter documentation

