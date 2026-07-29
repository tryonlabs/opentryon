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
from tryon.agents.vton import VTOnAgent

def main():
    parser = argparse.ArgumentParser(
        description="Generate virtual try-on images using AI agent that intelligently selects the best provider",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
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
        """
    )
    
    # Required arguments
    parser.add_argument(
        '-p', '--person',
        type=str,
        required=True,
        help='Path or URL to person/model image'
    )
    
    parser.add_argument(
        '-g', '--garment',
        type=str,
        required=True,
        help='Path or URL to garment/cloth image'
    )
    
    parser.add_argument(
        '--prompt',
        type=str,
        required=True,
        help='Natural language prompt describing the virtual try-on request. The agent will select the provider based on keywords in the prompt (e.g., "Use Kling AI", "Generate with Nova Canvas", "Try Segmind")'
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
        help='Specific LLM model to use (e.g., "gpt-4-turbo-preview", "claude-3-opus-20240229", "gemini-pro"). If not specified, uses default model for the provider'
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
        help='Directory to save generated images. Default: outputs/'
    )
    
    parser.add_argument(
        '--save-base64',
        action='store_true',
        help='Also save Base64 encoded strings to .txt files (in addition to PNG images)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Print verbose output including agent reasoning steps'
    )
    
    args = parser.parse_args()
    
    # Validate file paths (if they're local files, not URLs)
    if not args.person.startswith(('http://', 'https://')):
        if not os.path.exists(args.person):
            raise FileNotFoundError(f"Person image not found: {args.person}")
    
    if not args.garment.startswith(('http://', 'https://')):
        if not os.path.exists(args.garment):
            raise FileNotFoundError(f"Garment image not found: {args.garment}")
    
    # Create output directory if it doesn't exist
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize agent
    print(f"Initializing Virtual Try-On Agent...")
    print(f"  LLM Provider: {args.llm_provider}")
    if args.llm_model:
        print(f"  LLM Model: {args.llm_model}")
    print(f"  Temperature: {args.llm_temperature}")
    
    try:
        agent = VTOnAgent(
            llm_provider=args.llm_provider,
            llm_model=args.llm_model,
            temperature=args.llm_temperature,
            api_key=args.llm_api_key
        )
    except ValueError as e:
        print(f"\n✗ Error initializing agent: {e}")
        print("\nPlease ensure:")
        print("  1. Required LLM API key is set in environment variables or --llm-api-key")
        print("  2. LangChain dependencies are installed: pip install langchain langchain-openai langchain-anthropic langchain-google-genai")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error initializing agent: {e}")
        return 1
    
    # Generate virtual try-on
    print(f"\n{'='*60}")
    print(f"🚀 Starting Virtual Try-On Generation")
    print(f"{'='*60}")
    print(f"  👤 Person image: {args.person}")
    print(f"  👕 Garment image: {args.garment}")
    print(f"  💬 Prompt: {args.prompt}")
    print(f"{'='*60}\n")
    
    try:
        # Always show progress (verbose controls detail level)
        result = agent.generate(
            person_image=args.person,
            garment_image=args.garment,
            prompt=args.prompt,
            verbose=True  # Always show intermediate steps
        )
        
        if args.verbose:
            print(f"\n📋 Full agent result:")
            print(json.dumps(result, indent=2, default=str))
        
        if result["status"] == "error":
            print(f"\n{'='*60}")
            print(f"❌ Error: {result.get('error', 'Unknown error')}")
            print(f"{'='*60}")
            return 1
        
        # Extract images
        images = result.get("images", [])
        provider = result.get("provider", "unknown")
        
        if not images:
            print(f"\n{'='*60}")
            print(f"❌ Error: No images generated")
            print(f"{'='*60}")
            return 1
        
        print(f"\n{'='*60}")
        print(f"✅ Successfully generated {len(images)} image(s) using {provider}")
        print(f"{'='*60}")
        
        # Process and save images
        saved_images = []
        for idx, image_data in enumerate(images):
            try:
                # Handle different image formats
                if isinstance(image_data, str):
                    # Check if it's a URL
                    if image_data.startswith(('http://', 'https://')):
                        # Download image from URL
                        img_response = requests.get(image_data)
                        img_response.raise_for_status()
                        image_bytes = img_response.content
                        image = Image.open(io.BytesIO(image_bytes))
                    else:
                        # Assume it's base64
                        image_bytes = base64.b64decode(image_data)
                        image = Image.open(io.BytesIO(image_bytes))
                else:
                    # Already bytes or PIL Image
                    if isinstance(image_data, bytes):
                        image = Image.open(io.BytesIO(image_data))
                    else:
                        image = image_data
                
                # Save PNG
                output_path = output_dir / f"vton_agent_result_{idx}.png"
                image.save(output_path)
                saved_images.append(output_path)
                print(f"💾 Saved image {idx + 1}/{len(images)}: {output_path}")
                
                # Optionally save Base64
                if args.save_base64:
                    buffer = io.BytesIO()
                    image.save(buffer, format='PNG')
                    image_bytes = buffer.getvalue()
                    image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                    
                    output_path_txt = output_dir / f"vton_agent_result_{idx}.txt"
                    with open(output_path_txt, 'w') as f:
                        f.write(image_base64)
                    print(f"💾 Saved Base64 string {idx + 1}: {output_path_txt}")
                    
            except Exception as e:
                print(f"✗ Error processing image {idx + 1}: {e}")
                continue
        
        print(f"\n{'='*60}")
        print(f"🎉 Complete! Saved {len(saved_images)} image(s) to {output_dir}")
        print(f"{'='*60}")
        return 0
        
    except ValueError as e:
        print(f"\n✗ Error: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())

