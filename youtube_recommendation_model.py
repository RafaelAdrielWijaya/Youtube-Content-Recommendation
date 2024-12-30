# -*- coding: utf-8 -*-
"""YouTube_Recommendation_Model.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1TEXBE1pT7cdy9a2TKF0XeER7kmIxkoY0

# 1. Data Collection and Preprocessing

## 1.1 Import necessary libraries
"""

from googleapiclient.discovery import build
from dateutil import parser
import pandas as pd
from IPython.display import JSON
import json

# Data viz packages
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# NLP
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
nltk.download('stopwords')
nltk.download('punkt')
from wordcloud import WordCloud

"""## 1.2 Authenticate with YouTube API"""

#api_key = 'AIzaSyCXOURGqUK5KJ1IU56TAdiza8wGKNPOyNY'  # Replace with your API key

"""## 1.3 Retrieve channel and video data"""

from googleapiclient.discovery import build



# Initialize the YouTube API client (1.2)
youtube = build('youtube', 'v3', developerKey=api_key)

# Search for channel by name (1.3)
search_request = youtube.search().list(
    part="snippet",
    q="The Verge",
    type="channel"
)

# Execute the request
search_response = search_request.execute()

# Extract Channel ID
if search_response['items']:
    channel_id = search_response['items'][0]['snippet']['channelId']
    print(f"Channel ID: {channel_id}")
else:
    print("Channel not found.")

channel_ids = [' UCvJJ_dzjViJCoLf5uKUTwoA',
               'UC16niRr50-MSBwiO3YDb3RA',
               'UCddiUEpeqJcYeBxX1IVBKvQ',

               # more channels here
              ]

api_service_name = "youtube"
api_version = "v3"

# Get credentials and create an API client
youtube = build(
    api_service_name, api_version, developerKey=api_key)

# request = youtube.channels().list(
#         part="snippet,contentDetails,statistics",
#         id=','.join(channel_ids)
#     )
# response = request.execute()
# JSON(response)

import pandas as pd
import datetime
def get_uploads_playlist_id(youtube, channel_id):
    """
    Retrieve the 'uploads' playlist ID for a given channel.
    """
    request = youtube.channels().list(
        part="contentDetails",
        id=channel_id
    )
    response = request.execute()

    # Get the uploads playlist ID
    playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    return playlist_id

def get_recent_video_ids(youtube, playlist_id, months=3):
    """
    Get video IDs published within the last `months` months from a playlist.
    """
    recent_video_ids = []
    now = datetime.datetime.now()
    cutoff_date = now - datetime.timedelta(days=months * 30)  # Set cutoff to 3 months ago

    # Fetch videos from the playlist
    request = youtube.playlistItems().list(
        part="snippet,contentDetails",
        playlistId=playlist_id,
        maxResults=50
    )
    response = request.execute()

    while response:
        for item in response['items']:
            # Check if the video is within the cutoff date
            published_date = datetime.datetime.strptime(item['contentDetails']['videoPublishedAt'], '%Y-%m-%dT%H:%M:%SZ')
            if published_date >= cutoff_date:
                recent_video_ids.append(item['contentDetails']['videoId'])

        # Move to the next page if there are more results
        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break
        response = youtube.playlistItems().list(
            part="contentDetails",
            playlistId=playlist_id,
            maxResults=50,
            pageToken=next_page_token
        ).execute()

    return recent_video_ids


def get_video_details(youtube, video_ids):
    """
    Get video details for recent videos.
    """
    all_video_info = []

    for i in range(0, len(video_ids), 50):
        request = youtube.videos().list(
            part="snippet,contentDetails,statistics",
            id=','.join(video_ids[i:i+50])
        )
        response = request.execute()

        for video in response['items']:
            stats_to_keep = {
                'snippet': ['channelTitle', 'title', 'description', 'tags', 'publishedAt', 'categoryId'],
                'statistics': ['viewCount', 'likeCount', 'favouriteCount', 'commentCount'],
                'contentDetails': ['duration', 'definition', 'caption']
            }
            video_info = {'video_id': video['id']}

            for k, v_list in stats_to_keep.items():
                for v in v_list:
                    video_info[v] = video[k].get(v, None)

            if 'tags' not in video_info or not isinstance(video_info['tags'], list):
                video_info['tags'] = []

            all_video_info.append(video_info)

    return pd.DataFrame(all_video_info)

