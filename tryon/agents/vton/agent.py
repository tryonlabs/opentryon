"""
Virtual Try-On Agent using LangChain

This agent uses LangChain 1.x to intelligently select and use the appropriate
virtual try-on adapter based on user prompts. The agent receives a person image,
garment image, and a natural language prompt, then decides which adapter to use.

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

from .tools import get_vton_tools, get_tool_output_from_cache


class VTOnAgent:
    """
    LangChain-based Virtual Try-On Agent.
    
    This agent intelligently selects and uses the appropriate virtual try-on
    adapter based on user prompts. It supports multiple adapters:
    - Kling AI
    - Amazon Nova Canvas
    - Segmind
    
    The agent analyzes the user's prompt to determine which adapter to use,
    then performs the virtual try-on operation.
    
    Example:
        >>> from tryon.agents.vton import VTOnAgent
        >>> 
        >>> agent = VTOnAgent(llm_provider="openai")
        >>> result = agent.generate(
        ...     person_image="person.jpg",
        ...     garment_image="shirt.jpg",
        ...     prompt="Use Kling AI to generate a virtual try-on"
        ... )
        >>> print(result)
    """
    
    # Provider name mappings for prompt matching
    PROVIDER_KEYWORDS = {
        "kling_ai": ["kling ai", "kling", "kolors"],
        "nova_canvas": ["nova canvas", "amazon nova", "aws", "bedrock", "amazon"],
        "segmind": ["segmind", "segmind try-on"],
    }
    
    def __init__(
        self,
        llm_provider: str = "openai",
        llm_model: Optional[str] = None,
        temperature: float = 0.0,
        api_key: Optional[str] = None,
        **llm_kwargs
    ):
        """
        Initialize the Virtual Try-On Agent.
        
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
        self.tools = get_vton_tools()
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
        # Ensure API key is a string, not a callable (for sync client compatibility)
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
            # Only add api_key if provided (let it use env var if not)
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
            # Only add api_key if provided (let it use env var if not)
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
            # Only add google_api_key if provided (let it use env var if not)
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
        system_prompt = """You are a helpful virtual try-on assistant. Your task is to analyze user requests and select
the appropriate virtual try-on tool based on the user's prompt.

Available tools:
- kling_ai_virtual_tryon: Use when user mentions "kling ai", "kling", or "kolors". Best for high-quality results.
- nova_canvas_virtual_tryon: Use when user mentions "nova canvas", "amazon nova", "aws", or "bedrock". Good for AWS integration.
- segmind_virtual_tryon: Use when user mentions "segmind". Fast and efficient for quick iterations.

User will provide:
1. Person image (path or URL)
2. Garment image (path or URL)
3. A prompt describing what they want

Your task:
1. Analyze the user's prompt to identify which provider they want to use
2. Extract any additional parameters from the prompt (e.g., garment class, category)
3. Call the appropriate tool with the person_image and garment_image
4. Return the result as a JSON string with status, provider, and images fields

If the user doesn't specify a provider, default to kling_ai_virtual_tryon for best quality.
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
        person_image: str,
        garment_image: str,
        prompt: str,
        verbose: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate virtual try-on images using the agent.
        
        The agent analyzes the prompt to determine which adapter to use,
        then performs the virtual try-on operation.
        
        Args:
            person_image: Path or URL to the person/model image
            garment_image: Path or URL to the garment/cloth image
            prompt: Natural language prompt describing the request.
                   Should mention the desired provider (e.g., "Use Kling AI",
                   "Generate with Nova Canvas", "Try Segmind")
            verbose: If True, print debug information about message parsing
            **kwargs: Additional parameters to pass to the agent
        
        Returns:
            Dictionary containing:
            - 'status': 'success' or 'error'
            - 'provider': Name of the provider used
            - 'images': List of generated images (URLs or base64 strings)
            - 'result': Full agent response
            - 'error': Error message (if status is 'error')
        
        Example:
            >>> agent = VTOnAgent()
            >>> result = agent.generate(
            ...     person_image="person.jpg",
            ...     garment_image="shirt.jpg",
            ...     prompt="Use Kling AI to create a virtual try-on of this shirt"
            ... )
            >>> print(result['images'])
        """
        # Construct the input message for the agent (LangChain 1.x format)
        user_message = f"""Person Image: {person_image}
Garment Image: {garment_image}
User Request: {prompt}

Please perform virtual try-on using the appropriate tool based on the user's request."""
        
        try:
            # Execute the agent with streaming to show intermediate steps
            if verbose:
                print("\n🤔 Analyzing request and selecting provider...")
            
            # Use streaming to capture intermediate steps
            result = None
            last_message_count = 0
            
            async def stream_agent():
                nonlocal result, last_message_count
                try:
                    # Use astream with stream_mode="values" to get full state at each step
                    async for chunk in self.agent.astream(
                        {"messages": [{"role": "user", "content": user_message}]},
                        stream_mode="values",
                        **kwargs
                    ):
                        # Process each chunk - chunk is the full state at each step
                        if isinstance(chunk, dict):
                            messages = chunk.get("messages", [])
                            if len(messages) > last_message_count:
                                # New messages added
                                for msg in messages[last_message_count:]:
                                    msg_type = getattr(msg, 'type', None) or (msg.get("type") if isinstance(msg, dict) else None)
                                    
                                    if msg_type == "ai":
                                        # Agent is thinking/responding
                                        content = getattr(msg, 'content', None) or (msg.get("content") if isinstance(msg, dict) else "")
                                        if content and verbose:
                                            # Check if agent is calling a tool
                                            tool_calls = getattr(msg, 'tool_calls', None) or (msg.get("tool_calls") if isinstance(msg, dict) else [])
                                            if tool_calls:
                                                tool_names = []
                                                for tc in tool_calls:
                                                    if isinstance(tc, dict):
                                                        tool_names.append(tc.get("name", "unknown"))
                                                    else:
                                                        tool_names.append(getattr(tc, 'name', 'unknown'))
                                                if tool_names:
                                                    print(f"🔧 Calling tool: {', '.join(tool_names)}")
                                            elif content.strip() and len(content.strip()) > 10:
                                                if verbose:
                                                    print(f"💭 Agent: {content[:200]}")
                                    
                                    elif msg_type == "tool":
                                        # Tool execution started/completed
                                        if verbose:
                                            tool_name = getattr(msg, 'name', None) or (msg.get("name") if isinstance(msg, dict) else "unknown")
                                            print(f"⚙️  Tool '{tool_name}' executing...")
                                
                                last_message_count = len(messages)
                            
                            # Always update result with latest chunk (final chunk has complete state)
                            result = chunk.copy() if hasattr(chunk, 'copy') else chunk
                except Exception as e:
                    if verbose:
                        print(f"⚠️  Streaming error: {e}, falling back to standard execution...")
                    # Fallback to non-streaming
                    result = await self.agent.ainvoke(
                        {"messages": [{"role": "user", "content": user_message}]},
                        **kwargs
                    )
            
            # Run the streaming agent
            asyncio.run(stream_agent())
            
            # If result is still None or empty, fallback to non-streaming
            if not result or not result.get("messages"):
                if verbose:
                    print("⚠️  No result from streaming, using standard execution...")
                result = asyncio.run(
                    self.agent.ainvoke(
                        {"messages": [{"role": "user", "content": user_message}]},
                        **kwargs
                    )
                )
            
            # Extract the output from messages (LangChain 1.x format)
            # Result contains messages list with the conversation history
            if not result:
                raise ValueError("Agent execution returned no result")
            
            messages = result.get("messages", [])
            if not messages:
                # If no messages, result might be in a different format
                if verbose:
                    print(f"⚠️  No messages found in result. Result keys: {list(result.keys()) if isinstance(result, dict) else 'not a dict'}")
                # Try to get messages from different possible locations
                if isinstance(result, dict):
                    # Check if messages are nested differently
                    for key in ["messages", "output", "state"]:
                        if key in result:
                            potential_messages = result[key]
                            if isinstance(potential_messages, list):
                                messages = potential_messages
                                break
            output = ""
            tool_output = None
            
            if verbose:
                print(f"\n📊 Processing {len(messages)} messages...")
                if messages:
                    for i, msg in enumerate(messages):
                        msg_type = getattr(msg, 'type', None) or (msg.get("type") if isinstance(msg, dict) else None)
                        msg_content = getattr(msg, 'content', None) or (msg.get("content") if isinstance(msg, dict) else str(msg))
                        print(f"  [{i}] {msg_type}: {str(msg_content)[:100]}")
                else:
                    print("  ⚠️  No messages to process")
                    if isinstance(result, dict):
                        print(f"  Result keys: {list(result.keys())}")
                        print(f"  Result preview: {str(result)[:500]}")
            
            # Look for tool outputs in messages (LangChain 1.x stores tool results in messages)
            for message in reversed(messages):
                # Check if this is a tool message with output
                message_type = None
                if hasattr(message, 'type'):
                    message_type = message.type
                elif isinstance(message, dict):
                    message_type = message.get("type") or message.get("message_type")
                
                # Tool messages contain the actual tool output
                # In LangChain 1.x, tool outputs are in messages with type "tool"
                if message_type == "tool" or (isinstance(message, dict) and message.get("type") == "tool"):
                    # Extract tool output
                    if hasattr(message, 'content'):
                        tool_output = message.content
                    elif isinstance(message, dict):
                        tool_output = message.get("content", "")
                    
                    if tool_output:
                        if verbose:
                            print(f"✅ Tool output received")
                        # Try to parse tool output to show provider
                        try:
                            tool_result = json.loads(tool_output)
                            provider = tool_result.get("provider", "unknown")
                            if provider != "unknown":
                                print(f"📸 Provider selected: {provider}")
                        except:
                            pass
                        break
                
                # Get assistant message content as fallback
                if not output and not tool_output:
                    if hasattr(message, 'content'):
                        content = message.content
                    elif isinstance(message, dict):
                        content = message.get("content", "")
                    else:
                        content = str(message)
                    
                    if content and content.strip():
                        output = content
            
            # Prefer tool output over assistant message
            if tool_output:
                output = tool_output
            
            # Fallback: convert last message to string if no content found
            if not output and messages:
                output = str(messages[-1])
            
            # Try to extract structured data from the output
            # The tool returns JSON strings, so parse them
            parsed_result = None
            try:
                # First, try to parse the entire output as JSON
                parsed_result = json.loads(output)
            except (json.JSONDecodeError, TypeError):
                # If that fails, look for JSON in the output text
                try:
                    if "{" in output and "}" in output:
                        json_start = output.find("{")
                        json_end = output.rfind("}") + 1
                        json_str = output[json_start:json_end]
                        parsed_result = json.loads(json_str)
                except json.JSONDecodeError:
                    pass
            
            # If we successfully parsed JSON, extract images
            if parsed_result:
                # Check if it's an error result
                if parsed_result.get("status") == "error":
                    return {
                        "status": "error",
                        "provider": parsed_result.get("provider", "unknown"),
                        "images": [],
                        "error": parsed_result.get("error", "Unknown error from tool"),
                        "result": output,
                        "raw_output": result
                    }
                
                # Check if we have a cache_key (new format to avoid token limits)
                cache_key = parsed_result.get("cache_key")
                if cache_key:
                    if verbose:
                        print(f"🔍 Retrieving images from cache (key: {cache_key[:8]}...)")
                    # Retrieve full images from cache
                    cached_data = get_tool_output_from_cache(cache_key)
                    if cached_data:
                        images = cached_data.get("images", [])
                        provider = cached_data.get("provider", parsed_result.get("provider", "unknown"))
                        if verbose:
                            print(f"✅ Retrieved {len(images)} image(s) from cache")
                    else:
                        if verbose:
                            print("⚠️  Cache miss, trying alternative extraction...")
                        # Cache miss, try to get from parsed result
                        images = parsed_result.get("images", [])
                        provider = parsed_result.get("provider", "unknown")
                else:
                    # Old format - extract directly from parsed result
                    if verbose:
                        print("📥 Extracting images from tool output...")
                    images = parsed_result.get("images", [])
                    provider = parsed_result.get("provider", "unknown")
                
                if verbose:
                    print(f"✅ Successfully extracted {len(images)} image(s) from {provider}")
                
                return {
                    "status": "success",
                    "provider": provider,
                    "images": images if isinstance(images, list) else [images] if images else [],
                    "result": output,
                    "raw_output": result
                }
            
            # Return text output if JSON parsing fails
            debug_info = f"Could not parse JSON from output. Output type: {type(output)}, Output preview: {str(output)[:200]}"
            if verbose:
                print(f"[DEBUG] {debug_info}")
                print(f"[DEBUG] Full output: {output}")
            
            return {
                "status": "success",
                "provider": "unknown",
                "images": [],
                "result": output,
                "raw_output": result,
                "debug_info": debug_info
            }
            
        except Exception as e:
            return {
                "status": "error",
                "provider": "unknown",
                "images": [],
                "error": str(e),
                "raw_output": None
            }
    
    def generate_and_decode(
        self,
        person_image: str,
        garment_image: str,
        prompt: str,
        **kwargs
    ) -> List:
        """
        Generate virtual try-on images and decode them to PIL Images.
        
        This is a convenience method that calls generate() and then decodes
        the resulting images to PIL Image objects.
        
        Args:
            person_image: Path or URL to the person/model image
            garment_image: Path or URL to the garment/cloth image
            prompt: Natural language prompt describing the request
            **kwargs: Additional parameters
        
        Returns:
            List of PIL Image objects
        
        Note:
            This method requires the adapters to support generate_and_decode().
            Currently, this is a placeholder that returns the raw result.
            Full implementation would decode base64 images or download URLs.
        """
        result = self.generate(
            person_image=person_image,
            garment_image=garment_image,
            prompt=prompt,
            **kwargs
        )
        
        # TODO: Implement image decoding based on result format
        # For now, return the raw result
        return result

