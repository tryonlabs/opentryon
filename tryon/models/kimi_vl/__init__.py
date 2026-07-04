"""
Kimi-VL (open-weight) Local Model

Local GPU inference adapter for Moonshot AI's open-weight Kimi-VL family on
Hugging Face -- the open-weight counterpart to the closed Kimi K2.6 / K2.7
Code APIs (see `tryon.api.kimi.KimiUnderstandAdapter`).

Reference: https://github.com/MoonshotAI/Kimi-VL
"""

from .adapter import KimiVLAdapter

__all__ = [
    "KimiVLAdapter",
]