def get_comments_as_list(youtube, video_ids, max_comments=100):
    """
    Get comments for each video and store as a list in one row per video.
    """
    video_comments = []

    for video_id in video_ids:
        comments_list = []
        comments_fetched = 0
        try:
            request = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=min(max_comments, 100),
                textFormat="plainText"
            )
            response = request.execute()
            comments = response.get("items", [])

            while comments and comments_fetched < max_comments:
                for item in comments:
                    if comments_fetched >= max_comments:
                        break
                    comment_text = item['snippet']['topLevelComment']['snippet']['textDisplay']
                    comments_list.append(comment_text)
                    comments_fetched += 1

                # Check for more comments if limit not yet reached
                if 'nextPageToken' in response and comments_fetched < max_comments:
                    request = youtube.commentThreads().list(
                        part="snippet",
                        videoId=video_id,
                        pageToken=response['nextPageToken'],
                        maxResults=min(max_comments - comments_fetched, 100),
                        textFormat="plainText"
                    )
                    response = request.execute()
                    comments = response.get("items", [])
                else:
                    break

        except Exception as e:
            print(f"Could not retrieve comments for video ID {video_id}: {e}")

        # Add a dictionary with video_id and comments list to video_comments
        video_comments.append({'video_id': video_id, 'comments': comments_list})

    # Convert list of dictionaries to DataFrame
    return pd.DataFrame(video_comments)

# Example usage
# List of channel IDs
channel_ids = [
    'UCvJJ_dzjViJCoLf5uKUTwoA',
    'UC16niRr50-MSBwiO3YDb3RA',
    'UCddiUEpeqJcYeBxX1IVBKvQ',
    # Add more channel IDs here
]

# Initialize an empty list to store all recent video IDs
all_recent_video_ids = []

# Loop through each channel ID to fetch recent videos from the last 3 months
for channel_id in channel_ids:
    try:
        # Get the uploads playlist ID for the channel
        playlist_id = get_uploads_playlist_id(youtube, channel_id)
        # Get recent video IDs from the uploads playlist
        recent_video_ids = get_recent_video_ids(youtube, playlist_id, months=3)
        all_recent_video_ids.extend(recent_video_ids)
    except Exception as e:
        print(f"Could not retrieve videos for channel ID {channel_id}: {e}")

# Now, get video details for all recent videos
recent_videos_df = get_video_details(youtube, all_recent_video_ids)

# Get up to 100 comments for each recent video, stored as a list
comments_df = get_comments_as_list(youtube, all_recent_video_ids, max_comments=100)

# Merge comments with video details on video_id
merged_df = pd.merge(recent_videos_df, comments_df, on='video_id', how='left')

print(merged_df)

merged_df

"""## 1.4 Data Cleaning

"""

# Filter rows where the 'comments' column is empty or NaN
empty_comments_df = merged_df[(merged_df['comments'].isnull()) | (merged_df['comments'].apply(lambda x: len(x) == 0))]

# Display the 'channelTitle' and 'video_id' for videos with empty comments
print(empty_comments_df[['channelTitle', 'video_id']])

# Drop rows with empty or NaN comments
merged_df = merged_df[merged_df['comments'].apply(lambda x: isinstance(x, list) and len(x) > 0)]

# Reset the index after dropping rows
merged_df.reset_index(drop=True, inplace=True)

# Display the updated DataFrame
print(merged_df)

"""# 2. Sentiment Analysis

## 2.1 Install necessary libraries
"""

