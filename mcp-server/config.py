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
    SERVER_VERSION = "0.1.0"
    
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
        """Get a human-readable status message."""
        status = cls.validate()
        lines = ["OpenTryOn MCP Server Configuration Status:"]
        lines.append(f"  Amazon Nova Canvas: {'✓ Configured' if status['amazon_nova'] else '✗ Not configured'}")
        lines.append(f"  Kling AI: {'✓ Configured' if status['kling_ai'] else '✗ Not configured'}")
        lines.append(f"  Segmind: {'✓ Configured' if status['segmind'] else '✗ Not configured'}")
        lines.append(f"  Gemini (Nano Banana): {'✓ Configured' if status['gemini'] else '✗ Not configured'}")
        lines.append(f"  FLUX.2: {'✓ Configured' if status['flux2'] else '✗ Not configured'}")
        lines.append(f"  Luma AI: {'✓ Configured' if status['luma_ai'] else '✗ Not configured'}")
        lines.append(f"  U2Net (Preprocessing): {'✓ Configured' if status['u2net'] else '✗ Not configured'}")
        return "\n".join(lines)


config = Config()

