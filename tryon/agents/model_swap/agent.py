"""
Model Swap Agent using LangChain

This agent uses LangChain 1.x to intelligently extract person attributes from
user prompts and perform model swapping using Nano Banana Pro API. The agent
takes an image of a person wearing an outfit and replaces the model based on
natural language descriptions.

Use Case: E-commerce sellers and clothing brands can create professional quality
product imagery with high-quality fashion models for their online stores.

Example:
    >>> from tryon.agents.model_swap import ModelSwapAgent
    >>> 
    >>> # Using default Nano Banana Pro
    >>> agent = ModelSwapAgent(llm_provider="openai")
    >>> result = agent.generate(
    ...     image="person_with_outfit.jpg",
    ...     prompt="Replace with a professional Asian female model in her 30s, athletic build"
    ... )
    >>> print(result)
    
    >>> # Using FLUX 2 Pro
    >>> agent = ModelSwapAgent(llm_provider="openai", model="flux2_pro")
    >>> result = agent.generate(
    ...     image="person_with_outfit.jpg",
    ...     prompt="Replace with a professional male model in his 30s"
    ... )
"""

import json
import asyncio
from typing import Optional, Dict, Any, List

# LangChain 1.x imports
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.language_models import BaseChatModel

from .tools import get_model_swap_tools, get_tool_output_from_cache


