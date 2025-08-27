#!/usr/bin/env python3
"""
WhatsApp Chat Analyzer - Main Entry Point

This script provides a unified entry point that can run either:
1. Streamlit web interface (if streamlit is available)
2. Command-line interface (fallback)

Usage:
    # To run the Streamlit UI
    streamlit run main.py

    # To run the CLI
    python main.py --cli [CLI_OPTIONS]
"""

import sys
import argparse
from pathlib import Path

def main():
    """Main entry point for handling CLI or guiding user to run Streamlit."""

    # Check if Streamlit is available
    try:
        import streamlit
        STREAMLIT_AVAILABLE = True
    except ImportError:
        STREAMLIT_AVAILABLE = False

    parser = argparse.ArgumentParser(
        description="WhatsApp Chat Analyzer - Unified Entry Point",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Note: The --ui flag is removed as it's not the correct way to launch the app.
    # The primary way to run the UI is now 'streamlit run main.py'.

    parser.add_argument(
        "--cli",
        action="store_true",
        help="Force CLI mode"
    )

    # Pass through any other arguments to CLI
    parser.add_argument("cli_args", nargs=argparse.REMAINDER, help="CLI arguments")

    args = parser.parse_args()

    # Determine which interface to use
    if args.cli:
        run_cli(args.cli_args)
    elif STREAMLIT_AVAILABLE:
        # If no flags are provided and Streamlit is installed, guide the user.
        print("✅ Streamlit UI is available.")
        print("   To launch the web interface, please run this command in your terminal:")
        print("\n       streamlit run main.py\n")
    else:
        # If Streamlit is not available and --cli is not specified, default to CLI help.
        print("💻 Streamlit not available. Running in CLI mode.")
        run_cli(["--help"])

def run_streamlit_ui():
    """
    This function contains the Streamlit app logic.
    It will be executed automatically when you run 'streamlit run main.py'.
    """
    try:
        from whatsapp_analyzer.ui.streamlit_app import main as streamlit_main
        streamlit_main()
    except Exception as e:
        # In a real Streamlit app, you might use st.error(e)
        print(f"❌ Streamlit UI error: {e}")

def run_cli(cli_args):
    """Run the command-line interface."""
    try:
        from whatsapp_analyzer.cli import main as cli_main

        # If no CLI args provided, show help
        if not cli_args:
            cli_args = ["--help"]

        # Set sys.argv for CLI argument parsing
        original_argv = sys.argv
        sys.argv = ["whatsapp-analyzer"] + cli_args

        try:
            cli_main()
        finally:
            # Restore original argv
            sys.argv = original_argv

    except ImportError as e:
        print(f"❌ Failed to import CLI: {e}")
        print("Please ensure the package is properly installed.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ CLI error: {e}")
        sys.exit(1)

# This check ensures that run_streamlit_ui() is only called when executed by Streamlit
if __name__ == "__main__":
    # The 'streamlit' module is added to sys.modules by the 'streamlit run' command.
    # We check for its presence to decide whether to run the UI or the CLI dispatcher.
    if 'streamlit' in sys.modules:
        run_streamlit_ui()
    else:
        main()