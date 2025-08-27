"""
Core parsing functionality for WhatsApp chat exports.

This module handles the parsing of WhatsApp chat exports from both Android and iOS platforms,
with automatic platform detection and robust error handling.
"""

import re
import logging
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional, Union
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

# Platform detection patterns
ANDROID_PATTERN = re.compile(
    r"^([0-9]{1,2})/([0-9]{1,2})/([0-9]{2,4}), ([0-9]{1,2}):([0-9]{2})\s*([AP]M|am|pm)? -"
)

# iOS pattern with support for various Unicode spaces
_SP = "[ \u00A0\u202F\u2009\u200A\u2002-\u2006\u2007\u2008]"
IOS_PATTERN = re.compile(
    "^\\["                                   # opening bracket
    "(\\d{1,2}[/-]\\d{1,2}[/-]\\d{2,4})"   # date
    "(?:,?" + _SP + "+)"                      # comma optional, then spaces
    "(\\d{1,2}:\\d{2}(?::\\d{2})?)"        # time with optional seconds
    "(?:" + _SP + "*(AM|PM|am|pm))?"           # optional AM/PM
    "\\]"                                      # closing bracket
)


class ChatParseError(Exception):
    """Raised when chat parsing fails."""
    pass


class PlatformDetectionError(Exception):
    """Raised when platform detection fails."""
    pass


def _decode_file_content(file_content: Union[bytes, str]) -> List[str]:
    """
    Decode file content trying common encodings for WhatsApp exports.
    
    Args:
        file_content: Raw file content as bytes or string
        
    Returns:
        List of decoded lines
        
    Raises:
        ChatParseError: If decoding fails with all attempted encodings
    """
    if isinstance(file_content, str):
        return file_content.splitlines()
    
    encodings = ["utf-8", "utf-8-sig", "utf-16", "utf-16-le", "utf-16-be"]
    
    for encoding in encodings:
        try:
            decoded = file_content.decode(encoding)
            logger.debug(f"Successfully decoded with {encoding}")
            return decoded.splitlines()
        except UnicodeDecodeError as e:
            logger.debug(f"Failed to decode with {encoding}: {e}")
            continue
    
    # Fallback to utf-8 with error handling
    try:
        decoded = file_content.decode("utf-8", errors="ignore")
        logger.warning("Using utf-8 with error handling as fallback")
        return decoded.splitlines()
    except Exception as e:
        raise ChatParseError(f"Failed to decode file content: {e}")


def _clean_line(line: str) -> str:
    """
    Clean line by removing directionality marks and normalizing spaces.
    
    Args:
        line: Raw line from chat export
        
    Returns:
        Cleaned line
    """
    # Remove directionality marks common in iOS exports
    cleaned = line.replace("\u200e", "").replace("\u200f", "")
    # Remove BOM and normalize whitespace
    cleaned = cleaned.strip("\ufeff\n\r")
    return cleaned


def _is_android_format(line: str) -> bool:
    """Check if line matches Android format."""
    return ANDROID_PATTERN.match(line) is not None


def _is_ios_format(line: str) -> bool:
    """Check if line matches iOS format."""
    return IOS_PATTERN.match(line) is not None


def _parse_android_line(line: str) -> Tuple[str, str, Optional[str], str]:
    """
    Parse Android format line: "DATE, TIME - AUTHOR: MESSAGE"
    
    Args:
        line: Line in Android format
        
    Returns:
        Tuple of (date, time, author, message)
        
    Raises:
        ChatParseError: If line format is invalid
    """
    try:
        parts = line.split(" - ", 1)
        if len(parts) != 2:
            raise ChatParseError(f"Invalid Android format: {line}")
        
        date_time, message_part = parts
        date, time = date_time.split(", ", 1)
        
        if ":" in message_part:
            author, message = message_part.split(": ", 1)
        else:
            author, message = None, message_part
            
        return date, time, author, message
    except Exception as e:
        raise ChatParseError(f"Failed to parse Android line '{line}': {e}")


