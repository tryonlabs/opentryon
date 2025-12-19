"""
Virtual Try-On Agent Module

This module provides a LangChain-based agent for virtual try-on operations.
The agent intelligently selects and uses the appropriate adapter based on
user prompts.

Example:
    >>> from tryon.agents.vton import VTOnAgent
    >>> 
    >>> agent = VTOnAgent(llm_provider="openai")
    >>> result = agent.generate(
    ...     person_image="person.jpg",
    ...     garment_image="shirt.jpg",
    ...     prompt="Use Kling AI to generate a virtual try-on"
    ... )
"""

from .agent import VTOnAgent
from .tools import (
    get_vton_tools,
    kling_ai_virtual_tryon,
    nova_canvas_virtual_tryon,
    segmind_virtual_tryon,
)

__all__ = [
    "VTOnAgent",
    "get_vton_tools",
    "kling_ai_virtual_tryon",
    "nova_canvas_virtual_tryon",
    "segmind_virtual_tryon",
]