# Commented out IPython magic to ensure Python compatibility.
# %pip install textblob nltk pandas

"""## 2.2 Sentiment Analysis using VADER and create sentiment dataframe"""

import nltk
nltk.download('vader_lexicon')
import pandas as pd
from textblob import TextBlob
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# Initialize the VADER sentiment analyzer
sid = SentimentIntensityAnalyzer()

def analyze_sentiment(comments):
    """
    Analyze sentiment of a list of comments and categorize them.
    Returns counts of negative, neutral, and positive comments.
    """
    sentiment_counts = {'negative': 0, 'neutral': 0, 'positive': 0}

    for comment in comments:
        # Using VADER sentiment analysis
        sentiment_score = sid.polarity_scores(comment)

        if sentiment_score['compound'] >= 0.05:
            sentiment_counts['positive'] += 1
        elif sentiment_score['compound'] <= -0.05:
            sentiment_counts['negative'] += 1
        else:
            sentiment_counts['neutral'] += 1

    return sentiment_counts

# DataFrame to store sentiment results
sentiment_results = []

# Loop through each video and perform sentiment analysis on comments
for index, row in merged_df.iterrows():
    video_id = row['video_id']
    comments = row['comments']

    sentiment_counts = analyze_sentiment(comments)
    total_comments = sum(sentiment_counts.values())

    # Calculate percentages
    sentiment_percentages = {
        'video_id': video_id,
        'negative_percentage': (sentiment_counts['negative'] / total_comments) * 100 if total_comments > 0 else 0,
        'neutral_percentage': (sentiment_counts['neutral'] / total_comments) * 100 if total_comments > 0 else 0,
        'positive_percentage': (sentiment_counts['positive'] / total_comments) * 100 if total_comments > 0 else 0,
    }

    sentiment_results.append(sentiment_percentages)

# Create a new DataFrame for sentiment analysis results
sentiment_df = pd.DataFrame(sentiment_results)

# Display the sentiment DataFrame
print(sentiment_df)

"""# 3. Feature Engineering

## 3.1 Display sentiment DataFrame
"""

sentiment_df

"""## 3.2 Get unique category IDs"""

merged_df['categoryId'].unique()

"""## 3.3 Get video categories using the YouTube API"""

def get_video_categories(youtube):
    """
    Get the video categories from YouTube API.

    Params:
    ------
    youtube: build object of YouTube API

    Returns:
    ------
    A dictionary mapping category IDs to category names.
    """
    request = youtube.videoCategories().list(
        part="snippet",
        regionCode="US"  # Region code can be changed as needed
    )
    response = request.execute()

    categories = {}
    for item in response['items']:
        category_id = item['id']
        category_name = item['snippet']['title']
        categories[category_id] = category_name

    return categories

categories = get_video_categories(youtube)
categories

"""## 3.4 Request video details (redundant)"""

request = youtube.videos().list(
    part="snippet,contentDetails,statistics",
    id=recent_video_ids[0:5]
)
response = request.execute()
response

"""## 3.5 Check for missing values in the DataFrame:"""

merged_df.isnull().any()

"""## 3.6 Convert count columns to numeric"""

numeric_cols = ['viewCount', 'likeCount', 'favouriteCount', 'commentCount']
merged_df[numeric_cols] = merged_df[numeric_cols].apply(pd.to_numeric, errors = 'coerce', axis = 1)
merged_df[numeric_cols].dtypes
merged_df

"""## 3.7 Extract publish day of the week"""

merged_df['publishedAt'] = pd.to_datetime(merged_df['publishedAt'].astype(str), errors='coerce')
merged_df['publishedAt'] = merged_df['publishedAt'].dt.tz_localize(None)
merged_df['pushblishDayName'] = merged_df['publishedAt'].apply(lambda x: x.strftime("%A"))

"""## 3.8 Parse video duration from ISO 8601 format and convert to seconds using isodate library"""

# Commented out IPython magic to ensure Python compatibility.
# %pip install isodate
import isodate

