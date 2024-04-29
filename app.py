import re
import requests
from googletrans import Translator
from nltk import word_tokenize
from nltk.corpus import stopwords
from textblob import TextBlob
import streamlit as st

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
        match = re.search(r"watch\?v=(\S+)", video_url)
        video_id = match.group(1)
        api_key = 'API_KEY'  # Replace with your actual YouTube Data API key
        endpoint = f'https://www.googleapis.com/youtube/v3/videos?id={video_id}&key={api_key}&part=snippet'
        response = requests.get(endpoint)
        response.raise_for_status()
        video_info = response.json()
        title = video_info['items'][0]['snippet']['title']
        description = video_info['items'][0]['snippet']['description']
        return video_id, title, description, api_key
    except Exception as e:
        st.error(f"An error occurred while analyzing video info: {e}")
        return None, None, None, None

# Streamlit UI
st.title("YouTube Video Analyzer")

# Input field for YouTube video URL
video_url = st.text_input("Enter YouTube video URL:")

# Button to trigger analysis
if st.button("Analyze"):
    if video_url:
        # Analyze video information
        video_id, title, description, api_key = get_video_info(video_url)
        if title and description:
            st.write(f"**Title:** {title}")
            st.write(f"**Description:** {description}")
            
            # Translate the title
            translated_title_mr, translated_title_hi, translated_title_en = translate_title(title)
            if translated_title_mr and translated_title_hi and translated_title_en:
                st.write("**Translated Titles:**")
                st.write(f"Marathi: {translated_title_mr}")
                st.write(f"Hindi: {translated_title_hi}")
                st.write(f"English: {translated_title_en}")
            else:
                st.error("Failed to translate title.")

            # Get comments for the video
            comments = get_video_comments(video_id, api_key)
            if comments:
                st.write("**Sentiment Analysis Results:**")
                sentiment_analysis = analyze_sentiment(comments)
                st.write(f"Positive: {sentiment_analysis['positive']:.2f}%")
                st.write(f"Negative: {sentiment_analysis['negative']:.2f}%")
                st.write(f"Neutral: {sentiment_analysis['neutral']:.2f}%")
            else:
                st.warning("No comments available for sentiment analysis.")
        else:
            st.error("Failed to retrieve video information.")
