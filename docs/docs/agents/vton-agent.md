---
title: Virtual Try-On Agent
description: LangChain-based agent that intelligently selects and uses the appropriate virtual try-on adapter based on user prompts.
keywords:
  - virtual try-on agent
  - langchain agent
  - kling ai
  - nova canvas
  - segmind
  - AI agent
  - vton agent
---

# Virtual Try-On Agent

A LangChain-based agent that intelligently selects and uses the appropriate virtual try-on adapter based on user prompts.

## Overview

The Virtual Try-On Agent uses LangChain to analyze user requests and automatically select the best virtual try-on adapter. It supports multiple providers:

- **Kling AI**: High-quality virtual try-on with asynchronous processing
- **Amazon Nova Canvas**: AWS Bedrock-based virtual try-on with automatic garment detection
- **Segmind**: Fast and efficient virtual try-on generation

## Features

- **Intelligent Provider Selection**: Automatically selects the adapter based on user prompts
- **Natural Language Interface**: Accepts natural language prompts describing the desired operation
- **Multiple LLM Support**: Works with OpenAI, Anthropic Claude, and Google Gemini
- **Flexible Input**: Supports file paths, URLs, and base64-encoded images
- **Error Handling**: Comprehensive error handling and reporting

## Installation

```bash
pip install langchain langchain-openai langchain-anthropic langchain-google-genai
```

