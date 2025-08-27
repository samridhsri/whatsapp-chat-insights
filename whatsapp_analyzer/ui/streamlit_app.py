"""
Streamlit web interface for WhatsApp Chat Analyzer.

This module provides a modern, interactive web interface for analyzing
WhatsApp chat exports with real-time visualizations and insights.
"""

import logging
import streamlit as st
from pathlib import Path
from typing import Optional, Dict, Any
import json

from ..core.parser import parse_chat, detect_platform, ChatParseError, PlatformDetectionError
from ..core.analyzer import ChatAnalyzer
from ..utils.emoji_extractor import extract_emojis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_page_config():
    """Configure Streamlit page settings."""
    st.set_page_config(
        page_title="WhatsApp Chat Analyzer",
        page_icon="📱",
        layout="wide",
        initial_sidebar_state="expanded"
    )


def create_sidebar() -> Dict[str, Any]:
    """Create and configure the sidebar with analysis options."""
    with st.sidebar:
        st.header("⚙️ Analysis Options")
        
        # Platform selection
        platform_choice = st.selectbox(
            "Chat Export Format",
            options=["Auto", "Android", "iOS"],
            index=0,
            help="Select the platform format of your WhatsApp export"
        )
        platform_key = {"Auto": "auto", "Android": "android", "iOS": "ios"}[platform_choice]
        
        # Analysis options
        include_media = st.toggle(
            "Include Media Messages",
            value=False,
            help="Include <Media omitted> and similar placeholder messages"
        )
        
        anonymize = st.toggle(
            "Anonymize Participants",
            value=False,
            help="Replace participant names with User 1, User 2, etc."
        )
        
        threshold_hours = st.slider(
            "Conversation Gap Threshold (hours)",
            min_value=1,
            max_value=24,
            value=1,
            help="Hours of inactivity to consider as new conversation"
        )
        
        # --- NEW: Sentiment rolling average slider ---
        sentiment_window = st.slider(
            "Sentiment Rolling Average (days)",
            min_value=1,
            max_value=30,
            value=7,
            help="Number of days for the sentiment rolling average window"
        )

        # Debug options
        with st.expander("🔧 Debug Options"):
            show_debug = st.toggle("Show Parsing Debug", value=False)
            run_tests = st.toggle("Run Developer Tests", value=False)
        
        st.markdown("---")
        st.caption(
            "💡 **Tip**: Use 'Auto' for automatic platform detection. "
            "iOS exports often use special Unicode spaces around timestamps."
        )
        
        return {
            "platform": platform_key,
            "include_media": include_media,
            "anonymize": anonymize,
            "threshold_hours": threshold_hours,
            "sentiment_window": sentiment_window, # New option
            "show_debug": show_debug,
            "run_tests": run_tests
        }


def display_upload_section() -> Optional[bytes]:
    """Display file upload section and return uploaded content."""
    st.title("📱 WhatsApp Chat Analyzer")
    st.caption(
        "Upload a WhatsApp chat export (.txt) to analyze conversation patterns, "
        "participant behavior, and engagement metrics."
    )
    
    uploaded_file = st.file_uploader(
        "Choose a WhatsApp chat export file",
        type=["txt"],
        help="Upload a .txt file exported from WhatsApp"
    )
    
    if not uploaded_file:
        st.info("👆 Please upload a WhatsApp chat export file to begin analysis.")
        st.stop()
    
    try:
        content = uploaded_file.getvalue()
        st.success(f"✅ Successfully uploaded {len(content)} bytes")
        return content
    except Exception as e:
        st.error(f"❌ Failed to read uploaded file: {e}")
        st.stop()


