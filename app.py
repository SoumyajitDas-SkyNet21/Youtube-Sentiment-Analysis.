import streamlit as st
from googleapiclient.discovery import build
import re
import emoji
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import numpy as np

# API_KEY for YouTube API
API_KEY = 'AIzaSyAKylkn9ANwkb2gA1q8MEVpMrs_a_UbHJY'
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
st.title('YouTube Comment Sentiment Analysis')



# Input field for YouTube video URL
video_url = st.text_input('Enter YouTube Video URL')

if video_url:
    # Extract video ID from URL
    video_id = video_url[-11:]
    st.write(f"Fetching comments for Video ID: {video_id}")

    # Fetch comments
    comments = fetch_comments(video_id)

    # Filter relevant comments
    relevant_comments = []
    threshold_ratio = 0.75
    hyperlink_pattern = re.compile(
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')

    for comment_text in comments:
        comment_text = comment_text.lower().strip()
        if hyperlink_pattern.search(comment_text):
            continue
        emojis_count = emoji.emoji_count(comment_text)
        text_characters = len(re.sub(r'\s', '', comment_text))
        if any(char.isalnum() for char in comment_text):
            if emojis_count == 0 or (text_characters / (text_characters + emojis_count)) > threshold_ratio:
                relevant_comments.append(comment_text)

    # Analyze sentiments
    positive_comments, negative_comments, neutral_comments = [], [], []
    polarity = []

    for comment in relevant_comments:
        score = sentiment_scores(comment)
        polarity.append(score)
        if score > 0.05:
            positive_comments.append(comment)
        elif score < -0.05:
            negative_comments.append(comment)
        else:
            neutral_comments.append(comment)

    # Display Sentiment Distribution as Bar Chart
    comment_counts = [len(positive_comments), len(negative_comments), len(neutral_comments)]
    labels = ['Positive', 'Negative', 'Neutral']
    
    fig, ax = plt.subplots()
    ax.bar(labels, comment_counts, color=['#76c7c0', '#f76c6c', '#ffcc5c'])
    ax.set_title('Sentiment Distribution')
    ax.set_xlabel('Sentiments')
    ax.set_ylabel('Number of Comments')
    st.pyplot(fig)

    # Display Sentiment Distribution as Pie Chart
    fig, ax = plt.subplots()
    ax.pie(comment_counts, labels=labels, autopct='%1.1f%%', startangle=90, colors=['#8fd175', '#f76c6c', '#ffd700'])
    ax.set_title('Sentiment Distribution (Pie Chart)')
    st.pyplot(fig)

    # Display Sentiment Distribution as Donut Chart
    fig, ax = plt.subplots()
    ax.pie(comment_counts, labels=labels, autopct='%1.1f%%', startangle=90, wedgeprops={'width': 0.4}, colors=['#76c7c0', '#f76c6c', '#ffcc5c'])
    ax.set_title('Sentiment Distribution (Donut Chart)')
    st.pyplot(fig)

    # Display Word Cloud
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(' '.join(relevant_comments))
    st.image(wordcloud.to_array(), use_column_width=True)

    # Display Average Polarity
    avg_polarity = sum(polarity) / len(polarity)
    st.write(f"Average Polarity: {avg_polarity:.2f}")
    if avg_polarity > 0.05:
        st.write("The Video has a Positive Response")
    elif avg_polarity < -0.05:
        st.write("The Video has a Negative Response")
    else:
        st.write("The Video has a Neutral Response")