**Note**: This agent uses LangChain 1.x API (`create_agent`). See [LangChain 1.x documentation](https://docs.langchain.com/oss/python/langchain/agents) for details.

## Quick Start

```python
from tryon.agents.vton import VTOnAgent

# Initialize the agent
agent = VTOnAgent(llm_provider="openai")

# Generate virtual try-on
result = agent.generate(
    person_image="person.jpg",
    garment_image="shirt.jpg",
    prompt="Use Kling AI to create a virtual try-on of this shirt"
)

print(result)
```

## Usage

### Command Line Interface

The Virtual Try-On Agent includes a command-line interface for easy usage:

```bash
# Basic usage with default OpenAI provider
python vton_agent.py --person person.jpg --garment shirt.jpg --prompt "Create a virtual try-on using Kling AI"

# Specify LLM provider
python vton_agent.py --person person.jpg --garment shirt.jpg --prompt "Use Nova Canvas for virtual try-on" --llm-provider anthropic

# Use Google Gemini as LLM
python vton_agent.py --person person.jpg --garment shirt.jpg --prompt "Generate try-on with Segmind" --llm-provider google

# Specify LLM model
python vton_agent.py --person person.jpg --garment shirt.jpg --prompt "Use Kling AI" --llm-model gpt-4-turbo-preview

# Save output to specific directory
python vton_agent.py --person person.jpg --garment shirt.jpg --prompt "Create virtual try-on" --output-dir results/

# Use URLs instead of file paths
python vton_agent.py --person https://example.com/person.jpg --garment https://example.com/shirt.jpg --prompt "Use Kling AI"

# Verbose output to see agent reasoning
python vton_agent.py --person person.jpg --garment shirt.jpg --prompt "Use Kling AI" --verbose
```

#### CLI Arguments

- `--person`, `-p`: Path or URL to person/model image (required)
- `--garment`, `-g`: Path or URL to garment/cloth image (required)
- `--prompt`: Natural language prompt describing the virtual try-on request (required)
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
from tryon.agents.vton import VTOnAgent

agent = VTOnAgent(llm_provider="openai")

result = agent.generate(
    person_image="path/to/person.jpg",
    garment_image="path/to/garment.jpg",
    prompt="Generate a virtual try-on using Nova Canvas"
)
```

### Provider Selection

The agent automatically selects the provider based on keywords in your prompt:

- **Kling AI**: "kling ai", "kling", "kolors"
- **Nova Canvas**: "nova canvas", "amazon nova", "aws", "bedrock"
- **Segmind**: "segmind"

Examples:

```python
# Uses Kling AI
result = agent.generate(
    person_image="person.jpg",
    garment_image="shirt.jpg",
    prompt="Use Kling AI to generate the try-on"
)

# Uses Nova Canvas
result = agent.generate(
    person_image="person.jpg",
    garment_image="shirt.jpg",
    prompt="Generate with Amazon Nova Canvas"
)

# Uses Segmind
result = agent.generate(
    person_image="person.jpg",
    garment_image="shirt.jpg",
    prompt="Try Segmind for this virtual try-on"
)
```

### Using Different LLM Providers

```python
# OpenAI
agent = VTOnAgent(llm_provider="openai", llm_model="gpt-4-turbo-preview")

# Anthropic Claude
agent = VTOnAgent(llm_provider="anthropic", llm_model="claude-3-opus-20240229")

# Google Gemini
agent = VTOnAgent(llm_provider="google", llm_model="gemini-pro")
```

### Environment Variables

Set the following environment variables for API keys:

```bash
# For OpenAI
export OPENAI_API_KEY="your-openai-api-key"

# For Anthropic
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# For Google
export GOOGLE_API_KEY="your-google-api-key"

# For Virtual Try-On APIs
export KLING_AI_API_KEY="your-kling-api-key"
export KLING_AI_SECRET_KEY="your-kling-secret-key"
export SEGMIND_API_KEY="your-segmind-api-key"
export AMAZON_NOVA_REGION="us-east-1"  # For Nova Canvas
```

## API Reference

### VTOnAgent

#### `__init__(llm_provider, llm_model=None, temperature=0.0, api_key=None, **llm_kwargs)`

Initialize the Virtual Try-On Agent.

**Parameters:**
- `llm_provider` (str): LLM provider to use. Options: "openai", "anthropic", "google"
- `llm_model` (str, optional): Specific model name. If None, uses default for provider
- `temperature` (float): Temperature for LLM (default: 0.0)
- `api_key` (str, optional): API key for LLM provider
- `**llm_kwargs`: Additional keyword arguments for LLM initialization

#### `generate(person_image, garment_image, prompt, **kwargs)`

Generate virtual try-on images using the agent.

**Parameters:**
- `person_image` (str): Path or URL to the person/model image
- `garment_image` (str): Path or URL to the garment/cloth image
- `prompt` (str): Natural language prompt describing the request
- `**kwargs`: Additional parameters to pass to the agent

**Returns:**
- Dictionary containing:
  - `status`: "success" or "error"
  - `provider`: Name of the provider used
  - `images`: List of generated images (URLs or base64 strings)
  - `result`: Full agent response
  - `error`: Error message (if status is "error")

## Architecture

The agent uses LangChain's ReAct agent framework:

1. **Tools**: Each virtual try-on adapter is wrapped as a LangChain tool
2. **Agent**: A ReAct agent that selects and uses tools based on user prompts
3. **LLM**: Language model (OpenAI, Anthropic, or Google) that powers the agent

### Tool Structure

Each tool follows this pattern:

```python
@tool("provider_name_virtual_tryon", args_schema=InputSchema)
def provider_virtual_tryon(person_image, garment_image, **kwargs):
    """Tool description"""
    adapter = ProviderAdapter()
    result = adapter.generate(...)
    return result
```

## Examples

### Example 1: Basic Virtual Try-On

```python
from tryon.agents.vton import VTOnAgent

agent = VTOnAgent(llm_provider="openai")

result = agent.generate(
    person_image="https://example.com/person.jpg",
    garment_image="https://example.com/shirt.jpg",
    prompt="Create a virtual try-on using Kling AI"
)

if result["status"] == "success":
    print(f"Generated {len(result['images'])} images using {result['provider']}")
else:
    print(f"Error: {result.get('error')}")
```

### Example 2: Provider Selection

```python
agent = VTOnAgent(llm_provider="anthropic")

# The agent will select Kling AI based on the prompt
result = agent.generate(
    person_image="person.jpg",
    garment_image="dress.jpg",
    prompt="I want to see how this dress looks. Use Kling AI for best quality."
)
```

### Example 3: Custom Parameters

```python
agent = VTOnAgent(llm_provider="google")

# The agent can extract parameters from the prompt
result = agent.generate(
    person_image="person.jpg",
    garment_image="pants.jpg",
    prompt="Generate virtual try-on with Nova Canvas for lower body garment"
)
```

## Limitations

- Currently supports only dedicated virtual try-on APIs (Kling AI, Nova Canvas, Segmind)
- Image generation APIs (Nano Banana Pro, FLUX 2 Pro, FLUX 2 Flex) are not yet integrated
- No vector store support (as requested)
- Agent output parsing may need refinement for complex scenarios

## Future Enhancements

- Add support for image generation APIs (Nano Banana Pro, FLUX 2 Pro, FLUX 2 Flex)
- Improve prompt understanding for better parameter extraction
- Add support for batch processing
- Implement image decoding utilities
- Add result caching

## Related Documentation

- [Agent Ideas](./agent-ideas.md) - Overview of Fashion AI Agents ecosystem
- [API Reference - Kling AI](../api-reference/kling-ai.md) - Kling AI adapter documentation
- [API Reference - Nova Canvas](../api-reference/nova-canvas.md) - Nova Canvas adapter documentation
- [API Reference - Segmind](../api-reference/segmind.md) - Segmind adapter documentation