def display_debug_info(content: bytes, platform: str, show_debug: bool):
    """Display debug information if enabled."""
    if not show_debug:
        return
    
    with st.expander("🔎 Parsing Debug Information"):
        try:
            # Basic file info
            st.write("**File Information:**")
            st.json({
                "file_size_bytes": len(content),
                "file_size_kb": round(len(content) / 1024, 2),
                "platform_selected": platform
            })
            
            # Platform detection
            try:
                lines = content.decode("utf-8", errors="ignore").splitlines()
                detected_platform = detect_platform(lines)
                st.write(f"**Platform Detection:** {detected_platform}")
            except Exception as e:
                st.write(f"**Platform Detection Error:** {e}")
            
            # Sample lines
            st.write("**Sample Lines (first 5):**")
            sample_lines = content.decode("utf-8", errors="ignore").splitlines()[:5]
            for i, line in enumerate(sample_lines):
                st.code(f"{i+1}: {line}")
                
        except Exception as e:
            st.error(f"Debug info error: {e}")


def parse_and_analyze_chat(content: bytes, options: Dict[str, Any]) -> ChatAnalyzer:
    """Parse chat content and create analyzer instance."""
    with st.spinner("🔄 Parsing and analyzing chat data..."):
        try:
            # Parse chat
            df = parse_chat(content, platform=options["platform"])
            
            # Apply filters
            if not options["include_media"]:
                df = df[~df["is_media"]]
                st.info(f"📊 Filtered out media messages. {len(df)} text messages remaining.")
            
            # Anonymize if requested
            if options["anonymize"]:
                mapping = {
                    author: f"User {i+1}" 
                    for i, author in enumerate(sorted(df["Author"].dropna().unique()))
                }
                df["Author"] = df["Author"].map(mapping)
                st.info("🔒 Participant names anonymized.")
            
            # Create analyzer
            analyzer = ChatAnalyzer(df)
            return analyzer
            
        except (ChatParseError, PlatformDetectionError) as e:
            st.error(f"❌ Parsing failed: {e}")
            st.info("💡 Try switching the platform format or check if the file is a valid WhatsApp export.")
            st.stop()
        except Exception as e:
            st.error(f"❌ Unexpected error: {e}")
            logger.error(f"Analysis error: {e}")
            st.stop()


def display_key_metrics(analyzer: ChatAnalyzer):
    """Display key metrics in a clean layout."""
    stats = analyzer.get_basic_stats()
    
    # Create metric columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Messages",
            f"{stats['total_messages']:,}",
            help="Total number of messages in the chat"
        )
    
    with col2:
        st.metric(
            "Participants",
            stats['total_participants'],
            help="Number of unique participants"
        )
    
    with col3:
        st.metric(
            "Days Active",
            stats['days_active'],
            help="Number of days with chat activity"
        )
    
    with col4:
        st.metric(
            "Avg Words/Message",
            stats['avg_words_per_message'],
            help="Average words per text message"
        )
    
    # Date range
    st.caption(f"📅 Activity period: {stats['date_range']['start']} → {stats['date_range']['end']}")


def display_activity_charts(analyzer: ChatAnalyzer):
    """Display activity pattern charts."""
    st.subheader("📈 Activity Patterns")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Hourly Activity**")
        hourly_chart = analyzer.create_hourly_activity_chart()
        st.plotly_chart(hourly_chart, use_container_width=True)
    
    with col2:
        st.write("**Daily Activity**")
        daily_chart = analyzer.create_daily_activity_chart()
        st.plotly_chart(daily_chart, use_container_width=True)
    
    # Date timeline
    st.write("**Daily Message Timeline**")
    date_activity = analyzer.get_date_activity()
    st.line_chart(date_activity, use_container_width=True)

def display_sentiment_debugging(analyzer: ChatAnalyzer):
    """Display random messages and their sentiment for debugging."""
    with st.expander("🔎 View Sentiment Analysis Samples"):
        st.write("Here are some random messages and their calculated sentiment scores from the chat:")
        
        samples = analyzer.get_sentiment_samples(n=5)
        
        if samples.empty:
            st.info("No text messages available to sample.")
            return

        for _, row in samples.iterrows():
            author = row['Author'] if row['Author'] else "Unknown"
            message = row['Message']
            score = row['sentiment_score']
            label = row['sentiment_label']
            
            # Use columns for a cleaner layout
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"> _{message}_")
                st.caption(f"**Author:** {author}")
            with col2:
                # Color the label for quick visual feedback
                if label == "Positive":
                    st.success(f"**{label}** ({score:.2f})")
                elif label == "Negative":
                    st.error(f"**{label}** ({score:.2f})")
                else:
                    st.info(f"**{label}** ({score:.2f})")
            st.markdown("---")

