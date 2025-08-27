"""
Tests for the WhatsApp chat parser module.

This module contains comprehensive tests for chat parsing functionality,
including platform detection, message parsing, and error handling.
"""

import pytest
import pandas as pd
from datetime import datetime

from whatsapp_analyzer.core.parser import (
    parse_chat, detect_platform, _decode_file_content,
    _clean_line, _is_android_format, _is_ios_format,
    _parse_android_line, _parse_ios_line, _parse_timestamp,
    ChatParseError, PlatformDetectionError
)


class TestPlatformDetection:
    """Test platform detection functionality."""
    
    def test_android_detection(self):
        """Test Android format detection."""
        android_lines = [
            "12/31/2023, 10:15 PM - Alice: Hello there!",
            "12/31/2023, 10:16 PM - Bob: Hi Alice!",
            "12/31/2023, 10:17 PM - Alice: How are you?",
        ]
        
        platform = detect_platform(android_lines)
        assert platform == "android"
    
    def test_ios_detection(self):
        """Test iOS format detection."""
        ios_lines = [
            "[4/20/23, 4:21:43 AM] 343: Messages and calls are end-to-end encrypted.",
            "[4/20/23, 4:21:55 AM] Shrey Khandelwal: Ek kaam Karo...",
            "[4/20/23, 4:21:59 AM] Sayantan: Bruh 🗿",
        ]
        
        platform = detect_platform(ios_lines)
        assert platform == "ios"
    
    def test_mixed_formats(self):
        """Test detection with mixed format lines."""
        mixed_lines = [
            "12/31/2023, 10:15 PM - Alice: Hello there!",
            "[4/20/23, 4:21:43 AM] 343: System message",
            "12/31/2023, 10:16 PM - Bob: Hi Alice!",
        ]
        
        # Should detect Android as it has more Android format lines
        platform = detect_platform(mixed_lines)
        assert platform == "android"
    
    def test_no_valid_formats(self):
        """Test detection with no valid format lines."""
        invalid_lines = [
            "This is not a valid format",
            "Neither is this",
            "Or this one",
        ]
        
        with pytest.raises(PlatformDetectionError):
            detect_platform(invalid_lines)


class TestLineParsing:
    """Test individual line parsing functions."""
    
    def test_android_line_parsing(self):
        """Test Android line parsing."""
        line = "12/31/2023, 10:15 PM - Alice: Hello there!"
        date, time, author, message = _parse_android_line(line)
        
        assert date == "12/31/2023"
        assert time == "10:15 PM"
        assert author == "Alice"
        assert message == "Hello there!"
    
    def test_android_line_no_author(self):
        """Test Android line without author."""
        line = "12/31/2023, 10:15 PM - System message"
        date, time, author, message = _parse_android_line(line)
        
        assert date == "12/31/2023"
        assert time == "10:15 PM"
        assert author is None
        assert message == "System message"
    
    def test_ios_line_parsing(self):
        """Test iOS line parsing."""
        line = "[4/20/23, 4:21:43 AM] Shrey Khandelwal: Ek kaam Karo..."
        date, time, author, message = _parse_ios_line(line)
        
        assert date == "4/20/23"
        assert time == "4:21:43 AM"
        assert author == "Shrey Khandelwal"
        assert message == "Ek kaam Karo..."
    
    def test_ios_line_no_author(self):
        """Test iOS line without author."""
        line = "[4/20/23, 4:21:43 AM] System message"
        date, time, author, message = _parse_ios_line(line)
        
        assert date == "4/20/23"
        assert time == "4:21:43 AM"
        assert author is None
        assert message == "System message"
    
    def test_invalid_android_line(self):
        """Test invalid Android line parsing."""
        line = "Invalid format line"
        
        with pytest.raises(ChatParseError):
            _parse_android_line(line)
    
    def test_invalid_ios_line(self):
        """Test invalid iOS line parsing."""
        line = "Invalid format line"
        
        with pytest.raises(ChatParseError):
            _parse_ios_line(line)


