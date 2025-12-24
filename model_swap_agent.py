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
from tryon.agents.model_swap import ModelSwapAgent

def main():
    parser = argparse.ArgumentParser(
        description="Swap models in images using AI agent while preserving outfit and styling",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage - replace with professional male model (uses Nano Banana Pro by default)
  python model_swap_agent.py --image model.jpg --prompt "Replace with a professional male model in his 30s, athletic build"
  
  # Use FLUX 2 Pro for high-quality results
  python model_swap_agent.py --image model.jpg --prompt "Replace with a professional female model" --model flux2_pro
  
  # Use FLUX 2 Flex for advanced control
  python model_swap_agent.py --image model.jpg --prompt "Replace with an athletic Asian model" --model flux2_flex
  
  # Use Nano Banana for fast generation
  python model_swap_agent.py --image model.jpg --prompt "Replace with a professional model" --model nano_banana
  
  # Specify detailed attributes with specific model
  python model_swap_agent.py --image outfit.jpg --prompt "Asian female model, mid-20s, athletic, confident pose" --model nano_banana_pro
  
  # Use different LLM provider
  python model_swap_agent.py --image model.jpg --prompt "Plus-size woman, African American, 40s" --llm-provider anthropic --model flux2_pro
  
  # Specify resolution (for Nano Banana Pro)
  python model_swap_agent.py --image model.jpg --prompt "Male model in his 30s" --resolution 2K --model nano_banana_pro
  
  # Use Google Search grounding for real-world references (Nano Banana Pro only)
  python model_swap_agent.py --image model.jpg --prompt "Model like professional fashion runway" --search-grounding --model nano_banana_pro
  
  # Use URLs instead of file paths
  python model_swap_agent.py --image https://example.com/model.jpg --prompt "Female model, 30s, professional" --model flux2_pro

Use Cases:
  - E-commerce sellers creating professional product imagery
  - Fashion brands showcasing clothing on diverse models
  - Clothing brands generating model portfolios
  - Product photography with consistent styling across models
        """
    )
    
    # Required arguments
    parser.add_argument(
        '-i', '--image',
        type=str,
        required=True,
        help='Path or URL to image of person wearing outfit (outfit will be preserved)'
    )
    
    parser.add_argument(
        '--prompt',
        type=str,
        required=True,
        help='Description of desired model/person. Examples: "Professional male model in 30s, athletic", "Asian female, mid-20s, confident pose", "Plus-size woman, friendly expression"'
    )
    
    # Model swap parameters
    parser.add_argument(
        '--model',
        type=str,
        default='nano_banana_pro',
        choices=['nano_banana', 'nano_banana_pro', 'flux2_pro', 'flux2_flex'],
        help='Model to use for model swapping. Options: nano_banana (fast, 1024px), nano_banana_pro (4K, default), flux2_pro (high-quality), flux2_flex (advanced controls)'
    )
    
    parser.add_argument(
        '--resolution',
        type=str,
        default='4K',
        choices=['1K', '2K', '4K'],
        help='Output image resolution (Nano Banana Pro only). Options: 1K (draft), 2K (high-quality), 4K (professional, default)'
    )
    
    parser.add_argument(
        '--search-grounding',
        action='store_true',
        help='Use Google Search grounding for real-world reference images (Nano Banana Pro only, useful for specific style references)'
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
    
    # Validate file path (if it's a local file, not URL)
    if not args.image.startswith(('http://', 'https://')):
        if not os.path.exists(args.image):
            raise FileNotFoundError(f"Image not found: {args.image}")
    
    # Create output directory if it doesn't exist
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize agent
    print(f"Initializing Model Swap Agent...")
    print(f"  Model: {args.model}")
    print(f"  LLM Provider: {args.llm_provider}")
    if args.llm_model:
        print(f"  LLM Model: {args.llm_model}")
    print(f"  Temperature: {args.llm_temperature}")
    if args.model == 'nano_banana_pro':
        print(f"  Output Resolution: {args.resolution}")
        if args.search_grounding:
            print(f"  Search Grounding: Enabled")
    
    try:
        agent = ModelSwapAgent(
            llm_provider=args.llm_provider,
            llm_model=args.llm_model,
            temperature=args.llm_temperature,
            api_key=args.llm_api_key,
            model=args.model
        )
    except ValueError as e:
        print(f"\nError initializing agent: {e}")
        print("\nPlease ensure:")
        print("  1. Required LLM API key is set in environment variables or --llm-api-key")
        print("  2. LangChain dependencies are installed: pip install langchain langchain-openai langchain-anthropic langchain-google-genai")
        if args.model in ['nano_banana', 'nano_banana_pro']:
            print(f"  3. Gemini API key is set for {args.model}: GEMINI_API_KEY")
        elif args.model in ['flux2_pro', 'flux2_flex']:
            print(f"  3. BFL API key is set for {args.model}: BFL_API_KEY")
        return 1
    except Exception as e:
        print(f"\nUnexpected error initializing agent: {e}")
        return 1
    
    # Generate model swap
    print(f"\n{'='*60}")
    print(f"Starting Model Swap Generation")
    print(f"{'='*60}")
    print(f"  Input image: {args.image}")
    print(f"  Desired model: {args.prompt}")
    print(f"  Model: {args.model}")
    if args.model == 'nano_banana_pro':
        print(f"  Resolution: {args.resolution}")
    print(f"{'='*60}\n")
    
    try:
        # Generate with agent
        # Only pass resolution and search_grounding for Nano Banana Pro
        generate_kwargs = {
            "image": args.image,
            "prompt": args.prompt,
            "verbose": True  # Always show progress
        }
        
        if args.model == 'nano_banana_pro':
            generate_kwargs["resolution"] = args.resolution
            generate_kwargs["use_search_grounding"] = args.search_grounding
        
        result = agent.generate(**generate_kwargs)
        
        if args.verbose:
            print(f"\nFull agent result:")
            print(json.dumps(result, indent=2, default=str))
        
        if result["status"] == "error":
            print(f"\n{'='*60}")
            print(f"Error: {result.get('error', 'Unknown error')}")
            print(f"{'='*60}")
            return 1
        
        # Extract images
        images = result.get("images", [])
        provider = result.get("provider", "nano_banana_pro")
        model_description = result.get("model_description", "")
        
        if not images:
            print(f"\n{'='*60}")
            print(f"Error: No images generated")
            print(f"{'='*60}")
            return 1
        
        print(f"\n{'='*60}")
        print(f"Successfully generated {len(images)} image(s) using {provider}")
        print(f"{'='*60}")
        
        if model_description and args.verbose:
            print(f"\nModel Description Used:")
            print(f"  {model_description[:200]}...")
        
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
                elif isinstance(image_data, bytes):
                    image = Image.open(io.BytesIO(image_data))
                elif isinstance(image_data, Image.Image):
                    image = image_data
                else:
                    # Try to handle image objects with save method
                    # (PIL Images, Google Genai Images, etc.)
                    if hasattr(image_data, 'save'):
                        # It's an image object with save capability
                        image = image_data
                    else:
                        print(f"Skipping image {idx + 1}: Unsupported format (type: {type(image_data).__name__})")
                        if args.verbose:
                            print(f"     Debug: {type(image_data)}, has save: {hasattr(image_data, 'save')}")
                        continue
                
                # Save PNG
                output_path = output_dir / f"model_swap_result_{idx}.png"
                image.save(output_path)
                saved_images.append(output_path)
                print(f"Saved image {idx + 1}/{len(images)}: {output_path}")
                
                # Optionally save Base64
                if args.save_base64:
                    buffer = io.BytesIO()
                    image.save(buffer, format='PNG')
                    image_bytes = buffer.getvalue()
                    image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                    
                    output_path_txt = output_dir / f"model_swap_result_{idx}.txt"
                    with open(output_path_txt, 'w') as f:
                        f.write(image_base64)
                    print(f"Saved Base64 string {idx + 1}: {output_path_txt}")
                    
            except Exception as e:
                print(f"Error processing image {idx + 1}: {e}")
                continue
        
        print(f"\n{'='*60}")
        print(f"Complete! Saved {len(saved_images)} image(s) to {output_dir}")
        print(f"{'='*60}")
        
        # Print tips
        print(f"\nTips:")
        if args.model == 'nano_banana_pro':
            print(f"  • Use --resolution 4K for professional e-commerce quality")
            print(f"  • Try --search-grounding for style-specific references")
        elif args.model in ['flux2_pro', 'flux2_flex']:
            print(f"  • FLUX models support custom width/height (via API)")
            print(f"  • FLUX 2 Flex offers advanced controls (guidance, steps)")
        print(f"  • Be specific in prompts: age, ethnicity, body type, pose")
        print(f"  • The outfit and styling are automatically preserved")
        print(f"  • Try different models: nano_banana (fast), nano_banana_pro (4K), flux2_pro (quality), flux2_flex (advanced)")
        
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