# --- NEW: Function to display sentiment analysis ---
def display_sentiment_analysis(analyzer: ChatAnalyzer, rolling_window: int):
    """Display sentiment analysis over time."""
    st.subheader("😊 Sentiment Over Time")
    st.write(
        f"This chart shows the {rolling_window}-day rolling average of the chat's sentiment. "
        "Scores above 0 are positive, and scores below 0 are negative."
    )
    
    try:
        sentiment_chart = analyzer.create_sentiment_over_time_chart(rolling_window)
        st.plotly_chart(sentiment_chart, use_container_width=True)
        
        # --- NEW: Add the debugging expander here ---
        display_sentiment_debugging(analyzer)

    except Exception as e:
        st.warning(f"Could not generate sentiment chart: {e}")

def display_participant_analysis(analyzer: ChatAnalyzer):
    """Display participant analysis."""
    st.subheader("👥 Participant Analysis")
    
    # Top participants chart
    participant_chart = analyzer.create_participant_activity_chart(top_n=10)
    st.plotly_chart(participant_chart, use_container_width=True)
    
    # Participant statistics table
    with st.expander("📊 Detailed Participant Statistics"):
        participant_stats = analyzer.get_participant_stats()
        st.dataframe(participant_stats, use_container_width=True)


def display_engagement_metrics(analyzer: ChatAnalyzer, threshold_hours: int):
    """Display engagement and response metrics."""
    st.subheader("⚡ Engagement Metrics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Response Times**")
        try:
            response_times = analyzer.get_response_times(threshold_hours)
            if not response_times.empty:
                response_df = response_times.to_frame("Avg Response Time (seconds)")
                st.dataframe(response_df, use_container_width=True)
            else:
                st.info(f"No response time data for {threshold_hours}h threshold")
        except Exception as e:
            st.warning(f"Could not analyze response times: {e}")
    
    with col2:
        st.write("**Conversation Starters**")
        try:
            starters = analyzer.get_conversation_starters(threshold_hours)
            if not starters.empty:
                starter_chart = analyzer.create_conversation_starters_chart(threshold_hours)
                st.plotly_chart(starter_chart, use_container_width=True)
            else:
                st.info(f"No conversation starter data for {threshold_hours}h threshold")
        except Exception as e:
            st.warning(f"Could not analyze conversation starters: {e}")


def display_emoji_analysis(analyzer: ChatAnalyzer):
    """Display emoji usage analysis."""
    st.subheader("😀 Emoji Analysis")
    
    try:
        emoji_analysis = analyzer.get_emoji_analysis(extract_emojis)
        
        if emoji_analysis["total_emojis"] > 0:
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total Emojis", f"{emoji_analysis['total_emojis']:,}")
                st.metric("Unique Emojis", emoji_analysis['unique_emojis'])
            
            with col2:
                if emoji_analysis["top_emojis"]:
                    st.write("**Most Used Emojis:**")
                    for emoji, count in emoji_analysis["top_emojis"][:10]:
                        st.write(f"{emoji} x{count}")
        else:
            st.info("No emojis found in the chat")
            
    except Exception as e:
        st.warning(f"Could not analyze emojis: {e}")


def display_word_analysis(analyzer: ChatAnalyzer):
    """Display word usage analysis."""
    st.subheader("📝 Word Analysis")
    
    try:
        # Basic word stats
        word_analysis = analyzer.get_word_analysis()
        
        if word_analysis["total_words"] > 0:
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total Words", f"{word_analysis['total_words']:,}")
                st.metric("Unique Words", word_analysis['unique_words'])
            
            with col2:
                if word_analysis["top_words"]:
                    st.write("**Most Used Words:**")
                    for word, count in word_analysis["top_words"][:15]:
                        st.write(f"'{word}' x{count}")
        else:
            st.info("No word data available")
            
    except Exception as e:
        st.warning(f"Could not analyze words: {e}")