# Parse the duration and convert it to timedelta
merged_df['durationSecs'] = merged_df['duration'].apply(lambda x: isodate.parse_duration(x))

# Convert timedelta to total seconds
merged_df['durationSecs'] = merged_df['durationSecs'].apply(lambda x: x.total_seconds())

"""## 3.9 Calculate a column named 'durationMinutes' and display it along with duration in seconds (for verification)"""

merged_df['durationMinutes'] = merged_df['durationSecs'] / 60

# Optionally, round to two decimal places for better readability
merged_df['durationMinutes'] = merged_df['durationMinutes'].round(2)

merged_df[['durationSecs', 'duration']]
merged_df[['durationMinutes', 'duration']]

"""## 3.10 Calculate and add 'days_since_published' column"""

# Ensure 'publishedAt' is in the correct datetime format
merged_df['publishedAt'] = pd.to_datetime(merged_df['publishedAt'], utc=True)

# Calculate 'days_since_published'
merged_df['days_since_published'] = (pd.Timestamp.now(tz='UTC') - merged_df['publishedAt']).dt.days

# Create a DataFrame with 'days_since_published' column
days_since_published_df = merged_df[['publishedAt', 'days_since_published']]

days_since_published_df

"""## 3.11 Calculate and print maximum and minimum video duration both in seconds and minutes"""

max_duration = merged_df['durationSecs'].max()
print(f"Maximum Duration (seconds): {max_duration}")

# Minimum duration in seconds
min_duration = merged_df['durationSecs'].min()
print(f"Minimum Duration (seconds): {min_duration}")

max_duration = merged_df['durationMinutes'].max()


# Minimum duration in seconds
min_duration = merged_df['durationMinutes'].min()
print(max_duration)
print(min_duration)

"""## 3.12 Display merged DataFrame"""

merged_df

"""# 4. Exploratoty Data Analysis (EDA)

## 4.1 Video Tag Analysis and Visualization
"""

from collections import Counter
import matplotlib.pyplot as plt
import pandas as pd

# Step 1: Define words to exclude
exclude_words = ["news", "bbc", "cnbc", "world", "america", "usa", " verge"]

# Step 2: Flatten the tags into a single list, excluding tags containing any of the exclude words
all_tags = [
    tag
    for sublist in merged_df['tags']
    if isinstance(sublist, list)
    for tag in sublist
    if not any(exclude_word in tag.lower() for exclude_word in exclude_words)
]

# Step 3: Count occurrences of each tag
tag_counts = Counter(all_tags)

# Step 4: Create a DataFrame for visualization
tag_counts_df = pd.DataFrame(tag_counts.items(), columns=['Tag', 'Count'])

# Step 5: Sort and visualize the top N tags
top_n = 20  # Change this value to display more or fewer tags
top_tags_df = tag_counts_df.sort_values(by='Count', ascending=False).head(top_n)

# Plotting
plt.figure(figsize=(12, 6))
top_tags_df.plot(kind='bar', x='Tag', y='Count', color='skyblue', legend=False)
plt.title(f'Top {top_n} Video Tags')
plt.xlabel('Tag')
plt.ylabel('Count')
plt.xticks(rotation=45)
plt.tight_layout()  # Adjust layout to prevent clipping
plt.show()

"""## 4.2 Create bar chart of view count for top and bottom 9 videos"""

ax = sns.barplot(x = 'title', y = 'viewCount', data = merged_df.sort_values('viewCount', ascending=False)[0:9])
plot = ax.set_xticklabels(ax.get_xticklabels(), rotation=90)
ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos:'{:,.0f}'.format(x/1000) + 'K'))

ax = sns.barplot(x = 'title', y = 'viewCount', data = merged_df.sort_values('viewCount', ascending=True)[0:9])
plot = ax.set_xticklabels(ax.get_xticklabels(), rotation=90)
ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos:'{:,.0f}'.format(x)))

