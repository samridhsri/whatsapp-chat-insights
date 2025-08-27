"""
Command-line interface for WhatsApp Chat Analyzer.

This module provides a robust CLI for analyzing WhatsApp chat exports
without requiring a web interface.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Optional

from .core.parser import parse_chat, detect_platform, ChatParseError, PlatformDetectionError
from .core.analyzer import ChatAnalyzer
from .utils.emoji_extractor import extract_emojis

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False, debug: bool = False) -> None:
    """Configure logging based on verbosity flags."""
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
    elif verbose:
        logging.getLogger().setLevel(logging.INFO)
    else:
        logging.getLogger().setLevel(logging.WARNING)


def read_input_file(file_path: str) -> bytes:
    """
    Read file content from the specified path.
    
    Args:
        file_path: Path to the file to read
        
    Returns:
        File content as bytes
        
    Raises:
        FileNotFoundError: If file doesn't exist
        PermissionError: If file can't be read
    """
    try:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")
        
        with open(path, 'rb') as f:
            content = f.read()
        
        logger.info(f"Successfully read {len(content)} bytes from {file_path}")
        return content
        
    except Exception as e:
        logger.error(f"Failed to read file {file_path}: {e}")
        raise


def read_stdin() -> bytes:
    """
    Read content from standard input.
    
    Returns:
        Content from stdin as bytes
    """
    try:
        content = sys.stdin.buffer.read()
        if not content:
            logger.warning("No content received from stdin")
        else:
            logger.info(f"Successfully read {len(content)} bytes from stdin")
        return content
    except Exception as e:
        logger.error(f"Failed to read from stdin: {e}")
        raise


def get_demo_data(platform: str) -> bytes:
    """
    Get demo data for testing.
    
    Args:
        platform: Platform identifier ('android' or 'ios')
        
    Returns:
        Demo chat data as bytes
    """
    if platform == "ios":
        demo_data = (
            "[4/20/23,\u202f4:21:43\u202fAM] 343: \u200eMessages and calls are end-to-end encrypted.\n"
            "[4/20/23,\u202f4:21:55\u202fAM] Shrey Khandelwal: Ek kaam Karo...\n"
            "[4/20/23,\u202f4:21:59\u202fAM] Sayantan: Bruh 🗿\n"
        ).encode("utf-8")
    else:  # android
        demo_data = (
            "12/31/2023, 10:15 PM - Alice: Happy New Year 😀\n"
            "12/31/2023, 10:16 PM - Bob: Same to you!\n"
            "12/31/2023, 10:17 PM - Alice: <Media omitted>\n"
        ).encode("utf-8")
    
    logger.info(f"Using demo data for {platform} platform")
    return demo_data


def analyze_chat(chat_data: bytes, platform: str, include_media: bool = False) -> ChatAnalyzer:
    """
    Parse and analyze chat data.
    
    Args:
        chat_data: Raw chat data
        platform: Platform identifier
        include_media: Whether to include media messages
        
    Returns:
        ChatAnalyzer instance with parsed data
    """
    try:
        # Parse chat data
        df = parse_chat(chat_data, platform=platform)
        
        # Filter media if requested
        if not include_media:
            df = df[~df["is_media"]]
            logger.info(f"Filtered out media messages, {len(df)} text messages remaining")
        
        # Create analyzer
        analyzer = ChatAnalyzer(df)
        return analyzer
        
    except (ChatParseError, PlatformDetectionError) as e:
        logger.error(f"Failed to parse chat: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during analysis: {e}")
        raise


def print_basic_stats(analyzer: ChatAnalyzer) -> None:
    """Print basic statistics to stdout."""
    stats = analyzer.get_basic_stats()
    
    print("\n" + "="*50)
    print("📊 BASIC STATISTICS")
    print("="*50)
    print(f"Total Messages: {stats['total_messages']:,}")
    print(f"Participants: {stats['total_participants']}")
    print(f"Days Active: {stats['days_active']}")
    print(f"Date Range: {stats['date_range']['start']} → {stats['date_range']['end']}")
    print(f"Total Words: {stats['total_words']:,}")
    print(f"Total Characters: {stats['total_characters']:,}")
    print(f"Media Messages: {stats['media_messages']}")
    print(f"Text Messages: {stats['text_messages']}")
    print(f"Avg Words/Message: {stats['avg_words_per_message']}")
    print(f"Avg Chars/Message: {stats['avg_chars_per_message']}")


def print_participant_stats(analyzer: ChatAnalyzer, top_n: int = 10) -> None:
    """Print participant statistics to stdout."""
    participant_stats = analyzer.get_participant_stats()
    
    print("\n" + "="*50)
    print(f"👥 TOP {top_n} PARTICIPANTS")
    print("="*50)
    
    top_participants = participant_stats.head(top_n)
    
    for i, (participant, stats) in enumerate(top_participants.iterrows(), 1):
        print(f"\n{i}. {participant}")
        print(f"   Messages: {stats['message_count']:,}")
        print(f"   Words: {stats['total_words']:,}")
        print(f"   Avg Words/Message: {stats['avg_words_per_message']}")
        print(f"   Activity Period: {stats['activity_days']} days")


def print_activity_patterns(analyzer: ChatAnalyzer) -> None:
    """Print activity pattern analysis to stdout."""
    print("\n" + "="*50)
    print("⏰ ACTIVITY PATTERNS")
    print("="*50)
    
    # Hourly activity
    hourly = analyzer.get_hourly_activity()
    peak_hour = hourly.idxmax()
    peak_count = hourly.max()
    print(f"\nPeak Activity Hour: {peak_hour}:00 ({peak_count} messages)")
    
    # Daily activity
    daily = analyzer.get_daily_activity()
    peak_day = daily.idxmax()
    peak_day_count = daily.max()
    print(f"Peak Activity Day: {peak_day} ({peak_day_count} messages)")
    
    # Date activity
    date_activity = analyzer.get_date_activity()
    if not date_activity.empty:
        busiest_date = date_activity.idxmax()
        busiest_count = date_activity.max()
        print(f"Busiest Date: {busiest_date} ({busiest_count} messages)")


def print_response_analysis(analyzer: ChatAnalyzer, threshold_hours: int = 1) -> None:
    """Print response time analysis to stdout."""
    try:
        response_times = analyzer.get_response_times(threshold_hours)
        
        if not response_times.empty:
            print("\n" + "="*50)
            print(f"⚡ RESPONSE TIME ANALYSIS (>={threshold_hours}h gap)")
            print("="*50)
            
            fastest_responder = response_times.index[0]
            fastest_time = response_times.iloc[0]
            print(f"\nFastest Responder: {fastest_responder}")
            print(f"Average Response Time: {fastest_time:.0f} seconds")
            
            if len(response_times) > 1:
                slowest_responder = response_times.index[-1]
                slowest_time = response_times.iloc[-1]
                print(f"Slowest Responder: {slowest_responder}")
                print(f"Average Response Time: {slowest_time:.0f} seconds")
        else:
            print(f"\nNo response time data available for {threshold_hours}h threshold")
            
    except Exception as e:
        logger.warning(f"Could not analyze response times: {e}")


def print_conversation_starters(analyzer: ChatAnalyzer, threshold_hours: int = 1) -> None:
    """Print conversation starter analysis to stdout."""
    try:
        starters = analyzer.get_conversation_starters(threshold_hours)
        
        if not starters.empty:
            print("\n" + "="*50)
            print(f"💬 CONVERSATION STARTERS (>={threshold_hours}h gap)")
            print("="*50)
            
            for i, (participant, count) in enumerate(starters.head(5).items(), 1):
                print(f"{i}. {participant}: {count} conversations started")
        else:
            print(f"\nNo conversation starter data available for {threshold_hours}h threshold")
            
    except Exception as e:
        logger.warning(f"Could not analyze conversation starters: {e}")


def print_emoji_analysis(analyzer: ChatAnalyzer) -> None:
    """Print emoji analysis to stdout."""
    try:
        emoji_analysis = analyzer.get_emoji_analysis(extract_emojis)
        
        if emoji_analysis["total_emojis"] > 0:
            print("\n" + "="*50)
            print("😀 EMOJI ANALYSIS")
            print("="*50)
            print(f"Total Emojis: {emoji_analysis['total_emojis']:,}")
            print(f"Unique Emojis: {emoji_analysis['unique_emojis']}")
            
            if emoji_analysis["top_emojis"]:
                print("\nTop 10 Emojis:")
                for emoji, count in emoji_analysis["top_emojis"][:10]:
                    print(f"  {emoji}  x{count}")
        else:
            print("\nNo emojis found in the chat")
            
    except Exception as e:
        logger.warning(f"Could not analyze emojis: {e}")


def export_results(analyzer: ChatAnalyzer, output_path: str, format_type: str = "excel") -> None:
    """
    Export analysis results to file.
    
    Args:
        analyzer: ChatAnalyzer instance
        output_path: Path to save results
        format_type: Export format ('excel', 'csv', 'json')
    """
    try:
        if format_type == "excel":
            analyzer.export_analysis_report(output_path)
            print(f"\n📊 Analysis report exported to: {output_path}")
        elif format_type == "csv":
            # Export main data
            csv_path = output_path.replace('.xlsx', '.csv')
            analyzer.chat_data.to_csv(csv_path, index=False)
            print(f"\n📊 Chat data exported to: {csv_path}")
        elif format_type == "json":
            # Export insights as JSON
            json_path = output_path.replace('.xlsx', '.json')
            insights = analyzer.get_all_insights()
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(insights, f, indent=2, default=str, ensure_ascii=False)
            print(f"\n📊 Analysis insights exported to: {json_path}")
            
    except Exception as e:
        logger.error(f"Failed to export results: {e}")
        raise


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="WhatsApp Chat Analyzer - Command Line Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze a chat file with auto-detection
  whatsapp-analyzer --file chat.txt
  
  # Force iOS platform detection
  whatsapp-analyzer --file chat.txt --platform ios
  
  # Read from stdin and export to Excel
  cat chat.txt | whatsapp-analyzer --stdin --export report.xlsx
  
  # Verbose output with debug info
  whatsapp-analyzer --file chat.txt --verbose --debug
        """
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--file", "-f",
        type=str,
        help="Path to WhatsApp chat export file (.txt)"
    )
    input_group.add_argument(
        "--stdin",
        action="store_true",
        help="Read chat data from standard input"
    )
    input_group.add_argument(
        "--demo",
        action="store_true",
        help="Use built-in demo data for testing"
    )
    
    # Analysis options
    parser.add_argument(
        "--platform", "-p",
        choices=["auto", "android", "ios"],
        default="auto",
        help="Chat export platform (default: auto-detect)"
    )
    parser.add_argument(
        "--include-media",
        action="store_true",
        help="Include media placeholder messages in analysis"
    )
    parser.add_argument(
        "--threshold-hours",
        type=int,
        default=1,
        help="Hours of inactivity to consider as new conversation (default: 1)"
    )
    
    # Output options
    parser.add_argument(
        "--export", "-o",
        type=str,
        help="Export results to file (supports .xlsx, .csv, .json)"
    )
    parser.add_argument(
        "--format",
        choices=["excel", "csv", "json"],
        default="excel",
        help="Export format when using --export (default: excel)"
    )
    
    # Control options
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug output"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress all output except errors"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose, args.debug)
    
    if args.quiet:
        logging.getLogger().setLevel(logging.ERROR)
    
    try:
        # Determine input source
        if args.demo:
            chat_data = get_demo_data(args.platform if args.platform != "auto" else "android")
        elif args.stdin:
            chat_data = read_stdin()
        else:
            chat_data = read_input_file(args.file)
        
        if not chat_data:
            logger.error("No chat data available for analysis")
            return 1
        
        # Analyze chat
        analyzer = analyze_chat(chat_data, args.platform, args.include_media)
        
        # Print analysis results
        if not args.quiet:
            print_basic_stats(analyzer)
            print_participant_stats(analyzer)
            print_activity_patterns(analyzer)
            print_response_analysis(analyzer, args.threshold_hours)
            print_conversation_starters(analyzer, args.threshold_hours)
            print_emoji_analysis(analyzer)
        
        # Export results if requested
        if args.export:
            export_results(analyzer, args.export, args.format)
        
        return 0
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 130
    except (FileNotFoundError, PermissionError) as e:
        logger.error(f"File error: {e}")
        return 1
    except (ChatParseError, PlatformDetectionError) as e:
        logger.error(f"Parsing error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main()) 