class TestFormatDetection:
    """Test format detection functions."""
    
    def test_android_format_detection(self):
        """Test Android format detection."""
        valid_line = "12/31/2023, 10:15 PM - Alice: Hello!"
        assert _is_android_format(valid_line) is True
        
        invalid_line = "Not an Android format"
        assert _is_android_format(invalid_line) is False
    
    def test_ios_format_detection(self):
        """Test iOS format detection."""
        valid_line = "[4/20/23, 4:21:43 AM] Alice: Hello!"
        assert _is_ios_format(valid_line) is True
        
        invalid_line = "Not an iOS format"
        assert _is_ios_format(invalid_line) is False


class TestTimestampParsing:
    """Test timestamp parsing functionality."""
    
    def test_android_timestamp_parsing(self):
        """Test Android timestamp parsing."""
        # Test various Android formats
        test_cases = [
            ("12/31/2023", "10:15 PM", "android"),
            ("1/1/23", "9:30 AM", "android"),
            ("31/12/2023", "22:15", "android"),  # European format
        ]
        
        for date, time, platform in test_cases:
            timestamp = _parse_timestamp(date, time, platform)
            assert timestamp is not None
            assert isinstance(timestamp, datetime)
    
    def test_ios_timestamp_parsing(self):
        """Test iOS timestamp parsing."""
        # Test various iOS formats
        test_cases = [
            ("4/20/23", "4:21:43 AM", "ios"),
            ("20/4/2023", "16:21:43", "ios"),  # European format
            ("4-20-23", "4:21 PM", "ios"),
        ]
        
        for date, time, platform in test_cases:
            timestamp = _parse_timestamp(date, time, platform)
            assert timestamp is not None
            assert isinstance(timestamp, datetime)
    
    def test_invalid_timestamp(self):
        """Test invalid timestamp parsing."""
        timestamp = _parse_timestamp("invalid", "time", "android")
        assert timestamp is None


class TestFileContentDecoding:
    """Test file content decoding functionality."""
    
    def test_utf8_decoding(self):
        """Test UTF-8 decoding."""
        content = "Hello, world! 🌍".encode("utf-8")
        lines = _decode_file_content(content)
        
        assert len(lines) == 1
        assert lines[0] == "Hello, world! 🌍"
    
    def test_utf16_decoding(self):
        """Test UTF-16 decoding."""
        content = "Hello, world! 🌍".encode("utf-16")
        lines = _decode_file_content(content)
        
        assert len(lines) == 1
        assert lines[0] == "Hello, world! 🌍"
    
    def test_fallback_decoding(self):
        """Test fallback decoding with errors."""
        # Create content with invalid bytes
        content = b"Hello\xff\xfe\x00world"
        lines = _decode_file_content(content)
        
        assert len(lines) == 1
        assert "Hello" in lines[0]
        assert "world" in lines[0]


class TestLineCleaning:
    """Test line cleaning functionality."""
    
    def test_remove_directionality_marks(self):
        """Test removal of directionality marks."""
        line = "\u200eHello\u200f world"
        cleaned = _clean_line(line)
        
        assert cleaned == "Hello world"
    
    def test_remove_bom(self):
        """Test removal of BOM characters."""
        line = "\ufeffHello world\n"
        cleaned = _clean_line(line)
        
        assert cleaned == "Hello world"