"""## 4.3 Create violin plot of view count by channel title"""

sns.violinplot(x='channelTitle', y='viewCount', data=merged_df)

# Optional: Show the plot
plt.xticks(rotation=45)  # Rotate x labels for better visibility
plt.show()

"""## 4.4 Create scatter plots of view count vs. comment count and like count"""

fig, ax = plt.subplots(1,2)
sns.scatterplot(data = merged_df, x = 'commentCount', y = 'viewCount', ax = ax[0])
sns.scatterplot(data = merged_df, x = 'likeCount', y = 'viewCount', ax = ax[1])

"""## 4.5 Count videos longer than 80 minutes"""

# Count the number of videos with duration greater than 80 minutes
count_videos_longer_than_80 = (merged_df['durationMinutes'] > 80).sum()

print(f"Number of videos longer than 80 minutes: {count_videos_longer_than_80}")

"""## 4.6 Create histogram of video duration"""

sns.histplot(data = merged_df, x = 'durationMinutes', bins=200)
plt.xlim(0, 80)

"""## 4.7 Create Word cloud from video titles (excluding common words)"""

from wordcloud import WordCloud
from nltk.corpus import stopwords
import matplotlib.pyplot as plt

# Define stop words and additional exclusions
stop_words = set(stopwords.words('english')).union({"CNBC"})

# Additional exclusions for words containing "BBC" or "News"
def exclude_specific_words(word):
    return "bbc" not in word.lower() and "news" not in word.lower() and "U" not in word and "Say" not in word

# Apply filtering to remove stop words and specific words
merged_df['title_no_stopwords'] = merged_df['title'].apply(
    lambda x: [item for item in str(x).split() if item not in stop_words and exclude_specific_words(item)]
)

# Combine all words into a single string
all_words = list([a for b in merged_df['title_no_stopwords'].tolist() for a in b])
all_words_str = ' '.join(all_words)

# Function to plot the word cloud
def plot_cloud(wordcloud):
    plt.figure(figsize=(30, 20))
    plt.imshow(wordcloud)
    plt.axis("off");

# Generate and display the word cloud
wordcloud = WordCloud(
    width=2000, height=1000, random_state=1, background_color='black',
    colormap='viridis', collocations=False
).generate(all_words_str)
plot_cloud(wordcloud)

"""## 4.8 Create and display bar chart of video publish day"""

# Create a DataFrame of value counts for the 'pushblishDayName' column
day_df = pd.DataFrame(merged_df['pushblishDayName'].value_counts())

# Reindex to include all weekdays
weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
day_df = day_df.reindex(weekdays)

# Reset the index and rename columns
day_df.reset_index(inplace=True)
day_df.columns = ['Day', 'Count']  # Rename the columns for clarity

# Plotting the bar chart
ax = day_df.plot.bar(x='Day', y='Count', rot=0)

"""## 4.9 Define category mapping dictionary"""

# Define the category mapping dictionary
category_mapping = {
    '1': 'Film & Animation',
    '2': 'Autos & Vehicles',
    '10': 'Music',
    '15': 'Pets & Animals',
    '17': 'Sports',
    '18': 'Short Movies',
    '19': 'Travel & Events',
    '20': 'Gaming',
    '21': 'Videoblogging',
    '22': 'People & Blogs',
    '23': 'Comedy',
    '24': 'Entertainment',
    '25': 'News & Politics',
    '26': 'Howto & Style',
    '27': 'Education',
    '28': 'Science & Technology',
    '29': 'Nonprofits & Activism',
    '30': 'Movies',
    '31': 'Anime/Animation',
    '32': 'Action/Adventure',
    '33': 'Classics',
    '34': 'Comedy',
    '35': 'Documentary',
    '36': 'Drama',
    '37': 'Family',
    '38': 'Foreign',
    '39': 'Horror',
    '40': 'Sci-Fi/Fantasy',
    '41': 'Thriller',
    '42': 'Shorts',
    '43': 'Shows',
}

