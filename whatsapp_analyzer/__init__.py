"""
WhatsApp Chat Analyzer - A production-grade tool for analyzing WhatsApp chat exports.

This package provides functionality to parse and analyze WhatsApp chat exports
from both Android and iOS platforms, with support for Streamlit UI and CLI interfaces.
"""

__version__ = "1.0.0"
__author__ = "WhatsApp Chat Analyzer Team"

from .core.parser import parse_chat, detect_platform
from .core.analyzer import ChatAnalyzer
from .utils.emoji_extractor import extract_emojis

__all__ = [
    "parse_chat",
    "detect_platform", 
    "ChatAnalyzer",
    "extract_emojis",
] 