def display_data_preview(analyzer: ChatAnalyzer):
    """Display preview of parsed data."""
    with st.expander("📋 Preview Parsed Data"):
        st.dataframe(
            analyzer.chat_data.head(200),
            use_container_width=True,
            column_config={
                "ts": st.column_config.DatetimeColumn("Timestamp"),
                "Message": st.column_config.TextColumn("Message", width="large")
            }
        )

def display_export_options(analyzer: ChatAnalyzer):
    """Display data export options."""
    st.subheader("💾 Export Options")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # CSV export
        csv_data = analyzer.chat_data.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📊 Download CSV",
            data=csv_data,
            file_name="whatsapp_chat_analysis.csv",
            mime="text/csv"
        )
    
    with col2:
        # Excel export with robust temporary file handling
        import tempfile
        import os

        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        tmp_filename = tmp_file.name
        tmp_file.close()

        try:
            analyzer.export_analysis_report(tmp_filename)
            with open(tmp_filename, 'rb') as f:
                excel_data = f.read()
            
            st.download_button(
                "📊 Download Excel Report",
                data=excel_data,
                file_name="whatsapp_chat_analysis.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except Exception as e:
            st.error(f"Excel export failed: {e}")
        finally:
            if os.path.exists(tmp_filename):
                os.unlink(tmp_filename)
    
    with col3:
        # JSON export
        def convert_keys_to_str(obj: Any) -> Any:
            if isinstance(obj, dict):
                return {str(k): convert_keys_to_str(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [convert_keys_to_str(elem) for elem in obj]
            return obj

        try:
            insights = analyzer.get_all_insights()
            sanitized_insights = convert_keys_to_str(insights)
            json_data = json.dumps(sanitized_insights, indent=2, default=str, ensure_ascii=False)
            
            st.download_button(
                "📊 Download JSON",
                data=json_data.encode("utf-8"),
                file_name="whatsapp_chat_insights.json",
                mime="application/json"
            )
        except Exception as e:
            st.error(f"JSON export failed: {e}")


def run_developer_tests(run_tests: bool):
    """Run developer tests if requested."""
    if not run_tests:
        return
    
    with st.expander("🧪 Developer Tests"):
        try:
            # Import test function
            from ..core.parser import _run_tests
            test_results = _run_tests()
            st.json(test_results)
        except Exception as e:
            st.error(f"Test execution failed: {e}")


def main():
    """Main Streamlit application."""
    setup_page_config()
    
    try:
        # Create sidebar and get options
        options = create_sidebar()
        
        # Display upload section
        content = display_upload_section()
        
        # Show debug info if enabled
        display_debug_info(content, options["platform"], options["show_debug"])
        
        # Parse and analyze chat
        analyzer = parse_and_analyze_chat(content, options)
        
        # Display results
        display_key_metrics(analyzer)
        
        # Activity patterns
        display_activity_charts(analyzer)

        # --- NEW: Call the sentiment analysis display function ---
        display_sentiment_analysis(analyzer, options["sentiment_window"])
        
        # Participant analysis
        display_participant_analysis(analyzer)
        
        # Engagement metrics
        display_engagement_metrics(analyzer, options["threshold_hours"])
        
        # Emoji analysis
        display_emoji_analysis(analyzer)
        
        # Word analysis
        display_word_analysis(analyzer)
        
        # Data preview
        display_data_preview(analyzer)
        
        # Export options
        display_export_options(analyzer)
        
        # Developer tests
        run_developer_tests(options["run_tests"])
        
        # Footer
        st.markdown("---")
        st.caption(
            "🔒 **Privacy**: All analysis is performed locally in your browser. "
            "No chat data is stored on our servers."
        )
        
    except Exception as e:
        st.error(f"❌ Application error: {e}")
        logger.error(f"Streamlit app error: {e}")
        st.stop()


if __name__ == "__main__":
    main()