class TestFullParsing:
    """Test complete chat parsing functionality."""
    
    def test_android_chat_parsing(self):
        """Test complete Android chat parsing."""
        android_chat = (
            "12/31/2023, 10:15 PM - Alice: Hello there!\n"
            "12/31/2023, 10:16 PM - Bob: Hi Alice!\n"
            "12/31/2023, 10:17 PM - Alice: How are you?\n"
        ).encode("utf-8")
        
        df = parse_chat(android_chat, platform="android")
        
        assert len(df) == 3
        assert list(df.columns) == ["Date", "Time", "Author", "Message", "ts", "date", "hour", "dow", "is_media"]
        assert df["Author"].iloc[0] == "Alice"
        assert df["Message"].iloc[1] == "Hi Alice!"
    
    def test_ios_chat_parsing(self):
        """Test complete iOS chat parsing."""
        ios_chat = (
            "[4/20/23, 4:21:43 AM] 343: Messages and calls are end-to-end encrypted.\n"
            "[4/20/23, 4:21:55 AM] Shrey Khandelwal: Ek kaam Karo...\n"
            "[4/20/23, 4:21:59 AM] Sayantan: Bruh 🗿\n"
        ).encode("utf-8")
        
        df = parse_chat(ios_chat, platform="ios")
        
        assert len(df) == 3
        assert list(df.columns) == ["Date", "Time", "Author", "Message", "ts", "date", "hour", "dow", "is_media"]
        assert df["Author"].iloc[1] == "Shrey Khandelwal"
        assert df["Message"].iloc[2] == "Bruh 🗿"
    
    def test_auto_platform_detection(self):
        """Test automatic platform detection."""
        android_chat = (
            "12/31/2023, 10:15 PM - Alice: Hello there!\n"
            "12/31/2023, 10:16 PM - Bob: Hi Alice!\n"
        ).encode("utf-8")
        
        df = parse_chat(android_chat, platform="auto")
        
        assert len(df) == 2
        assert df["Author"].iloc[0] == "Alice"
    
    def test_multiline_messages(self):
        """Test parsing of multiline messages."""
        chat_with_multiline = (
            "12/31/2023, 10:15 PM - Alice: Hello there!\n"
            "This is a continuation\n"
            "of the same message\n"
            "12/31/2023, 10:16 PM - Bob: Hi Alice!\n"
        ).encode("utf-8")
        
        df = parse_chat(chat_with_multiline, platform="android")
        
        assert len(df) == 2
        assert "continuation" in df["Message"].iloc[0]
        assert "same message" in df["Message"].iloc[0]
    
    def test_media_messages(self):
        """Test handling of media messages."""
        chat_with_media = (
            "12/31/2023, 10:15 PM - Alice: Hello there!\n"
            "12/31/2023, 10:16 PM - Bob: <Media omitted>\n"
            "12/31/2023, 10:17 PM - Alice: Nice photo!\n"
        ).encode("utf-8")
        
        df = parse_chat(chat_with_media, platform="android")
        
        assert len(df) == 3
        assert df["is_media"].iloc[1] is True
        assert df["is_media"].iloc[0] is False
        assert df["is_media"].iloc[2] is False


class TestErrorHandling:
    """Test error handling functionality."""
    
    def test_empty_content(self):
        """Test handling of empty content."""
        empty_content = b""
        
        with pytest.raises(ChatParseError):
            parse_chat(empty_content, platform="android")
    
    def test_no_valid_messages(self):
        """Test handling of content with no valid messages."""
        invalid_content = "This is not a valid chat format\n".encode("utf-8")
        
        with pytest.raises(ChatParseError):
            parse_chat(invalid_content, platform="android")
    
    def test_invalid_platform(self):
        """Test handling of invalid platform."""
        valid_content = "12/31/2023, 10:15 PM - Alice: Hello!".encode("utf-8")
        
        with pytest.raises(ValueError):
            parse_chat(valid_content, platform="invalid_platform")


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_single_message(self):
        """Test parsing of single message."""
        single_message = "12/31/2023, 10:15 PM - Alice: Hello!".encode("utf-8")
        
        df = parse_chat(single_message, platform="android")
        
        assert len(df) == 1
        assert df["Author"].iloc[0] == "Alice"
    
    def test_messages_with_special_characters(self):
        """Test parsing of messages with special characters."""
        special_chars = (
            "12/31/2023, 10:15 PM - Alice: Hello! 😀\n"
            "12/31/2023, 10:16 PM - Bob: Hi! 🌍\n"
        ).encode("utf-8")
        
        df = parse_chat(special_chars, platform="android")
        
        assert len(df) == 2
        assert "😀" in df["Message"].iloc[0]
        assert "🌍" in df["Message"].iloc[1]
    
    def test_various_date_formats(self):
        """Test parsing of various date formats."""
        date_formats = (
            "12/31/2023, 10:15 PM - Alice: US format\n"
            "31/12/2023, 22:15 - Bob: European format\n"
            "1/1/23, 9:30 AM - Charlie: Short year\n"
        ).encode("utf-8")
        
        df = parse_chat(date_formats, platform="android")
        
        assert len(df) == 3
        assert all(df["ts"].notna())  # All timestamps should be parsed successfully 