"""## 4.10 Create new DataFrame with selected features"""

# Create the new DataFrame with the desired features
new_merged_df = pd.DataFrame({
    'category': merged_df['categoryId'].map(category_mapping),  # Assuming you have a mapping for categoryId to category names
    'likeCount': merged_df['likeCount'],
    'commentCount': merged_df['commentCount'],
    'duration_minutes': merged_df['durationMinutes'],  # Assuming this is in minutes
    'days_since_published': merged_df['days_since_published'],
    'title_length': merged_df['title'].apply(len),
    'views': merged_df['viewCount']  # Assuming this is the views count
})

# Display the new DataFrame
new_merged_df.head()

"""## 4.11 Merge the sentiment data into the DataFrame"""

# Assuming `sentiment_df` and `merged_df` are already loaded as pandas DataFrames
# Ensure both DataFrames have a common column for merging, e.g., `video_id`

# Merge sentiment data into the new DataFrame
new_merged_df = pd.DataFrame({
    'video_id': merged_df['video_id'],  # Include video_id for merging
    'category': merged_df['categoryId'].map(category_mapping),  # Assuming you have a mapping for categoryId to category names
    'likeCount': merged_df['likeCount'],
    'commentCount': merged_df['commentCount'],
    'duration_minutes': merged_df['durationMinutes'],  # Assuming this is in minutes
    'days_since_published': merged_df['days_since_published'],
    'title_length': merged_df['title'].apply(len),
    'views': merged_df['viewCount']  # Assuming this is the views count
})

# Merge with sentiment_df based on video_id
new_merged_df = new_merged_df.merge(sentiment_df, on='video_id', how='left')

# Display the updated DataFrame
new_merged_df.head()

"""## 4.12 Handle missing values in likeCount and commentCount"""

new_merged_df['likeCount'] = merged_df['likeCount'].fillna(0)  # Fill missing likes with 0
new_merged_df['commentCount'] = merged_df['commentCount'].fillna(0)  # Check for NaN or missing values in the DataFrame
print(new_merged_df.isna().sum())

"""## 4.13 Add categoryId to the new DataFrame"""

new_merged_df['categoryId']=merged_df['categoryId']

new_merged_df['categoryId']

"""## 4.14 Model Building and Evaluation"""

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score

# Features and target (now includes sentiment parameters)
X = new_merged_df[
    [
        'categoryId',
        'likeCount',
        'duration_minutes',
        'days_since_published',
        'title_length',
        'negative_percentage',
        'neutral_percentage',
        'positive_percentage'
    ]
]
y = new_merged_df['views']

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Model
model = RandomForestRegressor(n_estimators=200, random_state=42)
model.fit(X_train, y_train)

# Predictions
y_pred = model.predict(X_test)

# Evaluation
mse = mean_squared_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print(f"Mean Squared Error: {mse}")
print(f"R-squared: {r2}")

"""## 4.15 Time Series Analysis and Moving Average for 90 days"""

merged_df['category'] = merged_df['categoryId'].astype(str).map(category_mapping)

import pandas as pd
import matplotlib.pyplot as plt

# Assuming you have your `merged_df` DataFrame already loaded

# Step 1: Convert 'publishedAt' to datetime and handle NaN values
merged_df['publishedAt_dt'] = pd.to_datetime(merged_df['publishedAt'])
merged_df = merged_df.sort_values(by='publishedAt_dt')  # Sort by datetime

# Optional: Extract just the date (ignoring time and timezone)
merged_df['publishDate'] = merged_df['publishedAt_dt'].dt.date

# Fill NaN values in the counts with 0
merged_df['likeCount'] = merged_df['likeCount'].fillna(0)
merged_df['commentCount'] = merged_df['commentCount'].fillna(0)
merged_df['viewCount'] = merged_df['viewCount'].fillna(0)

# Step 2: Plot raw data over time
plt.figure(figsize=(10, 6))

