"""
Fashion Agent using LangChain

This agent uses LangChain 1.x to intelligently perform various fashion-related tasks
including virtual try-on, image generation, video generation, image editing, model swapping,
and fashion preprocessing. The agent analyzes user requests and selects the appropriate tools
to accomplish the task.

Based on LangChain 1.x API: https://docs.langchain.com/oss/python/langchain/agents
"""

import json
import asyncio
from typing import Optional, Dict, Any, List, Union

# LangChain 1.x imports
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.language_models import BaseChatModel

from tryon.tools import get_all_tools, get_tool_output_cache


def _run_async(coro):
    """
    Run an async coroutine, handling both regular Python and Jupyter notebook environments.
    
    In Jupyter notebooks, there's already an event loop running, so we need to use
    nest_asyncio to allow nested event loops, or run in a separate thread.
    
    Args:
        coro: The coroutine to run
        
    Returns:
        The result of the coroutine
    """
    try:
        # Check if there's already a running event loop
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No running loop, we can use asyncio.run()
        return asyncio.run(coro)
    
    # There's a running loop (e.g., in Jupyter), use nest_asyncio or thread
    try:
        import nest_asyncio
        nest_asyncio.apply()
        return asyncio.run(coro)
    except ImportError:
        # nest_asyncio not available, run in a new thread
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, coro)
            return future.result()


class FashionAgent:
    """
    LangChain-based Fashion Agent.
    
    This agent intelligently performs various fashion-related tasks by analyzing
    user prompts and selecting appropriate tools. It supports:
    - Virtual Try-On (Kling AI, Nova Canvas, Segmind)
    - Image Generation (Nano Banana, FLUX, GPT-Image, Luma AI)
    - Video Generation (Sora, Veo, Luma AI)
    - Model Swapping (Nano Banana Pro, FLUX 2 Pro/Flex)
    - Image Editing (GPT-Image editing, mask-based editing, composition)
    - Fashion Preprocessing (garment segmentation, pose estimation)
    
    The agent analyzes the user's prompt to determine which tools to use,
    then performs the requested operations.
    
    Example:
        >>> from tryon.agents.fashion import FashionAgent
        >>> 
        >>> agent = FashionAgent(llm_provider="openai")
        >>> result = agent.generate(
        ...     prompt="Generate a virtual try-on of this shirt on this model using Kling AI"
        ... )
        >>> print(result)
    """
    
    def __init__(
        self,
        llm_provider: str = "openai",
        llm_model: Optional[str] = None,
        temperature: float = 0.0,
        api_key: Optional[str] = None,
        **llm_kwargs
    ):
        """
        Initialize the Fashion Agent.
        
        Args:
            llm_provider: LLM provider to use. Options: "openai", "anthropic", "google"
            llm_model: Specific model name (e.g., "gpt-4", "claude-3-opus-20240229")
                     If None, uses default model for the provider
            temperature: Temperature for LLM (default: 0.0 for deterministic behavior)
            api_key: API key for the LLM provider (if not set via environment variable)
            **llm_kwargs: Additional keyword arguments for LLM initialization
        
        Raises:
            ValueError: If llm_provider is not supported
        """
        self.llm_provider = llm_provider.lower()
        self.tools = get_all_tools()
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
            model_name = llm_model or "gpt-4o"
            llm_kwargs = {
                "model": model_name,
                "temperature": temperature,
                **kwargs
            }
            if api_key:
                llm_kwargs["api_key"] = api_key
            return ChatOpenAI(**llm_kwargs)
        elif llm_provider == "anthropic":
            model_name = llm_model or "claude-sonnet-4-20250514"
            llm_kwargs = {
                "model": model_name,
                "temperature": temperature,
                **kwargs
            }
            if api_key:
                llm_kwargs["api_key"] = api_key
            return ChatAnthropic(**llm_kwargs)
        elif llm_provider == "google":
            model_name = llm_model or "gemini-2.0-flash-exp"
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
        
        Reference: https://docs.langchain.com/oss/python/langchain/agents
        """
        system_prompt = """You are a helpful fashion AI assistant with access to a comprehensive set of tools
for virtual try-on, image generation, video generation, image editing, model swapping, and fashion preprocessing.

IMPORTANT: You MUST ONLY use the tools that are available to you. Do NOT attempt to perform tasks outside of your scope.
If a user's query does not relate to any of the available tools or capabilities, politely decline and provide a helpful response.

Your capabilities include:

1. VIRTUAL TRY-ON:
   - kling_ai_virtual_tryon: High-quality virtual try-on (best quality, supports high-res)
   - nova_canvas_virtual_tryon: Amazon Nova Canvas via AWS Bedrock
   - segmind_virtual_tryon: Fast and efficient try-on

2. IMAGE GENERATION:
   - nano_banana_text_to_image: Fast image generation (Google Gemini 2.5 Flash)
   - nano_banana_pro_text_to_image: High-quality 4K images (Google Gemini 3 Pro)
   - flux2_pro_text_to_image: Professional quality images
   - flux2_flex_text_to_image: Fast and flexible generation
   - gpt_image_text_to_image: OpenAI GPT-Image (excellent prompt understanding)
   - luma_ai_text_to_image: Luma AI image generation

