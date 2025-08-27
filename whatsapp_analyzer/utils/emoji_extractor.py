"""
Emoji extraction utilities for WhatsApp chat analysis.

This module provides robust emoji detection and extraction capabilities,
with fallback support for different regex implementations.
"""

import re
import logging
from typing import List

logger = logging.getLogger(__name__)

# Try to use the more robust regex library, fallback to standard re
try:
    import regex as re2
    USING_REGEX = True
    logger.debug("Using regex library for emoji extraction")
except ImportError:
    re2 = re
    USING_REGEX = False
    logger.debug("Using standard re library for emoji extraction")

# Emoji Unicode ranges
EMOJI_RANGES = [
    (0x1F300, 0x1F5FF),  # Misc Symbols and Pictographs
    (0x1F600, 0x1F64F),  # Emoticons
    (0x1F680, 0x1F6FF),  # Transport and Map
    (0x1F900, 0x1F9FF),  # Supplemental Symbols and Pictographs
    (0x1FA70, 0x1FAFF),  # Symbols & Pictographs Extended-A
    (0x2600, 0x26FF),    # Miscellaneous Symbols
    (0x2700, 0x27BF),    # Dingbats
    (0x1F1E6, 0x1F1FF),  # Regional Indicator Symbols (flags)
    (0xFE00, 0xFE0F),    # Variation Selectors
    (0x20E3, 0x20E3),    # Combining enclosing keycap
    (0x23CF, 0x23CF),    # Eject button
    (0x24C2, 0x24C2),    # Circled Latin capital letter M
    (0x1F004, 0x1F004),  # Mahjong tile red dragon
    (0x1F0CF, 0x1F0CF),  # Playing card black joker
    (0x1F170, 0x1F171),  # Negative squared Latin capital letter A/B
    (0x1F17E, 0x1F17F),  # Negative squared Latin capital letter O/P
    (0x1F18E, 0x1F18E),  # Negative squared AB
    (0x1F191, 0x1F19A),  # Squared CL, COOL, FREE, ID, NEW, NG, OK, P, SOS, UP
    (0x1F1E6, 0x1F1FF),  # Regional indicator symbols
    (0x1F201, 0x1F202),  # Squared katakana KOKO, SA
    (0x1F21A, 0x1F21A),  # Squared katakana U+7121
    (0x1F22F, 0x1F22F),  # Squared katakana U+6307
    (0x1F232, 0x1F23A),  # Squared CJK unified ideographs
    (0x1F250, 0x1F251),  # Circled ideograph advantage, accept
    (0x1F300, 0x1F321),  # Various pictographs
    (0x1F324, 0x1F393),  # Various pictographs
    (0x1F396, 0x1F397),  # Various pictographs
    (0x1F399, 0x1F39B),  # Various pictographs
    (0x1F39E, 0x1F3F0),  # Various pictographs
    (0x1F3F3, 0x1F3F5),  # Various pictographs
    (0x1F3F7, 0x1F3FA),  # Various pictographs
    (0x1F400, 0x1F4FD),  # Various pictographs
    (0x1F4FF, 0x1F53D),  # Various pictographs
    (0x1F549, 0x1F54E),  # Various pictographs
    (0x1F550, 0x1F567),  # Various pictographs
    (0x1F56F, 0x1F570),  # Various pictographs
    (0x1F573, 0x1F57A),  # Various pictographs
    (0x1F587, 0x1F587),  # Various pictographs
    (0x1F58A, 0x1F58D),  # Various pictographs
    (0x1F590, 0x1F590),  # Various pictographs
    (0x1F595, 0x1F596),  # Various pictographs
    (0x1F5A4, 0x1F5A5),  # Various pictographs
    (0x1F5A8, 0x1F5A8),  # Various pictographs
    (0x1F5B1, 0x1F5B2),  # Various pictographs
    (0x1F5BC, 0x1F5BC),  # Various pictographs
    (0x1F5C2, 0x1F5C4),  # Various pictographs
    (0x1F5D1, 0x1F5D3),  # Various pictographs
    (0x1F5DC, 0x1F5DE),  # Various pictographs
    (0x1F5E1, 0x1F5E1),  # Various pictographs
    (0x1F5E3, 0x1F5E3),  # Various pictographs
    (0x1F5E8, 0x1F5E8),  # Various pictographs
    (0x1F5EF, 0x1F5EF),  # Various pictographs
    (0x1F5F3, 0x1F5F3),  # Various pictographs
    (0x1F5FA, 0x1F64F),  # Various pictographs
    (0x1F680, 0x1F6C5),  # Various pictographs
    (0x1F6CB, 0x1F6D2),  # Various pictographs
    (0x1F6E0, 0x1F6E5),  # Various pictographs
    (0x1F6E9, 0x1F6E9),  # Various pictographs
    (0x1F6EB, 0x1F6EC),  # Various pictographs
    (0x1F6F0, 0x1F6F0),  # Various pictographs
    (0x1F6F3, 0x1F6F9),  # Various pictographs
    (0x1F910, 0x1F93A),  # Various pictographs
    (0x1F93C, 0x1F93E),  # Various pictographs
    (0x1F940, 0x1F945),  # Various pictographs
    (0x1F947, 0x1F970),  # Various pictographs
    (0x1F973, 0x1F976),  # Various pictographs
    (0x1F97A, 0x1F97A),  # Various pictographs
    (0x1F97C, 0x1F97C),  # Various pictographs
    (0x1F980, 0x1F984),  # Various pictographs
    (0x1F986, 0x1F987),  # Various pictographs
    (0x1F988, 0x1F988),  # Various pictographs
    (0x1F98A, 0x1F98A),  # Various pictographs
    (0x1F98B, 0x1F98B),  # Various pictographs
    (0x1F98C, 0x1F98C),  # Various pictographs
    (0x1F98D, 0x1F98D),  # Various pictographs
    (0x1F98E, 0x1F98E),  # Various pictographs
    (0x1F98F, 0x1F98F),  # Various pictographs
    (0x1F990, 0x1F990),  # Various pictographs
    (0x1F991, 0x1F991),  # Various pictographs
    (0x1F992, 0x1F992),  # Various pictographs
    (0x1F993, 0x1F993),  # Various pictographs
    (0x1F994, 0x1F994),  # Various pictographs
    (0x1F995, 0x1F995),  # Various pictographs
    (0x1F996, 0x1F996),  # Various pictographs
    (0x1F997, 0x1F997),  # Various pictographs
    (0x1F998, 0x1F998),  # Various pictographs
    (0x1F999, 0x1F999),  # Various pictographs
    (0x1F99A, 0x1F99A),  # Various pictographs
    (0x1F99B, 0x1F99B),  # Various pictographs
    (0x1F99C, 0x1F99C),  # Various pictographs
    (0x1F99D, 0x1F99D),  # Various pictographs
    (0x1F99E, 0x1F99E),  # Various pictographs
    (0x1F99F, 0x1F99F),  # Various pictographs
    (0x1F9A0, 0x1F9A0),  # Various pictographs
    (0x1F9A1, 0x1F9A1),  # Various pictographs
    (0x1F9A2, 0x1F9A2),  # Various pictographs
    (0x1F9A3, 0x1F9A3),  # Various pictographs
    (0x1F9A4, 0x1F9A4),  # Various pictographs
    (0x1F9A5, 0x1F9A5),  # Various pictographs
    (0x1F9A6, 0x1F9A6),  # Various pictographs
    (0x1F9A7, 0x1F9A7),  # Various pictographs
    (0x1F9A8, 0x1F9A8),  # Various pictographs
    (0x1F9A9, 0x1F9A9),  # Various pictographs
    (0x1F9AA, 0x1F9AA),  # Various pictographs
    (0x1F9AB, 0x1F9AB),  # Various pictographs
    (0x1F9AC, 0x1F9AC),  # Various pictographs
    (0x1F9AD, 0x1F9AD),  # Various pictographs
    (0x1F9AE, 0x1F9AE),  # Various pictographs
    (0x1F9AF, 0x1F9AF),  # Various pictographs
    (0x1F9B0, 0x1F9B0),  # Various pictographs
    (0x1F9B1, 0x1F9B1),  # Various pictographs
    (0x1F9B2, 0x1F9B2),  # Various pictographs
    (0x1F9B3, 0x1F9B3),  # Various pictographs
    (0x1F9B4, 0x1F9B4),  # Various pictographs
    (0x1F9B5, 0x1F9B5),  # Various pictographs
    (0x1F9B6, 0x1F9B6),  # Various pictographs
    (0x1F9B7, 0x1F9B7),  # Various pictographs
    (0x1F9B8, 0x1F9B8),  # Various pictographs
    (0x1F9B9, 0x1F9B9),  # Various pictographs
    (0x1F9BA, 0x1F9BA),  # Various pictographs
    (0x1F9BB, 0x1F9BB),  # Various pictographs
    (0x1F9BC, 0x1F9BC),  # Various pictographs
    (0x1F9BD, 0x1F9BD),  # Various pictographs
    (0x1F9BE, 0x1F9BE),  # Various pictographs
    (0x1F9BF, 0x1F9BF),  # Various pictographs
    (0x1F9C0, 0x1F9C0),  # Various pictographs
    (0x1F9C1, 0x1F9C1),  # Various pictographs
    (0x1F9C2, 0x1F9C2),  # Various pictographs
    (0x1F9C3, 0x1F9C3),  # Various pictographs
    (0x1F9C4, 0x1F9C4),  # Various pictographs
    (0x1F9C5, 0x1F9C5),  # Various pictographs
    (0x1F9C6, 0x1F9C6),  # Various pictographs
    (0x1F9C7, 0x1F9C7),  # Various pictographs
    (0x1F9C8, 0x1F9C8),  # Various pictographs
    (0x1F9C9, 0x1F9C9),  # Various pictographs
    (0x1F9CA, 0x1F9CA),  # Various pictographs
    (0x1F9CB, 0x1F9CB),  # Various pictographs
    (0x1F9CC, 0x1F9CC),  # Various pictographs
    (0x1F9CD, 0x1F9CD),  # Various pictographs
    (0x1F9CE, 0x1F9CE),  # Various pictographs
    (0x1F9CF, 0x1F9CF),  # Various pictographs
    (0x1F9D0, 0x1F9D0),  # Various pictographs
    (0x1F9D1, 0x1F9D1),  # Various pictographs
    (0x1F9D2, 0x1F9D2),  # Various pictographs
    (0x1F9D3, 0x1F9D3),  # Various pictographs
    (0x1F9D4, 0x1F9D4),  # Various pictographs
    (0x1F9D5, 0x1F9D5),  # Various pictographs
    (0x1F9D6, 0x1F9D6),  # Various pictographs
    (0x1F9D7, 0x1F9D7),  # Various pictographs
    (0x1F9D8, 0x1F9D8),  # Various pictographs
    (0x1F9D9, 0x1F9D9),  # Various pictographs
    (0x1F9DA, 0x1F9DA),  # Various pictographs
    (0x1F9DB, 0x1F9DB),  # Various pictographs
    (0x1F9DC, 0x1F9DC),  # Various pictographs
    (0x1F9DD, 0x1F9DD),  # Various pictographs
    (0x1F9DE, 0x1F9DE),  # Various pictographs
    (0x1F9DF, 0x1F9DF),  # Various pictographs
    (0x1F9E0, 0x1F9E0),  # Various pictographs
    (0x1F9E1, 0x1F9E1),  # Various pictographs
    (0x1F9E2, 0x1F9E2),  # Various pictographs
    (0x1F9E3, 0x1F9E3),  # Various pictographs
    (0x1F9E4, 0x1F9E4),  # Various pictographs
    (0x1F9E5, 0x1F9E5),  # Various pictographs
    (0x1F9E6, 0x1F9E6),  # Various pictographs
    (0x1F9E7, 0x1F9E7),  # Various pictographs
    (0x1F9E8, 0x1F9E8),  # Various pictographs
    (0x1F9E9, 0x1F9E9),  # Various pictographs
    (0x1F9EA, 0x1F9EA),  # Various pictographs
    (0x1F9EB, 0x1F9EB),  # Various pictographs
    (0x1F9EC, 0x1F9EC),  # Various pictographs
    (0x1F9ED, 0x1F9ED),  # Various pictographs
    (0x1F9EE, 0x1F9EE),  # Various pictographs
    (0x1F9EF, 0x1F9EF),  # Various pictographs
    (0x1F9F0, 0x1F9F0),  # Various pictographs
    (0x1F9F1, 0x1F9F1),  # Various pictographs
    (0x1F9F2, 0x1F9F2),  # Various pictographs
    (0x1F9F3, 0x1F9F3),  # Various pictographs
    (0x1F9F4, 0x1F9F4),  # Various pictographs
    (0x1F9F5, 0x1F9F5),  # Various pictographs
    (0x1F9F6, 0x1F9F6),  # Various pictographs
    (0x1F9F7, 0x1F9F7),  # Various pictographs
    (0x1F9F8, 0x1F9F8),  # Various pictographs
    (0x1F9F9, 0x1F9F9),  # Various pictographs
    (0x1F9FA, 0x1F9FA),  # Various pictographs
    (0x1F9FB, 0x1F9FB),  # Various pictographs
    (0x1F9FC, 0x1F9FC),  # Various pictographs
    (0x1F9FD, 0x1F9FD),  # Various pictographs
    (0x1F9FE, 0x1F9FE),  # Various pictographs
    (0x1F9FF, 0x1F9FF),  # Various pictographs
]