plt.plot(merged_df['publishedAt_dt'], merged_df['viewCount'], label='Views', color='blue')
plt.plot(merged_df['publishedAt_dt'], merged_df['likeCount'], label='Likes', color='green')
plt.plot(merged_df['publishedAt_dt'], merged_df['commentCount'], label='Comments', color='red')

plt.title('Views, Likes, and Comments Over Time')
plt.xlabel('Published Date')
plt.ylabel('Counts')
plt.legend()
plt.grid(True)
plt.show()

# Step 3: Set 'publishedAt_dt' as the index for time-based rolling averages
merged_df.set_index('publishedAt_dt', inplace=True)

# Step 4: Calculate Moving Averages (90-day window)
merged_df['views_MA'] = merged_df['viewCount'].rolling('90D').mean()
merged_df['likes_MA'] = merged_df['likeCount'].rolling('90D').mean()
merged_df['comments_MA'] = merged_df['commentCount'].rolling('90D').mean()

# Step 5: Plot Moving Averages
plt.figure(figsize=(10, 6))

plt.plot(merged_df.index, merged_df['views_MA'], label='Views (90D MA)', color='blue')
plt.plot(merged_df.index, merged_df['likes_MA'], label='Likes (90D MA)', color='green')
plt.plot(merged_df.index, merged_df['comments_MA'], label='Comments (90D MA)', color='red')

plt.title('90-Day Moving Averages for Views, Likes, and Comments')
plt.xlabel('Published Date')
plt.ylabel('Moving Averages')
plt.legend()
plt.grid(True)
plt.show()

# Step 6: Optional - Reset the index if you need the original structure
merged_df.reset_index(inplace=True)

# Step 7: Category-Level Trend Analysis (Optional)
category_trend = merged_df.groupby(['category', pd.Grouper(key='publishedAt_dt', freq='M')])[
    ['viewCount', 'likeCount', 'commentCount']
].mean()

# Plot Category Trends for Views
plt.figure(figsize=(10, 6))
for category, data in category_trend.groupby(level=0):
    plt.plot(
        data.index.get_level_values(1),  # Extract date index
        data['viewCount'],
        label=f'{category}'
    )

plt.title('Category-Level Views Trend Over Time')
plt.xlabel('Date')
plt.ylabel('Average Views')
plt.legend(title='Category')
plt.grid(True)
plt.show()

"""# 5. Clustering Process

## 5.1 Clustering using K-Means
"""

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# Assuming merged_df is already defined and contains the necessary features

# Step 1: Prepare the data
# Select relevant features for clustering
features = merged_df[['likeCount', 'commentCount', 'viewCount', 'durationMinutes']]

# Step 2: Feature Engineering
# Add additional features
features['likes_to_views_ratio'] = features['likeCount'] / features['viewCount']
features['comments_to_views_ratio'] = features['commentCount'] / features['viewCount']

# Step 3: Handle NaN values (if any)
features.fillna(0, inplace=True)

# Step 4: Normalize the features
scaler = StandardScaler()
normalized_features = scaler.fit_transform(features)

# Step 5: K-Means Clustering
k = 4  # Number of clusters
kmeans = KMeans(n_clusters=k, random_state=42)
clusters = kmeans.fit_predict(normalized_features)

# Add the cluster labels to the original DataFrame
merged_df['cluster'] = clusters

# Step 6: Add the calculated features back to the original DataFrame
merged_df['likes_to_views_ratio'] = features['likes_to_views_ratio']
merged_df['comments_to_views_ratio'] = features['comments_to_views_ratio']

# Step 7: Analyze Clusters
# Group by cluster and calculate mean values to understand characteristics of each cluster
numeric_cols = ['likeCount', 'commentCount', 'viewCount', 'durationMinutes', 'likes_to_views_ratio', 'comments_to_views_ratio']
cluster_analysis = merged_df.groupby('cluster')[numeric_cols].mean()

