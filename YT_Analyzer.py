import re
import requests
from googletrans import Translator
from nltk import word_tokenize
from nltk.corpus import stopwords
from textblob import TextBlob
import streamlit as st
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Set up Streamlit app
st.set_page_config(page_title="YouTube Video Analyzer", layout="centered")

# Custom styling for the app
st.markdown(
    """
    <style>
    .title {
        font-size: 35px;
        font-weight: bold;
        color: #2C3E50;
    }
    .subheading {
        font-size: 22px;
        color: #34495E;
    }
    .box {
        border: 1px solid #D5DBDB;
        border-radius: 5px;
        padding: 10px;
        background-color: #F8F9F9;
    }
    </style>
    """, unsafe_allow_html=True
)

# Function to translate the title
def translate_title(video_title):
    try:
        translator = Translator()
        translated_title_mr = translator.translate(video_title, dest="mr").text
        translated_title_hi = translator.translate(video_title, dest="hi").text
        translated_title_en = translator.translate(video_title, dest="en").text
        return translated_title_mr, translated_title_hi, translated_title_en
    except Exception as e:
        st.error(f"An error occurred while translating title: {e}")
        return None, None, None

# Function to preprocess text
def preprocess_text(text):
    tokens = word_tokenize(text.lower())
    stop_words = set(stopwords.words('english'))
    filtered_tokens = [token for token in tokens if token not in stop_words and token.isalnum()]
    return ' '.join(filtered_tokens)

# Function to get comments for a YouTube video
def get_video_comments(video_id, api_key):
    try:
        max_results = 100
        comments = []

        endpoint = f'https://www.googleapis.com/youtube/v3/commentThreads?part=snippet&videoId={video_id}&key={api_key}&maxResults={max_results}'
        response = requests.get(endpoint)
        response.raise_for_status()
        comments_data = response.json()

        for item in comments_data.get('items', []):
            comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
            comments.append(comment)

        return comments

    except requests.exceptions.HTTPError as e:
        st.error(f"An HTTP error occurred while retrieving comments: {e}")
        return []
    except Exception as e:
        st.error(f"An error occurred while retrieving comments: {e}")
        return []

# Function to analyze sentiment
def analyze_sentiment(comments):
    positive_count = 0
    negative_count = 0
    neutral_count = 0

    for comment in comments:
        blob = TextBlob(comment)
        polarity = blob.sentiment.polarity
        if polarity > 0:
            positive_count += 1
        elif polarity < 0:
            negative_count += 1
        else:
            neutral_count += 1

    total_comments = len(comments)

    if total_comments == 0:
        return {
            'positive': 0,
            'negative': 0,
            'neutral': 0
        }

    positive_percentage = (positive_count / total_comments) * 100
    negative_percentage = (negative_count / total_comments) * 100
    neutral_percentage = (neutral_count / total_comments) * 100

    return {
        'positive': positive_percentage,
        'negative': negative_percentage,
        'neutral': neutral_percentage
    }

# Function to get video info
def get_video_info(video_url):
    try:
        # Extract the video ID from the URL
        match = re.search(r"watch\?v=(\S+)", video_url)
        if not match:
            raise ValueError("Invalid YouTube URL provided.")
        video_id = match.group(1)

        # Define your API key and endpoint
        api_key = os.getenv('YOUTUBE_API_KEY')  # API Key from environment variable
        endpoint = f'https://www.googleapis.com/youtube/v3/videos?id={video_id}&key={api_key}&part=snippet'

        response = requests.get(endpoint, verify=False)
        response.raise_for_status()  # Raises an HTTPError for bad responses

        video_info = response.json()
        title = video_info['items'][0]['snippet']['title']
        description = video_info['items'][0]['snippet']['description']
        return video_id, title, description, api_key
    except Exception as e:
        st.error(f"An error occurred while analyzing video info: {e}")
        return None, None, None, None

# Streamlit UI
st.markdown('<h1 class="title">YouTube Video Analyzer</h1>', unsafe_allow_html=True)

# Input field for YouTube video URL
video_url = st.text_input("Enter YouTube video URL:")

# Button to trigger analysis
if st.button("Analyze"):
    if video_url:
        # Add a progress spinner
        with st.spinner("Analyzing video..."):
            # Analyze video information
            video_id, title, description, api_key = get_video_info(video_url)
            if title and description:
                st.markdown(f'<h2 class="subheading">Video Information</h2>', unsafe_allow_html=True)
                st.write(f"**Title:** {title}")
                st.write(f"**Description:** {description}")
                
                # Translate the title
                st.markdown(f'<h2 class="subheading">Translated Titles</h2>', unsafe_allow_html=True)
                translated_title_mr, translated_title_hi, translated_title_en = translate_title(title)
                if translated_title_mr and translated_title_hi and translated_title_en:
                    st.write(f"**Marathi:** {translated_title_mr}")
                    st.write(f"**Hindi:** {translated_title_hi}")
                    st.write(f"**English:** {translated_title_en}")
                else:
                    st.error("Failed to translate title.")

                # Get comments for the video
                comments = get_video_comments(video_id, api_key)
                if comments:
                    st.markdown(f'<h2 class="subheading">Sentiment Analysis</h2>', unsafe_allow_html=True)
                    sentiment_analysis = analyze_sentiment(comments)
                    
                    # Display sentiment results with Streamlit's metric component
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Positive", f"{sentiment_analysis['positive']:.2f}%")
                    col2.metric("Negative", f"{sentiment_analysis['negative']:.2f}%")
                    col3.metric("Neutral", f"{sentiment_analysis['neutral']:.2f}%")
                    
                    # Optionally, display all comments
                    with st.expander("Show comments"):
                        for comment in comments:
                            st.write(comment)
                else:
                    st.warning("No comments available for sentiment analysis.")
            else:
                st.error("Failed to retrieve video information.")
    else:
        st.warning("Please enter a valid YouTube video URL.")