def _is_emoji_codepoint(codepoint: int) -> bool:
    """
    Check if a codepoint falls within emoji ranges.
    
    Args:
        codepoint: Unicode codepoint to check
        
    Returns:
        True if codepoint is in emoji range
    """
    for start, end in EMOJI_RANGES:
        if start <= codepoint <= end:
            return True
    return False


def _is_emoji_grapheme(grapheme: str) -> bool:
    """
    Check if a grapheme contains emoji characters.
    
    Args:
        grapheme: Grapheme cluster to check
        
    Returns:
        True if grapheme contains emoji
    """
    # Check each character in the grapheme
    for char in grapheme:
        if _is_emoji_codepoint(ord(char)):
            return True
    
    # Special handling for ZWJ sequences (e.g., family emojis)
    if "\u200d" in grapheme:  # Zero-width joiner
        for char in grapheme:
            if 0x1F000 <= ord(char) <= 0x1FAFF:
                return True
    
    return False


def extract_emojis(text: str) -> List[str]:
    """
    Extract emojis from text using robust detection.
    
    Args:
        text: Text to extract emojis from
        
    Returns:
        List of emoji graphemes found in text
    """
    if not text:
        return []
    
    try:
        if USING_REGEX:
            # Use regex library for better grapheme support
            emoji_pattern = re2.compile(r"\X", re2.UNICODE)
            graphemes = emoji_pattern.findall(text)
        else:
            # Fallback to standard re with character class approach
            emoji_pattern = re.compile(
                r"[\U0001F300-\U0001FAFF\u2600-\u26FF\u2700-\u27BF]"
            )
            graphemes = emoji_pattern.findall(text)
        
        # Filter to only emoji graphemes
        emojis = [g for g in graphemes if _is_emoji_grapheme(g)]
        
        logger.debug(f"Extracted {len(emojis)} emojis from text of length {len(text)}")
        return emojis
        
    except Exception as e:
        logger.warning(f"Error extracting emojis: {e}")
        return []