# Get recommended video categories based on clusters
for cluster in range(k):
    print(f"\nCluster {cluster}:")
    # Replace 'tags' with 'categoryId' or a mapped 'category' if you have a mapping
    print(merged_df[merged_df['cluster'] == cluster]['category'].value_counts().head(5))  # Or use 'category' if mapped

#Videos with high views but relatively low likes and comments (e.g., viral but not engaging).
#Videos with balanced views, likes, and comments (e.g., consistently engaging content).
#Videos with low views but high engagement ratios (e.g., niche audience).

merged_df[merged_df['cluster'] == 1]['category'].value_counts().head(5)

"""## 5.2 Cluster distribution by likes and views"""

import matplotlib.pyplot as plt

# Scatter plot with two features
plt.figure(figsize=(10, 6))

# Use 'likeCount' and 'viewCount' as axes, color points by cluster
for cluster in merged_df['cluster'].unique():
    cluster_data = merged_df[merged_df['cluster'] == cluster]
    plt.scatter(cluster_data['likeCount'], cluster_data['viewCount'], label=f'Cluster {cluster}', alpha=0.6)

plt.title('Cluster Distribution by Likes and Views')
plt.xlabel('Likes')
plt.ylabel('Views')
plt.legend()
plt.grid(True)
plt.show()

"""## 5.3 Cluster distribution using PCA"""

from sklearn.decomposition import PCA
import matplotlib.pyplot as plt

# Perform PCA to reduce to 2D
pca = PCA(n_components=2)
pca_result = pca.fit_transform(normalized_features)

# Scatter plot of PCA results
plt.figure(figsize=(10, 6))
for cluster in range(k):
    cluster_data = pca_result[clusters == cluster]
    plt.scatter(cluster_data[:, 0], cluster_data[:, 1], label=f'Cluster {cluster}', alpha=0.6)

plt.title('Cluster Distribution using PCA')
plt.xlabel('PCA Component 1')
plt.ylabel('PCA Component 2')
plt.legend()
plt.grid(True)
plt.show()

"""## 5.4 Cluster Feature Average using Heatmap"""

import seaborn as sns

# Heatmap of cluster averages
plt.figure(figsize=(12, 8))
sns.heatmap(cluster_analysis, annot=True, fmt=".2f", cmap="coolwarm", linewidths=0.5)
plt.title('Cluster Feature Averages')
plt.ylabel('Cluster')
plt.xlabel('Features')
plt.show()

"""## 5.5 Features on each cluster"""

cluster_analysis

"""# 6. Video Recommendation Function"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
# Ensure tags, title, and category are strings before concatenation
merged_df['tags'] = merged_df['tags'].apply(lambda x: ' '.join(x) if isinstance(x, list) else str(x))
merged_df['title'] = merged_df['title'].fillna('').astype(str)
merged_df['categoryId'] = merged_df['category'].fillna('').astype(str)

# Combine text-based features for analysis
merged_df['content_features'] = merged_df['tags'] + ' ' + merged_df['title'] + ' ' + merged_df['categoryId']

# Vectorize text data using TF-IDF
vectorizer = TfidfVectorizer(stop_words='english')
tfidf_matrix = vectorizer.fit_transform(merged_df['content_features'])

# Compute cosine similarity matrix
cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)

cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)

# Function to recommend similar videos based on a given video index
def recommend_videos(video_index, num_recommendations=5):
    # Get similarity scores for the video
    sim_scores = list(enumerate(cosine_sim[video_index]))
    # Sort videos by similarity score
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    # Select the top recommendations (excluding the video itself)
    sim_scores = sim_scores[1:num_recommendations + 1]
    # Get the indices of the recommended videos
    video_indices = [i[0] for i in sim_scores]
    return merged_df.iloc[video_indices][['title', 'categoryId', 'viewCount', 'likeCount']]

# Example: Recommend videos similar to the first video in the dataset
recommendations = recommend_videos(video_index=0, num_recommendations=5)
recommendations