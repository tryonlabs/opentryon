"""Configuration management for OpenTryOn MCP Server."""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from parent directory
parent_dir = Path(__file__).parent.parent
env_path = parent_dir / ".env"
try:
    if env_path.exists():
        load_dotenv(env_path)
except Exception:
    # Silently fail if .env cannot be loaded (e.g., permission issues)
    pass


class Config:
    """Configuration for OpenTryOn MCP Server."""
    
    # Server settings
    SERVER_NAME = "opentryon-mcp"
    SERVER_VERSION = "0.0.1"
    
    # AWS/Amazon Nova Canvas
    AWS_ACCESS_KEY_ID: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY")
    AMAZON_NOVA_REGION: str = os.getenv("AMAZON_NOVA_REGION", "us-east-1")
    AMAZON_NOVA_MODEL_ID: str = os.getenv("AMAZON_NOVA_MODEL_ID", "amazon.nova-canvas-v1:0")
    
    # Kling AI
    KLING_AI_API_KEY: Optional[str] = os.getenv("KLING_AI_API_KEY")
    KLING_AI_SECRET_KEY: Optional[str] = os.getenv("KLING_AI_SECRET_KEY")
    KLING_AI_BASE_URL: str = os.getenv("KLING_AI_BASE_URL", "https://api-singapore.klingai.com")
    
    # Segmind
    SEGMIND_API_KEY: Optional[str] = os.getenv("SEGMIND_API_KEY")
    
    # Google Gemini (Nano Banana)
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    
    # BFL API (FLUX.2)
    BFL_API_KEY: Optional[str] = os.getenv("BFL_API_KEY")
    
    # Luma AI
    LUMA_AI_API_KEY: Optional[str] = os.getenv("LUMA_AI_API_KEY")
    
    # U2Net Checkpoint
    U2NET_CLOTH_SEG_CHECKPOINT_PATH: Optional[str] = os.getenv("U2NET_CLOTH_SEG_CHECKPOINT_PATH")
    
    # File handling
    MAX_FILE_SIZE_MB = 50
    ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
    ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi"}
    
    # Temporary files
    TEMP_DIR = Path("/tmp/opentryon_mcp")
    TEMP_DIR.mkdir(exist_ok=True, parents=True)
    
    @classmethod
    def validate(cls) -> dict[str, bool]:
        """Validate configuration and return status of each service."""
        return {
            "amazon_nova": bool(cls.AWS_ACCESS_KEY_ID and cls.AWS_SECRET_ACCESS_KEY),
            "kling_ai": bool(cls.KLING_AI_API_KEY and cls.KLING_AI_SECRET_KEY),
            "segmind": bool(cls.SEGMIND_API_KEY),
            "gemini": bool(cls.GEMINI_API_KEY),
            "flux2": bool(cls.BFL_API_KEY),
            "luma_ai": bool(cls.LUMA_AI_API_KEY),
            "u2net": bool(cls.U2NET_CLOTH_SEG_CHECKPOINT_PATH),
        }
    
    @classmethod
    def get_status_message(cls) -> str:
        """Get a human-readable status message with helpful guidance."""
        status = cls.validate()
        lines = ["OpenTryOn MCP Server Configuration Status:"]
        
        # Virtual Try-On Services
        nova_status = "✓ Configured" if status['amazon_nova'] else "✗ Not configured (optional - requires AWS)"
        kling_status = "✓ Configured" if status['kling_ai'] else "✗ Not configured (recommended)"
        segmind_status = "✓ Configured" if status['segmind'] else "✗ Not configured (recommended)"
        
        lines.append(f"  Amazon Nova Canvas: {nova_status}")
        lines.append(f"  Kling AI: {kling_status}")
        lines.append(f"  Segmind: {segmind_status}")
        
        # Image Generation Services
        gemini_status = "✓ Configured" if status['gemini'] else "✗ Not configured (recommended)"
        flux_status = "✓ Configured" if status['flux2'] else "✗ Not configured (recommended)"
        luma_status = "✓ Configured" if status['luma_ai'] else "✗ Not configured (optional - for video)"
        
        lines.append(f"  Gemini (Nano Banana): {gemini_status}")
        lines.append(f"  FLUX.2: {flux_status}")
        lines.append(f"  Luma AI: {luma_status}")
        
        # Preprocessing
        u2net_status = "✓ Configured" if status['u2net'] else "✗ Not configured (optional - for local segmentation)"
        lines.append(f"  U2Net (Preprocessing): {u2net_status}")
        
        # Add helpful message
        vton_count = sum([status['amazon_nova'], status['kling_ai'], status['segmind']])
        img_count = sum([status['gemini'], status['flux2'], status['luma_ai']])
        
        lines.append("")
        if vton_count == 0:
            lines.append("⚠️  Warning: No virtual try-on service configured!")
            lines.append("   Configure at least one: Kling AI (recommended) or Segmind")
        if img_count == 0:
            lines.append("⚠️  Warning: No image generation service configured!")
            lines.append("   Configure at least one: Gemini (recommended) or FLUX.2")
        
        if vton_count > 0 and img_count > 0:
            lines.append("✅ Ready! At least one service from each category is configured.")
            lines.append(f"   Virtual Try-On: {vton_count}/3 services")
            lines.append(f"   Image Generation: {img_count}/3 services")
        
        lines.append("")
        lines.append("💡 Tip: Copy env.template to .env and add your API keys")
        lines.append("📖 Setup guide: mcp-server/README.md")
        
        return "\n".join(lines)
    
    @classmethod
    def get_missing_services(cls) -> dict[str, list[str]]:
        """Get list of missing services by category."""
        status = cls.validate()
        
        missing = {
            "virtual_tryon": [],
            "image_generation": [],
            "optional": []
        }
        
        # Virtual Try-On (at least one required)
        if not status['kling_ai']:
            missing["virtual_tryon"].append("Kling AI")
        if not status['segmind']:
            missing["virtual_tryon"].append("Segmind")
        if not status['amazon_nova']:
            missing["optional"].append("Amazon Nova Canvas (requires AWS)")
        
        # Image Generation (at least one required)
        if not status['gemini']:
            missing["image_generation"].append("Gemini (Nano Banana)")
        if not status['flux2']:
            missing["image_generation"].append("FLUX.2")
        
        # Optional services
        if not status['luma_ai']:
            missing["optional"].append("Luma AI (for video generation)")
        if not status['u2net']:
            missing["optional"].append("U2Net (for local garment segmentation)")
        
        return missing
    
    @classmethod
    def is_ready(cls) -> bool:
        """Check if minimum required services are configured."""
        status = cls.validate()
        
        # Need at least one virtual try-on service
        has_vton = status['kling_ai'] or status['segmind'] or status['amazon_nova']
        
        # Need at least one image generation service
        has_img_gen = status['gemini'] or status['flux2'] or status['luma_ai']
        
        return has_vton and has_img_gen


config = Config()