def get_emoji_stats(emojis: List[str]) -> dict:
    """
    Get statistics about extracted emojis.
    
    Args:
        emojis: List of emoji graphemes
        
    Returns:
        Dictionary with emoji statistics
    """
    if not emojis:
        return {
            "total": 0,
            "unique": 0,
            "most_common": [],
            "categories": {}
        }
    
    from collections import Counter
    emoji_counter = Counter(emojis)
    
    # Basic stats
    stats = {
        "total": len(emojis),
        "unique": len(emoji_counter),
        "most_common": emoji_counter.most_common(10)
    }
    
    # Categorize emojis (basic categorization)
    categories = {
        "faces": [],
        "animals": [],
        "objects": [],
        "symbols": [],
        "flags": [],
        "other": []
    }
    
    for emoji in emojis:
        # Simple categorization based on Unicode ranges
        codepoint = ord(emoji[0]) if emoji else 0
        
        if 0x1F600 <= codepoint <= 0x1F64F:  # Emoticons
            categories["faces"].append(emoji)
        elif 0x1F400 <= codepoint <= 0x1F4F9:  # Animals and objects
            if 0x1F400 <= codepoint <= 0x1F4F9:  # Animals
                categories["animals"].append(emoji)
            else:
                categories["objects"].append(emoji)
        elif 0x1F1E6 <= codepoint <= 0x1F1FF:  # Flags
            categories["flags"].append(emoji)
        elif 0x2600 <= codepoint <= 0x27BF:  # Symbols
            categories["symbols"].append(emoji)
        else:
            categories["other"].append(emoji)
    
    # Convert to counts
    stats["categories"] = {k: len(v) for k, v in categories.items()}
    
    return stats 