def _parse_ios_line(line: str) -> Tuple[str, str, Optional[str], str]:
    """
    Parse iOS format line: "[DATE, TIME] AUTHOR: MESSAGE"
    
    Args:
        line: Line in iOS format
        
    Returns:
        Tuple of (date, time, author, message)
        
    Raises:
        ChatParseError: If line format is invalid
    """
    try:
        match = IOS_PATTERN.match(line)
        if not match:
            raise ChatParseError(f"Invalid iOS format: {line}")
        
        date, time, ampm = match.groups()
        
        # Normalize AM/PM
        if ampm:
            time = f"{time} {ampm.upper()}"
        
        # Extract message part after the timestamp
        message_part = line[match.end():].lstrip()
        
        # --- FIX STARTS HERE ---
        # Robustly split author and message. This now handles system messages
        # where there is no space after the colon, or no message at all.
        parts = message_part.split(":", 1)
        if len(parts) == 2:
            # Standard message: "Author: Message"
            author = parts[0].strip()
            message = parts[1].strip()
            # If the message is empty after splitting, it's a system message
            if not message:
                message = f"System message from {author}"
                author = None # Re-assign author to None for system messages
        else:
            # A line without a colon is a system message
            author = None
            message = message_part.strip()
        # --- FIX ENDS HERE ---
            
        return date, time, author, message
    except Exception as e:
        raise ChatParseError(f"Failed to parse iOS line '{line}': {e}")


def _parse_timestamp(date: str, time: str, platform: str) -> Optional[datetime]:
    """
    Parse date and time strings into datetime object.
    
    Args:
        date: Date string
        time: Time string
        platform: Platform identifier ('android' or 'ios')
        
    Returns:
        Parsed datetime or None if parsing fails
    """
    date_time_str = f"{date} {time}"
    
    if platform == "android":
        formats = [
            # Month-first formats (US style)
            "%m/%d/%Y %I:%M %p", "%m/%d/%y %I:%M %p",
            "%m/%d/%Y %H:%M", "%m/%d/%y %H:%M",
            # Day-first formats (European/Indian style)
            "%d/%m/%Y %I:%M %p", "%d/%m/%y %I:%M %p",
            "%d/%m/%Y %H:%M", "%d/%m/%y %H:%M"
        ]
    else:  # iOS
        formats = [
            # Day-first formats
            "%d-%m-%Y %H:%M:%S", "%d-%m-%y %H:%M:%S",
            "%d/%m/%Y %H:%M:%S", "%d/%m/%y %H:%M:%S",
            "%d-%m-%Y %H:%M", "%d-%m-%y %H:%M",
            "%d/%m/%Y %H:%M", "%d/%m/%y %H:%M",
            "%d-%m-%Y %I:%M:%S %p", "%d-%m-%y %I:%M:%S %p",
            "%d/%m/%Y %I:%M:%S %p", "%d/%m/%y %I:%M:%S %p",
            "%d-%m-%Y %I:%M %p", "%d-%m-%y %I:%M %p",
            "%d/%m/%Y %I:%M %p", "%d/%m/%y %I:%M %p",
            # Month-first formats (US style iOS exports)
            "%m-%d-%Y %H:%M:%S", "%m-%d-%y %H:%M:%S",
            "%m/%d/%Y %H:%M:%S", "%m/%d/%y %H:%M:%S",
            "%m-%d-%Y %H:%M", "%m-%d-%y %H:%M",
            "%m/%d/%Y %H:%M", "%m/%d/%y %H:%M",
            "%m-%d-%Y %I:%M:%S %p", "%m-%d-%y %I:%M:%S %p",
            "%m/%d/%Y %I:%M:%S %p", "%m/%d/%y %I:%M:%S %p",
            "%m-%d-%Y %I:%M %p", "%m-%d-%y %I:%M %p",
            "%m/%d/%Y %I:%M %p", "%m/%d/%y %I:%M %p",
        ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_time_str, fmt)
        except ValueError:
            continue
    
    logger.warning(f"Failed to parse timestamp: {date_time_str}")
    return None