3. VIDEO GENERATION:
   - sora_text_to_video: OpenAI Sora (text-to-video, excellent quality)
   - sora_image_to_video: OpenAI Sora (image-to-video, animate images)
   - veo_text_to_video: Google Veo 3 (text-to-video, cinematic)
   - veo_image_to_video: Google Veo 3 (image-to-video)
   - luma_ai_text_to_video: Luma AI Dream Machine (text-to-video)
   - luma_ai_image_to_video: Luma AI Dream Machine (image-to-video)

4. MODEL SWAPPING:
   - nano_banana_pro_model_swap: Swap models while preserving outfits (4K quality)
   - flux2_pro_model_swap: High-quality model swapping
   - flux2_flex_model_swap: Fast model swapping

5. IMAGE EDITING:
   - gpt_image_edit: Edit images with text prompts
   - gpt_image_mask_edit: Edit specific regions using masks
   - gpt_image_multi_edit: Compose multiple images together

6. FASHION PREPROCESSING:
   - Garment preprocessing and segmentation (coming soon)
   - Pose estimation (coming soon)

TASK HANDLING GUIDELINES:

- For virtual try-on requests: Use kling_ai_virtual_tryon (best quality), nova_canvas_virtual_tryon (AWS integration), or segmind_virtual_tryon (fast)
- For image generation: Choose based on quality/speed needs. Use nano_banana_pro_text_to_image for best quality, flux2_flex for speed
- For video generation: Use sora_text_to_video for best quality, veo_text_to_video for cinematic, luma_ai for alternatives
- For model swapping: Use nano_banana_pro_model_swap for best outfit preservation
- For image editing: Use gpt_image_edit for general edits, gpt_image_mask_edit for precise region edits
- For multi-step tasks: Break them down and use multiple tools in sequence

OUT-OF-SCOPE HANDLING:
If a user's query does not relate to any of the available tools or is outside your scope, respond politely without using any tools.
Return a JSON response with status "out_of_scope" and a helpful message like:

"I'm sorry, but your query doesn't relate to the fashion-related tasks I can help with. I can assist you with the following:

• Virtual Try-On: Try on garments on models using different providers
• Image Generation: Generate fashion images from text descriptions
• Video Generation: Create fashion videos from text or images
• Model Swapping: Replace models in images while preserving outfits
• Image Editing: Edit fashion images, apply masks, or compose multiple images

Please let me know which of these tasks you'd like help with, and I'll be happy to assist!"

USER INPUT FORMAT:
Users will provide natural language requests. Extract:
- Task type (virtual try-on, image generation, video generation, etc.)
- Required inputs (images, prompts, parameters)
- Preferences (model/provider, quality settings, etc.)

