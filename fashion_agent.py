from dotenv import load_dotenv
load_dotenv()

import os
import json
import argparse
import base64
import io
import requests
from pathlib import Path
from PIL import Image
from tryon.agents.fashion import FashionAgent
from tryon.tools import get_tool_output_cache

def main():
    parser = argparse.ArgumentParser(
        description="Fashion Agent CLI - Perform various fashion-related tasks using AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Virtual Try-On
  python fashion_agent.py --prompt "Generate a virtual try-on using Kling AI" --person person.jpg --garment shirt.jpg
  
  # Image Generation
  python fashion_agent.py --prompt "Generate a professional fashion photo of a model wearing an elegant evening gown"
  
  # Video Generation
  python fashion_agent.py --prompt "Generate a video of a fashion model walking on a runway" --image model.jpg
  
  # Model Swapping
  python fashion_agent.py --prompt "Replace the model with a professional Asian female model in her 30s, athletic build" --image person_wearing_outfit.jpg
  
  # Image Editing
  python fashion_agent.py --prompt "Change the dress color to midnight blue" --image fashion_photo.jpg
  
  # Multi-Image Composition
  python fashion_agent.py --prompt "Combine these outfit images into a fashion collage" --images outfit1.jpg outfit2.jpg outfit3.jpg
  
  # Use different LLM provider
  python fashion_agent.py --prompt "Generate a virtual try-on" --person person.jpg --garment shirt.jpg --llm-provider anthropic
  
  # Verbose output
  python fashion_agent.py --prompt "Generate fashion image" --verbose

Capabilities:
  - Virtual Try-On (Kling AI, Nova Canvas, Segmind)
  - Image Generation (Nano Banana, FLUX, GPT-Image, Luma AI)
  - Video Generation (Sora, Veo, Luma AI)
  - Model Swapping (preserve outfits, swap models)
  - Image Editing (GPT-Image editing, mask-based editing)
  - Multi-Image Composition
        """
    )
    
    # Required: prompt
    parser.add_argument(
        '--prompt',
        type=str,
        required=True,
        help='Natural language prompt describing the task. Examples: "Generate virtual try-on", "Create fashion image", "Generate video", "Swap model", "Edit image"'
    )
    
    # Optional inputs (agent will determine what's needed based on prompt)
    parser.add_argument(
        '--person',
        type=str,
        default=None,
        help='Path or URL to person/model image (for virtual try-on)'
    )
    
    parser.add_argument(
        '--garment',
        type=str,
        default=None,
        help='Path or URL to garment/cloth image (for virtual try-on)'
    )
    
    parser.add_argument(
        '-i', '--image',
        type=str,
        default=None,
        help='Path or URL to image (for model swap, image editing, image-to-video)'
    )
    
    parser.add_argument(
        '--images',
        type=str,
        nargs='+',
        default=None,
        help='List of image paths/URLs (for multi-image composition)'
    )
    
    # LLM configuration
    parser.add_argument(
        '--llm-provider',
        type=str,
        default='openai',
        choices=['openai', 'anthropic', 'google'],
        help='LLM provider to use for the agent. Options: openai (default), anthropic, google'
    )
    
    parser.add_argument(
        '--llm-model',
        type=str,
        default=None,
        help='Specific LLM model to use (e.g., "gpt-4o", "claude-sonnet-4-20250514", "gemini-2.0-flash-exp"). If not specified, uses default model for the provider'
    )
    
    parser.add_argument(
        '--llm-temperature',
        type=float,
        default=0.0,
        help='Temperature for LLM (default: 0.0 for deterministic behavior). Range: 0.0-2.0'
    )
    
    parser.add_argument(
        '--llm-api-key',
        type=str,
        default=None,
        help='API key for LLM provider (if not set via environment variable). For OpenAI: OPENAI_API_KEY, Anthropic: ANTHROPIC_API_KEY, Google: GOOGLE_API_KEY'
    )
    
    # Output configuration
    parser.add_argument(
        '-o', '--output-dir',
        type=str,
        default='outputs',
        help='Directory to save generated outputs. Default: outputs/'
    )
    
    parser.add_argument(
        '--save-base64',
        action='store_true',
        help='Also save Base64 encoded strings to .txt files (in addition to PNG/MP4 files)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Print verbose output including agent reasoning steps and full results'
    )
    
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results in JSON format (useful for integration with other applications)'
    )
    
    args = parser.parse_args()
    
    # Validate file paths (if they're local files, not URLs)
    for file_arg, file_path in [
        ('person', args.person),
        ('garment', args.garment),
        ('image', args.image),
    ]:
        if file_path and not file_path.startswith(('http://', 'https://')):
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"{file_arg.capitalize()} file not found: {file_path}")
    
    if args.images:
        for img_path in args.images:
            if not img_path.startswith(('http://', 'https://')):
                if not os.path.exists(img_path):
                    raise FileNotFoundError(f"Image file not found: {img_path}")
    
    # Create output directory if it doesn't exist
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize agent
    print(f"Initializing Fashion Agent...")
    print(f"  LLM Provider: {args.llm_provider}")
    if args.llm_model:
        print(f"  LLM Model: {args.llm_model}")
    print(f"  Temperature: {args.llm_temperature}")
    
    try:
        agent = FashionAgent(
            llm_provider=args.llm_provider,
            llm_model=args.llm_model,
            temperature=args.llm_temperature,
            api_key=args.llm_api_key
        )
    except ValueError as e:
        print(f"\nError initializing agent: {e}")
        print("\nPlease ensure:")
        print("  1. Required LLM API key is set in environment variables or --llm-api-key")
        print("  2. LangChain dependencies are installed: pip install langchain langchain-openai langchain-anthropic langchain-google-genai")
        return 1
    except Exception as e:
        print(f"\nUnexpected error initializing agent: {e}")
        return 1
    
    # Prepare inputs (only show if not JSON output)
    if not args.json:
        print(f"\n{'='*60}")
        print(f"Task Information")
        print(f"{'='*60}")
        print(f"  Prompt: {args.prompt}")
        if args.person:
            print(f"  Person image: {args.person}")
        if args.garment:
            print(f"  Garment image: {args.garment}")
        if args.image:
            print(f"  Image: {args.image}")
        if args.images:
            print(f"  Images ({len(args.images)}): {', '.join(args.images)}")
        print(f"{'='*60}\n")
    
    try:
        # Generate with agent
        result = agent.generate(
            prompt=args.prompt,
            person_image=args.person,
            garment_image=args.garment,
            image=args.image,
            images=args.images,
            verbose=args.verbose and not args.json  # Don't show progress in JSON mode
        )
        
        # If JSON output is requested, output JSON and exit
        if args.json:
            json_output = {
                "status": result.get("status", "unknown"),
                "tool": result.get("tool"),
                "provider": result.get("provider"),
                "message": result.get("message") or result.get("result"),
                "error": result.get("error"),
            }
            
            # Add cache_key if available
            cache_key = result.get("cache_key")
            if cache_key:
                json_output["cache_key"] = cache_key
            
            print(json.dumps(json_output, indent=2, default=str))
            return 0 if result.get("status") != "error" else 1
        
        # Non-JSON output (original behavior)
        if args.verbose:
            print(f"\nFull agent result:")
            print(json.dumps(result, indent=2, default=str))
        
        if result["status"] == "error":
            print(f"\n{'='*60}")
            print(f"Error: {result.get('error', 'Unknown error')}")
            if result.get('message'):
                print(f"   {result['message']}")
            print(f"{'='*60}")
            return 1
        
        # Handle out-of-scope queries
        if result.get("status") == "out_of_scope":
            print(f"\n{'='*60}")
            print(f"{result.get('message', 'Query is outside the scope of available tools')}")
            print(f"{'='*60}")
            return 0
        
        # Extract information
        tool_name = result.get("tool", "unknown")
        provider = result.get("provider", "unknown")
        cache_key = result.get("cache_key")
        
        if not cache_key:
            # This might be a response without tool usage (e.g., informational query)
            if result.get("result"):
                print(f"\n{'='*60}")
                print(f"Response: {result.get('result')}")
                print(f"{'='*60}")
            return 0
        
        # Retrieve cached output
        cache = get_tool_output_cache()
        cached_data = cache.get(cache_key)
        
        if not cached_data:
            print(f"\n{'='*60}")
            print(f"Warning: Cache data not found for key: {cache_key}")
            print(f"{'='*60}")
            if args.verbose:
                print(f"\nResult: {result.get('result', 'No result text')}")
            return 0
        
        print(f"\n{'='*60}")
        print(f"Successfully completed task using {tool_name} ({provider})")
        print(f"{'='*60}")
        
        # Handle different output types
        saved_files = []
        
        # Check for images
        if "images" in cached_data:
            images = cached_data["images"]
            if images:
                print(f"\nSaving {len(images)} image(s)...")
                for idx, image_data in enumerate(images):
                    try:
                        # Handle different image formats
                        if isinstance(image_data, str):
                            if image_data.startswith(('http://', 'https://')):
                                img_response = requests.get(image_data)
                                img_response.raise_for_status()
                                image_bytes = img_response.content
                                image = Image.open(io.BytesIO(image_bytes))
                            else:
                                image_bytes = base64.b64decode(image_data)
                                image = Image.open(io.BytesIO(image_bytes))
                        elif isinstance(image_data, bytes):
                            image = Image.open(io.BytesIO(image_data))
                        elif isinstance(image_data, Image.Image):
                            image = image_data
                        else:
                            if hasattr(image_data, 'save'):
                                image = image_data
                            else:
                                print(f"Skipping image {idx + 1}: Unsupported format")
                                continue
                        
                        # Save PNG
                        output_path = output_dir / f"fashion_result_{idx}.png"
                        image.save(output_path)
                        saved_files.append(output_path)
                        print(f"  Saved image {idx + 1}/{len(images)}: {output_path}")
                        
                        # Optionally save Base64
                        if args.save_base64:
                            buffer = io.BytesIO()
                            image.save(buffer, format='PNG')
                            image_bytes = buffer.getvalue()
                            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                            
                            output_path_txt = output_dir / f"fashion_result_{idx}.txt"
                            with open(output_path_txt, 'w') as f:
                                f.write(image_base64)
                            print(f"  Saved Base64: {output_path_txt}")
                            
                    except Exception as e:
                        print(f"  Error processing image {idx + 1}: {e}")
                        continue
        
        # Check for video bytes
        if "video_bytes" in cached_data:
            video_bytes = cached_data["video_bytes"]
            if video_bytes:
                print(f"\nSaving video...")
                try:
                    output_path = output_dir / f"fashion_result_video.mp4"
                    with open(output_path, 'wb') as f:
                        if isinstance(video_bytes, bytes):
                            f.write(video_bytes)
                        else:
                            # Handle other byte-like objects
                            f.write(bytes(video_bytes))
                    saved_files.append(output_path)
                    print(f"  Saved video: {output_path}")
                    
                    # Optionally save Base64
                    if args.save_base64:
                        video_base64 = base64.b64encode(video_bytes if isinstance(video_bytes, bytes) else bytes(video_bytes)).decode('utf-8')
                        output_path_txt = output_dir / f"fashion_result_video.txt"
                        with open(output_path_txt, 'w') as f:
                            f.write(video_base64)
                        print(f"  Saved Base64: {output_path_txt}")
                        
                except Exception as e:
                    print(f"  Error saving video: {e}")
        
        print(f"\n{'='*60}")
        print(f"Complete! Saved {len(saved_files)} file(s) to {output_dir}")
        print(f"{'='*60}")
        
        # Print tips
        print(f"\nTips:")
        print(f"  • The agent automatically selects the best tools based on your prompt")
        print(f"  • Be specific in prompts for better results")
        print(f"  • Use --verbose to see detailed agent reasoning")
        print(f"  • Try different task types: virtual try-on, image generation, video generation, model swap, image editing")
        
        return 0
        
    except ValueError as e:
        print(f"\nError: {e}")
        return 1
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())

