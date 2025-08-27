"""
Core analysis functionality for WhatsApp chat data.

This module provides the ChatAnalyzer class, which performs various
analyses on a parsed chat DataFrame, from basic stats to complex
engagement and temporal pattern detection.
"""

import logging
import re
from typing import Dict, Any, List, Optional, Callable

import pandas as pd
import plotly.express as px
from collections import Counter
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

logger = logging.getLogger(__name__)


class ChatAnalyzer:
    """
    Analyzes a WhatsApp chat DataFrame to extract insights and visualizations.
    
    Attributes:
        chat_data (pd.DataFrame): The input DataFrame of parsed chat messages.
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize the analyzer with a chat DataFrame.
        
        Args:
            df: A DataFrame containing parsed WhatsApp chat data.
        """
        if not isinstance(df, pd.DataFrame) or df.empty:
            raise ValueError("A non-empty pandas DataFrame is required.")
        
        # --- FIX: Sort by timestamp to ensure correct chronological order ---
        # This is crucial for accurate time difference calculations (e.g., response times).
        df = df.sort_values(by="ts").reset_index(drop=True)
        
        self.chat_data = df.copy()
        self._analyze_sentiment()

    def _analyze_sentiment(self):
        """
        Calculate sentiment scores for each message using VADER.
        
        This method adds 'sentiment_score' and 'sentiment_label' columns
        to the chat_data DataFrame.
        """
        analyzer = SentimentIntensityAnalyzer()
        messages = self.chat_data['Message'].astype(str)
        sentiment_scores = messages.apply(
            lambda msg: analyzer.polarity_scores(msg)['compound']
        )
        self.chat_data['sentiment_score'] = sentiment_scores
        
        def to_label(score):
            if score > 0.05: return "Positive"
            elif score < -0.05: return "Negative"
            else: return "Neutral"
        
        self.chat_data['sentiment_label'] = sentiment_scores.apply(to_label)
        logger.info("Completed sentiment analysis on chat data.")

    # --- NEW: Function to get random samples for sentiment debugging ---
    def get_sentiment_samples(self, n: int = 5) -> pd.DataFrame:
        """
        Get n random samples of messages with their sentiment scores for debugging.
        
        Args:
            n: The number of random samples to return.
            
        Returns:
            A DataFrame with sample messages and their sentiment scores.
        """
        # Exclude media messages as they have no sentiment
        text_messages = self.chat_data[~self.chat_data["is_media"]]
        if text_messages.empty:
            return pd.DataFrame()
        
        # Ensure we don't request more samples than available messages
        num_samples = min(n, len(text_messages))
        
        return text_messages.sample(n=num_samples)[
            ["Author", "Message", "sentiment_score", "sentiment_label"]
        ]

    def get_basic_stats(self) -> Dict[str, Any]:
        """Get basic statistics from the chat data."""
        total_messages = len(self.chat_data)
        total_participants = self.chat_data["Author"].nunique()
        days_active = self.chat_data["date"].nunique()
        text_messages = self.chat_data[~self.chat_data["is_media"]]
        avg_words = round(text_messages["Message"].str.split().str.len().mean(), 2)
        
        return {
            "total_messages": total_messages,
            "total_participants": total_participants,
            "days_active": days_active,
            "avg_words_per_message": avg_words,
            "date_range": {
                "start": self.chat_data["date"].min().strftime("%Y-%m-%d"),
                "end": self.chat_data["date"].max().strftime("%Y-%m-%d"),
            },
        }

    def get_date_activity(self) -> pd.Series:
        """Get message count per date."""
        return self.chat_data.groupby("date")["Message"].count()

    def create_hourly_activity_chart(self) -> px.bar:
        """Create a bar chart of messages per hour."""
        hourly_activity = self.chat_data.groupby("hour")["Message"].count()
        chart = px.bar(
            hourly_activity, x=hourly_activity.index, y=hourly_activity.values,
            labels={"x": "Hour of Day", "y": "Number of Messages"}, template="plotly_white"
        )
        chart.update_layout(showlegend=False)
        return chart

    def create_daily_activity_chart(self) -> px.bar:
        """Create a bar chart of messages per day of the week."""
        daily_activity = self.chat_data.groupby("dow")["Message"].count()
        days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        daily_activity = daily_activity.reindex(days_order)
        chart = px.bar(
            daily_activity, x=daily_activity.index, y=daily_activity.values,
            labels={"x": "Day of Week", "y": "Number of Messages"}, template="plotly_white"
        )
        chart.update_layout(showlegend=False)
        return chart
    
    def get_participant_stats(self) -> pd.DataFrame:
        """Get detailed statistics for each participant."""
        stats = (
            self.chat_data.groupby("Author").agg(
                messages=("Message", "count"),
                words=("Message", lambda s: s.str.split().str.len().sum()),
                media_sent=("is_media", "sum"),
            ).sort_values(by="messages", ascending=False)
        )
        stats["avg_words"] = (stats["words"] / (stats["messages"] - stats["media_sent"])).round(2)
        return stats

    def create_participant_activity_chart(self, top_n: int = 10) -> px.bar:
        """Create a bar chart of top N participants by message count."""
        participant_activity = self.chat_data["Author"].value_counts().nlargest(top_n)
        chart = px.bar(
            participant_activity, x=participant_activity.index, y=participant_activity.values,
            labels={"x": "Participant", "y": "Number of Messages"}, template="plotly_white"
        )
        chart.update_layout(showlegend=False)
        return chart

    def get_response_times(self, threshold_hours: int) -> pd.Series:
        """Calculate average response time for each participant."""
        self.chat_data["time_diff"] = self.chat_data["ts"].diff().dt.total_seconds()
        response_df = self.chat_data[
            (self.chat_data["Author"] != self.chat_data["Author"].shift(1)) &
            (self.chat_data["time_diff"] < threshold_hours * 3600)
        ]
        avg_response_times = response_df.groupby("Author")["time_diff"].mean().sort_values()
        return avg_response_times.round(2)

    def get_conversation_starters(self, threshold_hours: int) -> pd.Series:
        """Identify who starts conversations most often."""
        time_diff = self.chat_data["ts"].diff().dt.total_seconds()
        starters = self.chat_data[time_diff > threshold_hours * 3600]["Author"].value_counts()
        return starters

    def create_conversation_starters_chart(self, threshold_hours: int) -> px.pie:
        """Create a pie chart of conversation starters."""
        starters = self.get_conversation_starters(threshold_hours)
        chart = px.pie(
            starters, values=starters.values, names=starters.index, template="plotly_white"
        )
        chart.update_traces(textposition='inside', textinfo='percent+label')
        return chart

    def create_sentiment_over_time_chart(self, rolling_window: int = 7) -> px.line:
        """Create a line chart showing the trend of sentiment over time."""
        daily_sentiment = self.chat_data.groupby('date')['sentiment_score'].mean().reset_index()
        daily_sentiment['rolling_avg'] = daily_sentiment['sentiment_score'].rolling(
            window=rolling_window, min_periods=1
        ).mean()
        chart = px.line(
            daily_sentiment, x='date', y='rolling_avg',
            labels={'date': 'Date', 'rolling_avg': f'{rolling_window}-Day Rolling Avg. Sentiment'},
            template='plotly_white'
        )
        chart.add_hline(y=0, line_dash="dash", line_color="grey")
        chart.update_layout(yaxis_title="Sentiment (Negative to Positive)", showlegend=False)
        return chart

    def get_emoji_analysis(self, emoji_extractor_func: Callable) -> Dict[str, Any]:
        """Analyze emoji usage in the chat."""
        all_emojis = [
            emoji for msg in self.chat_data["Message"] for emoji in emoji_extractor_func(msg)
        ]
        if not all_emojis:
            return {"total_emojis": 0, "unique_emojis": 0, "top_emojis": []}
        emoji_counts = Counter(all_emojis)
        return {
            "total_emojis": len(all_emojis), "unique_emojis": len(emoji_counts),
            "top_emojis": emoji_counts.most_common(10),
        }

    def get_word_analysis(self, top_n: int = 20) -> Dict[str, Any]:
        """Analyze word frequency, excluding common stop words."""
        stop_words = set([
            'the', 'a', 'an', 'in', 'is', 'it', 'to', 'for', 'of', 'on', 'and', 'i', 'you',
            'that', 'be', 'with', 'was', 'are', 'this', 'have', 'but', 'not', 'at', 'my', 'me'
        ])
        text_messages = self.chat_data[~self.chat_data["is_media"]]["Message"].astype(str)
        words = text_messages.str.lower().str.findall(r'\b\w+\b').explode()
        filtered_words = words[~words.isin(stop_words) & words.notna()]
        if filtered_words.empty:
            return {"total_words": 0, "unique_words": 0, "top_words": []}
        word_counts = Counter(filtered_words)
        return {
            "total_words": len(filtered_words), "unique_words": len(word_counts),
            "top_words": word_counts.most_common(top_n),
        }

    def get_all_insights(self) -> Dict[str, Any]:
        """Get all analysis insights as a single dictionary."""
        return {
            "basic_stats": self.get_basic_stats(),
            "participant_stats": self.get_participant_stats().to_dict('index'),
            "word_analysis": self.get_word_analysis(),
        }

    def export_analysis_report(self, file_path: str):
        """Export analysis to an Excel file with multiple sheets."""
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            self.chat_data.to_excel(writer, sheet_name='Raw Data', index=False)
            self.get_participant_stats().to_excel(writer, sheet_name='Participant Stats')
            basic_stats_df = pd.DataFrame.from_dict(
                self.get_basic_stats(), orient='index', columns=['Value']
            )
            basic_stats_df.to_excel(writer, sheet_name='Summary')