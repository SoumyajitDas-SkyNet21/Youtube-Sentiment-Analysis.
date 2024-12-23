import streamlit as st
from googleapiclient.discovery import build
import re
import emoji
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import matplotlib.pyplot as plt
from wordcloud import WordCloud

# Using the concept of environment variables 
from dotenv import load_dotenv 
import os

load_dotenv()  

# Loading the api key using environmental variables
API_KEY = os.getenv("API_KEY")


# API_KEY for YouTube API
# Replace with your YouTube API key
youtube = build('youtube', 'v3', developerKey=API_KEY)

# Function to fetch YouTube comments
def fetch_comments(video_id):
    comments = []
    nextPageToken = None
    while len(comments) < 600:
        request = youtube.commentThreads().list(
            part='snippet',
            videoId=video_id,
            maxResults=100,
            pageToken=nextPageToken
        )
        response = request.execute()
        for item in response['items']:
            comment = item['snippet']['topLevelComment']['snippet']
            comments.append(comment['textDisplay'])
        nextPageToken = response.get('nextPageToken')
        if not nextPageToken:
            break
    return comments

# Function for sentiment analysis
def sentiment_scores(comment):
    sentiment_analyzer = SentimentIntensityAnalyzer()
    sentiment_dict = sentiment_analyzer.polarity_scores(comment)
    return sentiment_dict['compound']

# Streamlit interface
st.markdown(
    """
    <h1 style='text-align: center; font-size: 2.5em;'>
    YouTube Comment Sentiment Analysis
    </h1>
    """,
    unsafe_allow_html=True
)

# Input field for YouTube video URL
video_url = st.text_input('Enter YouTube Video URL')

# Add an "Analyze" button
if st.button("Analyze"):
    if video_url:
        try:
            # Extract video ID from URL
            video_id = video_url[-11:]

            # Fetch comments
            comments = fetch_comments(video_id)

            if not comments:
                st.write("No comments fetched. Please check the video URL.")
            else:
                st.write(f"Fetched {len(comments)} comments.")

            # Filter comments (example for text-heavy comments)
            threshold_ratio = 0.65
            relevant_comments = []
            for comment_text in comments:
                comment_text = comment_text.lower().strip()
                emojis_count = emoji.emoji_count(comment_text)
                text_characters = len(re.sub(r'\s', '', comment_text))
                if any(char.isalnum() for char in comment_text) and (emojis_count == 0 or (text_characters / (text_characters + emojis_count)) > threshold_ratio):
                    relevant_comments.append(comment_text)

            # Sentiment analysis
            polarities = [sentiment_scores(comment) for comment in relevant_comments]
            positive = len([p for p in polarities if p > 0.05])
            negative = len([p for p in polarities if p < -0.05])
            neutral = len(relevant_comments) - positive - negative

            # Visualization
            st.write("### Sentiment Distribution")
            labels = ['Positive', 'Negative', 'Neutral']
            comment_counts = [positive, negative, neutral]
            colors = ['#76c7c0', '#f76c6c', '#ffcc5c']

            # Bar Chart
            st.write("#### Bar Chart")
            st.bar_chart(comment_counts)

            # Pie Chart
            st.write("#### Pie Chart")
            fig, ax = plt.subplots()
            ax.pie(comment_counts, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors)
            ax.set_title('Sentiment Distribution (Pie Chart)')
            st.pyplot(fig)

            # Donut Chart
            st.write("#### Donut Chart")
            fig, ax = plt.subplots()
            wedges, texts, autotexts = ax.pie(
                comment_counts, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors,
                wedgeprops={'width': 0.3, 'edgecolor': 'w'}
            )
            ax.set_title('Sentiment Distribution (Donut Chart)')
            st.pyplot(fig)

            # Word Cloud
            st.write("#### Word Cloud")
            text = ' '.join(relevant_comments)
            wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.imshow(wordcloud, interpolation='bilinear')
            ax.axis('off')
            st.pyplot(fig)

        except Exception as e:
            st.write(f"An error occurred: {e}")
    else:
        st.write("Please enter a YouTube video URL.")