def detect_platform(lines: List[str]) -> str:
    """
    Detect platform from chat export lines.
    
    Args:
        lines: List of lines from chat export
        
    Returns:
        Platform identifier ('android' or 'ios')
        
    Raises:
        PlatformDetectionError: If platform cannot be determined
    """
    android_count = 0
    ios_count = 0
    
    for line in lines[:100]:  # Check first 100 lines
        cleaned = _clean_line(line.strip())
        if not cleaned:
            continue
            
        if _is_android_format(cleaned):
            android_count += 1
        elif _is_ios_format(cleaned):
            ios_count += 1
    
    if android_count > ios_count:
        logger.info(f"Detected Android format ({android_count} vs {ios_count} iOS matches)")
        return "android"
    elif ios_count > android_count:
        logger.info(f"Detected iOS format ({ios_count} vs {android_count} Android matches)")
        return "ios"
    else:
        raise PlatformDetectionError(
            f"Could not determine platform. Android: {android_count}, iOS: {ios_count}"
        )


def parse_chat(
    file_content: Union[bytes, str, Path], 
    platform: str = "auto"
) -> pd.DataFrame:
    """
    Parse WhatsApp chat export into a structured DataFrame.
    
    Args:
        file_content: Chat export content as bytes, string, or file path
        platform: Platform identifier ('android', 'ios', or 'auto')
        
    Returns:
        DataFrame with columns: Date, Time, Author, Message, ts, date, hour, dow, is_media
        
    Raises:
        ChatParseError: If parsing fails
        PlatformDetectionError: If platform detection fails
    """
    try:
        # Handle file path input
        if isinstance(file_content, (str, Path)) and Path(file_content).exists():
            with open(file_content, 'rb') as f:
                file_content = f.read()
        
        # Decode content
        lines = _decode_file_content(file_content)
        
        # Auto-detect platform if requested
        if platform == "auto":
            platform = detect_platform(lines)
        
        logger.info(f"Parsing chat with platform: {platform}")
        
        # Parse messages
        parsed_messages = []
        message_buffer = []
        current_date = current_time = current_author = None
        
        parse_line_func = _parse_android_line if platform == "android" else _parse_ios_line
        is_format_func = _is_android_format if platform == "android" else _is_ios_format
        
        for line in lines:
            cleaned_line = _clean_line(line)
            if not cleaned_line:
                continue
                
            if is_format_func(cleaned_line):
                # Flush previous message buffer
                if message_buffer:
                    parsed_messages.append([
                        current_date, current_time, current_author, 
                        " ".join(message_buffer).strip()
                    ])
                    message_buffer.clear()
                
                # Parse new message header
                current_date, current_time, current_author, message = parse_line_func(cleaned_line)
                message_buffer.append(message)
            else:
                # Continue previous message
                message_buffer.append(cleaned_line)
        
        # Flush final message
        if message_buffer:
            parsed_messages.append([
                current_date, current_time, current_author,
                " ".join(message_buffer).strip()
            ])
        
        if not parsed_messages:
            raise ChatParseError("No messages found in chat export")
        
        # Create DataFrame
        df = pd.DataFrame(parsed_messages, columns=["Date", "Time", "Author", "Message"])
        
        # Parse timestamps
        df["ts"] = df.apply(
            lambda row: _parse_timestamp(row["Date"], row["Time"], platform), 
            axis=1
        )
        
        # Remove rows with invalid timestamps
        df = df.dropna(subset=["ts"]).reset_index(drop=True)
        
        if df.empty:
            raise ChatParseError("No valid timestamps found after parsing")
        
        # Add derived fields
        df["date"] = df["ts"].dt.date
        df["hour"] = df["ts"].dt.hour
        df["dow"] = df["ts"].dt.day_name()
        
        # Flag media messages
        df["is_media"] = (
            df["Message"].eq("<Media omitted>") |
            df["Message"].str.contains("<Media omitted>", na=False) |
            df["Message"].str.contains("omitted", case=False, na=False)
        )
        
        logger.info(f"Successfully parsed {len(df)} messages")
        return df
        
    except Exception as e:
        logger.error(f"Failed to parse chat: {e}")
        raise ChatParseError(f"Chat parsing failed: {e}") 