Always return results as JSON with status, provider/tool used, and cache_key for retrieving full outputs.
If the user doesn't specify a provider/model, choose the best default based on quality needs.
"""
        
        # Create agent using LangChain 1.x API
        agent = create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=system_prompt
        )
        
        return agent
    
    def generate(
        self,
        prompt: str,
        person_image: Optional[str] = None,
        garment_image: Optional[str] = None,
        image: Optional[str] = None,
        images: Optional[List[str]] = None,
        verbose: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate fashion-related content using the agent.
        
        The agent analyzes the prompt to determine which tools to use,
        then performs the requested operations.
        
        Args:
            prompt: Natural language prompt describing the request.
                   Examples:
                   - "Generate a virtual try-on of this shirt on this model using Kling AI"
                   - "Create a fashion image of a model wearing an elegant evening gown"
                   - "Generate a video of a model walking on a runway"
                   - "Swap the model in this image while preserving the outfit"
                   - "Edit this image to change the dress color to blue"
            person_image: Path or URL to person/model image (for virtual try-on)
            garment_image: Path or URL to garment/cloth image (for virtual try-on)
            image: Path or URL to image (for model swap, image editing, image-to-video)
            images: List of image paths/URLs (for multi-image composition)
            verbose: If True, print debug information
            **kwargs: Additional parameters to pass to the agent
        
        Returns:
            Dictionary containing:
            - 'status': 'success' or 'error'
            - 'tool': Name of the tool used
            - 'result': Full agent response
            - 'cache_key': Cache key for retrieving full outputs
            - 'error': Error message (if status is 'error')
        
        Example:
            >>> agent = FashionAgent()
            >>> result = agent.generate(
            ...     prompt="Generate a virtual try-on using Kling AI",
            ...     person_image="person.jpg",
            ...     garment_image="shirt.jpg"
            ... )
            >>> print(result['status'])
        """
        # Construct the input message for the agent
        user_message_parts = [f"User Request: {prompt}"]
        
        if person_image:
            user_message_parts.append(f"Person/Model Image: {person_image}")
        if garment_image:
            user_message_parts.append(f"Garment/Cloth Image: {garment_image}")
        if image:
            user_message_parts.append(f"Image: {image}")
        if images:
            user_message_parts.append(f"Images: {', '.join(images)}")
        
        user_message = "\n".join(user_message_parts) + "\n\nPlease perform the requested fashion-related task using the appropriate tools."
        
        try:
            if verbose:
                print("\nAnalyzing request and selecting appropriate tools...")
            
            # Execute the agent
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
                                    
                                    elif msg_type == "tool":
                                        if verbose:
                                            tool_name = getattr(msg, 'name', None) or (msg.get("name") if isinstance(msg, dict) else "unknown")
                                            print(f"Tool '{tool_name}' executing...")
                                
                                last_message_count = len(messages)
                            
                            result = chunk.copy() if hasattr(chunk, 'copy') else chunk
                except Exception as e:
                    if verbose:
                        print(f"Streaming error: {e}, falling back to standard execution...")
                    result = await self.agent.ainvoke(
                        {"messages": [{"role": "user", "content": user_message}]},
                        **kwargs
                    )
            
            # Run the streaming agent (handles both regular Python and Jupyter environments)
            _run_async(stream_agent())
            
            # Fallback to non-streaming if needed
            if not result or not result.get("messages"):
                if verbose:
                    print("No result from streaming, using standard execution...")
                result = _run_async(
                    self.agent.ainvoke(
                        {"messages": [{"role": "user", "content": user_message}]},
                        **kwargs
                    )
                )
            
            # Extract the output from messages
            if not result:
                raise ValueError("Agent execution returned no result")
            
            messages = result.get("messages", [])
            if not messages:
                if isinstance(result, dict):
                    for key in ["messages", "output", "state"]:
                        if key in result:
                            potential_messages = result[key]
                            if isinstance(potential_messages, list):
                                messages = potential_messages
                                break
            
            output = ""
            tool_output = None
            tool_name = None
            
            if verbose:
                print(f"\nProcessing {len(messages)} messages...")
            
            # Look for tool outputs in messages
            for message in reversed(messages):
                msg_type = getattr(message, 'type', None) or (message.get("type") if isinstance(message, dict) else None)
                
                if msg_type == "tool":
                    # This is a tool output
                    tool_output_raw = getattr(message, 'content', None) or (message.get("content") if isinstance(message, dict) else "")
                    tool_name = getattr(message, 'name', None) or (message.get("name") if isinstance(message, dict) else "unknown")
                    
                    if tool_output_raw:
                        try:
                            tool_output = json.loads(tool_output_raw) if isinstance(tool_output_raw, str) else tool_output_raw
                            if verbose:
                                print(f"Tool '{tool_name}' completed")
                        except json.JSONDecodeError:
                            tool_output = {"raw_output": tool_output_raw}
                    break
                elif msg_type == "ai":
                    # This is the AI's final response
                    content = getattr(message, 'content', None) or (message.get("content") if isinstance(message, dict) else "")
                    if content and not output:
                        output = content
            
            # Build result dictionary
            if tool_output and tool_output.get("status") == "success":
                return {
                    "status": "success",
                    "tool": tool_name or "unknown",
                    "provider": tool_output.get("provider", "unknown"),
                    "cache_key": tool_output.get("cache_key"),
                    "image_count": tool_output.get("image_count", 1),
                    "result": output,
                    "tool_output": tool_output,
                    "messages": messages
                }
            elif tool_output and tool_output.get("status") == "error":
                return {
                    "status": "error",
                    "tool": tool_name or "unknown",
                    "error": tool_output.get("error", "Unknown error"),
                    "message": tool_output.get("message", "Tool execution failed"),
                    "result": output
                }
            elif tool_output and tool_output.get("status") == "out_of_scope":
                return {
                    "status": "out_of_scope",
                    "message": tool_output.get("message", "Query is outside the scope of available tools"),
                    "result": output,
                    "messages": messages
                }
            else:
                # No tool output found - check if output suggests out-of-scope query
                # If no tool was called and we have a response, it might be out-of-scope
                if output and not tool_name:
                    # Check if the output contains out-of-scope indicators
                    output_lower = output.lower()
                    if any(indicator in output_lower for indicator in ["doesn't relate", "outside", "cannot help", "can't help", "not able", "out of scope"]):
                        return {
                            "status": "out_of_scope",
                            "message": output,
                            "result": output,
                            "messages": messages
                        }
                
                # Default: return the agent's response
                return {
                    "status": "success" if output else "unknown",
                    "result": output,
                    "messages": messages
                }
        
        except Exception as e:
            if verbose:
                print(f"Error: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "message": f"Agent execution failed: {str(e)}"
            }
    
    def get_cached_output(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached output using cache key.
        
        Args:
            cache_key: Cache key from tool output
        
        Returns:
            Dictionary containing cached data, or None if not found
        """
        cache = get_tool_output_cache()
        return cache.get(cache_key)