class ModelSwapAgent:
    """
    LangChain-based Model Swap Agent.
    
    This agent intelligently extracts person attributes from natural language
    prompts and uses Nano Banana Pro to swap the model while preserving the
    outfit and styling.
    
    The agent analyzes prompts to extract:
    - Gender (male, female, non-binary)
    - Age range (20s, 30s, 40s, etc.)
    - Ethnicity/appearance
    - Body type (athletic, slim, average, plus-size)
    - Facial features
    - Pose and styling preferences
    
    Example:
        >>> # Using default Nano Banana Pro
        >>> agent = ModelSwapAgent(llm_provider="openai")
        >>> result = agent.generate(
        ...     image="model.jpg",
        ...     prompt="Replace with a professional male model in his 30s, athletic build, confident pose"
        ... )
        
        >>> # Using FLUX 2 Flex for advanced control
        >>> agent = ModelSwapAgent(llm_provider="openai", model="flux2_flex")
        >>> result = agent.generate(
        ...     image="model.jpg",
        ...     prompt="Replace with a professional female model in her 20s"
        ... )
    """
    
    def __init__(
        self,
        llm_provider: str = "openai",
        llm_model: Optional[str] = None,
        temperature: float = 0.0,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        **llm_kwargs
    ):
        """
        Initialize the Model Swap Agent.
        
        Args:
            llm_provider: LLM provider to use. Options: "openai", "anthropic", "google"
            llm_model: Specific model name (e.g., "gpt-4", "claude-3-opus-20240229")
                     If None, uses default model for the provider
            temperature: Temperature for LLM (default: 0.0 for deterministic behavior)
            api_key: API key for the LLM provider (if not set via environment variable)
            model: Model to use for model swapping. Options: "nano_banana", "nano_banana_pro",
                   "flux2_pro", "flux2_flex". If None, defaults to "nano_banana_pro"
            **llm_kwargs: Additional keyword arguments for LLM initialization
        
        Raises:
            ValueError: If llm_provider is not supported
        """
        self.llm_provider = llm_provider.lower()
        # Normalize model name: handle None, convert to lowercase, replace dashes/spaces with underscores
        if model:
            self.model = model.lower().replace("-", "_").replace(" ", "_")
        else:
            self.model = "nano_banana_pro"
        self.tools = get_model_swap_tools(model=self.model)
        self.llm = self._initialize_llm(
            llm_provider=self.llm_provider,
            llm_model=llm_model,
            temperature=temperature,
            api_key=api_key,
            **llm_kwargs
        )
        self.agent = self._create_agent()
    
    def _initialize_llm(
        self,
        llm_provider: str,
        llm_model: Optional[str],
        temperature: float,
        api_key: Optional[str],
        **kwargs
    ) -> BaseChatModel:
        """Initialize the LLM based on provider."""
        if api_key and callable(api_key):
            raise ValueError(
                "API key must be a string, not a callable. "
                "For async operations, use async methods instead."
            )
        
        if llm_provider == "openai":
            model_name = llm_model or "gpt-5.1"
            llm_kwargs = {
                "model": model_name,
                "temperature": temperature,
                **kwargs
            }
            if api_key:
                llm_kwargs["api_key"] = api_key
            return ChatOpenAI(**llm_kwargs)
        elif llm_provider == "anthropic":
            model_name = llm_model or "claude-sonnet-4-5-20250929"
            llm_kwargs = {
                "model": model_name,
                "temperature": temperature,
                **kwargs
            }
            if api_key:
                llm_kwargs["api_key"] = api_key
            return ChatAnthropic(**llm_kwargs)
        elif llm_provider == "google":
            model_name = llm_model or "gemini-2.5-pro"
            llm_kwargs = {
                "model": model_name,
                "temperature": temperature,
                **kwargs
            }
            if api_key:
                llm_kwargs["google_api_key"] = api_key
            return ChatGoogleGenerativeAI(**llm_kwargs)
        else:
            raise ValueError(
                f"Unsupported LLM provider: {llm_provider}. "
                f"Supported providers: 'openai', 'anthropic', 'google'"
            )
    
    def _create_agent(self):
        """
        Create the LangChain 1.x agent using create_agent.
        
        The agent is responsible for:
        1. Analyzing user prompts to extract person attributes
        2. Constructing detailed prompts for model swap
        3. Calling Nano Banana Pro API with optimized parameters
        """
        # Determine which tool to use based on model
        tool_mapping = {
            "nano_banana": "nano_banana_model_swap",
            "nano_banana_pro": "nano_banana_pro_model_swap",
            "flux2_pro": "flux2_pro_model_swap",
            "flux2_flex": "flux2_flex_model_swap"
        }
        tool_name = tool_mapping.get(self.model, "nano_banana_pro_model_swap")
        
        # Build tool descriptions
        tool_descriptions = {
            "nano_banana": "nano_banana_model_swap: Uses Google's Gemini 2.5 Flash Image (Nano Banana) for fast model swapping at 1024px resolution. Good for quick iterations.",
            "nano_banana_pro": "nano_banana_pro_model_swap: Uses Google's Gemini 3 Pro Image Preview (Nano Banana Pro) for high-quality model swapping. Supports 1K, 2K, and 4K resolutions. Best for professional e-commerce quality.",
            "flux2_pro": "flux2_pro_model_swap: Uses FLUX 2 Pro for high-quality model swapping with custom width/height control. Professional quality results.",
            "flux2_flex": "flux2_flex_model_swap: Uses FLUX 2 Flex for advanced model swapping with guidance scale and steps control. Highest quality with fine-tuned parameters."
        }
        tool_description = tool_descriptions.get(self.model, tool_descriptions["nano_banana_pro"])
        
        system_prompt = f"""You are an expert fashion photography and model casting assistant. Your task is to analyze 
user requests for model swapping and extract detailed person attributes to generate professional product imagery.

Available tool:
- {tool_description}

User will provide:
1. An image of a person wearing an outfit
2. A description of the desired model/person to replace them with

Your task:
1. Analyze the user's prompt to extract person attributes:
   - Gender (male, female, non-binary, or unspecified)
   - Age range (teens, 20s, 30s, 40s, 50s+)
   - Ethnicity/appearance (Asian, African, Caucasian, Hispanic, Middle Eastern, mixed, diverse, or unspecified)
   - Body type (slim, athletic, average, curvy, plus-size, muscular)
   - Facial features (if specified: sharp features, soft features, distinctive characteristics)
   - Pose/expression (confident, casual, professional, friendly, serious, natural)
   - Styling preferences (professional, casual, editorial, commercial, lifestyle)

2. Construct a detailed, professional prompt for the model swap that:
   - Describes the desired model with extracted attributes
   - Emphasizes preserving the exact outfit, clothing, and styling
   - Maintains the original lighting, background, and composition
   - Ensures high-quality, professional photography standards

3. Select appropriate generation parameters based on the tool:
   - For nano_banana_pro_model_swap: Use "4K" resolution for professional e-commerce (default), "2K" for high-quality, "1K" for draft. Use search grounding if real-world references mentioned.
   - For nano_banana_model_swap: Optionally specify aspect ratio if needed.
   - For flux2_pro_model_swap and flux2_flex_model_swap: Use width/height if specified, otherwise use model defaults.

4. Call the {tool_name} tool with:
   - image: The input image path/URL
   - model_description: Your constructed detailed prompt
   - Additional parameters based on the tool (resolution, width/height, etc.)

5. Return the result as a JSON string with status, provider, and images fields

IMPORTANT PROMPT CONSTRUCTION GUIDELINES:
- Start with: "Professional fashion photography showing [person description] wearing the exact same outfit..."
- Be specific about preserving: clothing items, colors, patterns, textures, fit, styling
- Maintain: lighting setup, background, composition, camera angle, photo quality
- Emphasize photorealism and professional standards
- Keep the outfit and its details completely unchanged

Example good prompt construction:
User: "Replace with an athletic Asian woman in her 30s"
Your prompt: "Professional fashion photography showing an athletic Asian woman in her early 30s with 
confident posture, wearing the exact same outfit with all clothing details, patterns, and colors preserved 
perfectly. Maintain the original lighting, background, and composition. High-end e-commerce quality, 
photorealistic, professional model photography."

For nano_banana_pro, default to 4K resolution for professional quality unless the user specifies otherwise.
"""
        
        agent = create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=system_prompt
        )
        
        return agent
    
    def generate(
        self,
        image: str,
        prompt: str,
        resolution: Optional[str] = None,
        use_search_grounding: bool = False,
        verbose: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate model-swapped images using the agent.
        
        The agent analyzes the prompt to extract person attributes and calls
        Nano Banana Pro to swap the model while preserving the outfit.
        
        Args:
            image: Path or URL to the image of person wearing the outfit
            prompt: Natural language description of desired model/person.
                   Examples:
                   - "Replace with a professional male model in his 30s"
                   - "Athletic female model, Asian, mid-20s, confident pose"
                   - "Plus-size woman, African American, 40s, friendly expression"
            resolution: Optional resolution override. Options: "1K", "2K", "4K" (default: "4K")
            use_search_grounding: Whether to use Google Search grounding for real-world references
            verbose: If True, print debug information about agent reasoning
            **kwargs: Additional parameters to pass to the agent
        
        Returns:
            Dictionary containing:
            - 'status': 'success' or 'error'
            - 'provider': Model provider used (e.g., 'nano_banana_pro', 'flux2_pro', etc.)
            - 'images': List of generated images (base64 strings or PIL Images)
            - 'model_description': The detailed prompt used for generation
            - 'result': Full agent response
            - 'error': Error message (if status is 'error')
        
        Example:
            >>> agent = ModelSwapAgent()
            >>> result = agent.generate(
            ...     image="model.jpg",
            ...     prompt="Replace with a professional female model in her 30s, athletic build"
            ... )
            >>> images = result['images']
        """
        # Construct the input message for the agent
        user_message = f"""Image: {image}
Model Description: {prompt}
Model to use: {self.model}"""
        
        if resolution:
            user_message += f"\nResolution: {resolution}"
        
        if use_search_grounding:
            user_message += "\nUse search grounding: Yes"
        
        user_message += f"\n\nPlease perform model swap using {self.model} based on the description provided."
        
        try:
            # Execute the agent with streaming
            if verbose:
                print("\nAnalyzing prompt and extracting person attributes...")
            
            result = None
            last_message_count = 0
            
            async def stream_agent():
                nonlocal result, last_message_count
                try:
                    async for chunk in self.agent.astream(
                        {"messages": [{"role": "user", "content": user_message}]},
                        stream_mode="values",
                        **kwargs
                    ):
                        if isinstance(chunk, dict):
                            messages = chunk.get("messages", [])
                            if len(messages) > last_message_count:
                                for msg in messages[last_message_count:]:
                                    msg_type = getattr(msg, 'type', None) or (msg.get("type") if isinstance(msg, dict) else None)
                                    
                                    if msg_type == "ai":
                                        content = getattr(msg, 'content', None) or (msg.get("content") if isinstance(msg, dict) else "")
                                        if content and verbose:
                                            tool_calls = getattr(msg, 'tool_calls', None) or (msg.get("tool_calls") if isinstance(msg, dict) else [])
                                            if tool_calls:
                                                tool_names = []
                                                for tc in tool_calls:
                                                    if isinstance(tc, dict):
                                                        tool_names.append(tc.get("name", "unknown"))
                                                    else:
                                                        tool_names.append(getattr(tc, 'name', 'unknown'))
                                                if tool_names:
                                                    print(f"Calling tool: {', '.join(tool_names)}")
                                            elif content.strip() and len(content.strip()) > 10:
                                                if verbose:
                                                    print(f"Agent: {content[:200]}")
                                    
                                    elif msg_type == "tool":
                                        if verbose:
                                            tool_name = getattr(msg, 'name', None) or (msg.get("name") if isinstance(msg, dict) else "unknown")
                                            print(f"Tool '{tool_name}' executing...")
                                
                                last_message_count = len(messages)
                            
                            result = chunk.copy() if hasattr(chunk, 'copy') else chunk
                except Exception as e:
                    if verbose:
                        print(f"WARNING: Streaming error: {e}, falling back to standard execution...")
                    result = await self.agent.ainvoke(
                        {"messages": [{"role": "user", "content": user_message}]},
                        **kwargs
                    )
            
            # Run the streaming agent
            asyncio.run(stream_agent())
            
            # Fallback if no result
            if not result or not result.get("messages"):
                if verbose:
                    print("WARNING: No result from streaming, using standard execution...")
                result = asyncio.run(
                    self.agent.ainvoke(
                        {"messages": [{"role": "user", "content": user_message}]},
                        **kwargs
                    )
                )
            
            # Extract output from messages
            if not result:
                raise ValueError("Agent execution returned no result")
            
            messages = result.get("messages", [])
            if not messages:
                if verbose:
                    print(f"WARNING: No messages found in result")
                if isinstance(result, dict):
                    for key in ["messages", "output", "state"]:
                        if key in result:
                            potential_messages = result[key]
                            if isinstance(potential_messages, list):
                                messages = potential_messages
                                break
            
            output = ""
            tool_output = None
            
            if verbose:
                print(f"\nProcessing {len(messages)} messages...")
            
            # Extract tool output from messages
            for message in reversed(messages):
                message_type = None
                if hasattr(message, 'type'):
                    message_type = message.type
                elif isinstance(message, dict):
                    message_type = message.get("type") or message.get("message_type")
                
                if message_type == "tool" or (isinstance(message, dict) and message.get("type") == "tool"):
                    if hasattr(message, 'content'):
                        tool_output = message.content
                    elif isinstance(message, dict):
                        tool_output = message.get("content", "")
                    
                    if tool_output:
                        if verbose:
                            print(f"Tool output received")
                        try:
                            tool_result = json.loads(tool_output)
                            provider = tool_result.get("provider", "unknown")
                            if provider != "unknown":
                                print(f"Provider: {provider}")
                        except:
                            pass
                        break
                
                if not output and not tool_output:
                    if hasattr(message, 'content'):
                        content = message.content
                    elif isinstance(message, dict):
                        content = message.get("content", "")
                    else:
                        content = str(message)
                    
                    if content and content.strip():
                        output = content
            
            # Prefer tool output
            if tool_output:
                output = tool_output
            
            if not output and messages:
                output = str(messages[-1])
            
            # Parse JSON output
            parsed_result = None
            try:
                parsed_result = json.loads(output)
            except (json.JSONDecodeError, TypeError):
                try:
                    if "{" in output and "}" in output:
                        json_start = output.find("{")
                        json_end = output.rfind("}") + 1
                        json_str = output[json_start:json_end]
                        parsed_result = json.loads(json_str)
                except json.JSONDecodeError:
                    pass
            
            # Extract results
            if parsed_result:
                if parsed_result.get("status") == "error":
                    return {
                        "status": "error",
                        "provider": parsed_result.get("provider", self.model),
                        "images": [],
                        "error": parsed_result.get("error", "Unknown error from tool"),
                        "result": output,
                        "raw_output": result
                    }
                
                # Check for cache key
                cache_key = parsed_result.get("cache_key")
                if cache_key:
                    if verbose:
                        print(f"Retrieving images from cache (key: {cache_key[:8]}...)")
                    cached_data = get_tool_output_from_cache(cache_key)
                    if cached_data:
                        images = cached_data.get("images", [])
                        provider = cached_data.get("provider", parsed_result.get("provider", self.model))
                        model_description = cached_data.get("model_description", "")
                        if verbose:
                            print(f"Retrieved {len(images)} image(s) from cache")
                    else:
                        if verbose:
                            print("WARNING: Cache miss, trying alternative extraction...")
                        images = parsed_result.get("images", [])
                        provider = parsed_result.get("provider", self.model)
                        model_description = parsed_result.get("model_description", "")
                else:
                    if verbose:
                        print("Extracting images from tool output...")
                    images = parsed_result.get("images", [])
                    provider = parsed_result.get("provider", self.model)
                    model_description = parsed_result.get("model_description", "")
                
                if verbose:
                    print(f"Successfully generated {len(images)} image(s)")
                
                return {
                    "status": "success",
                    "provider": provider,
                    "images": images if isinstance(images, list) else [images] if images else [],
                    "model_description": model_description,
                    "result": output,
                    "raw_output": result
                }
            
            # Return error if parsing failed
            debug_info = f"Could not parse JSON from output. Output type: {type(output)}, Output preview: {str(output)[:200]}"
            if verbose:
                print(f"[DEBUG] {debug_info}")
            
            return {
                "status": "error",
                "provider": self.model,
                "images": [],
                "error": "Failed to parse tool output",
                "result": output,
                "raw_output": result,
                "debug_info": debug_info
            }
            
        except Exception as e:
            return {
                "status": "error",
                "provider": self.model,
                "images": [],
                "error": str(e),
                "raw_output": None
            }

