# Youtube-Content-Recommendation
Create a machine learning model to recommend YouTube contents using NLP and Sentiment Analysis
Language Used: Python
1. Data Collection and Preprocessing:
   Import Libraries: Necessary libraries for data collection, processing, visualization, and NLP tasks are imported;
    Authenticate with YouTube API: The code authenticates with the YouTube API using an API key;
    Retrieve Channel and Video Data: Channel IDs are specified, and the code retrieves video details, including comments, using the API;
    Data Cleaning: The DataFrame is cleaned by removing rows with empty comments.
  
2. Sentiment Analysis:
   Install Libraries: Required libraries for sentiment analysis are installed (TextBlob, NLTK, pandas);
    Sentiment Analysis using VADER: Sentiment analysis is performed on the video comments using the VADER sentiment analyzer. A new DataFrame is created to store the sentiment percentages for each video.

3. Feature Engineering:
   Get Video Categories: The code fetches video category information using the YouTube API;
    Data Handling: Missing values are handled, data types are converted, and new features like publish day, duration in seconds/minutes, and days since published are added;
    Descriptive Statistics: The code calculates and displays descriptive statistics like maximum and minimum video duration.

4. Exploratory Data Analysis (EDA):
   Visualization: Various plots and charts are created, including:
       Video tag analysis and visualization,
        Bar charts for view counts and video publish day,
        Violin plot for view count by channel title,
        Scatter plots for view count vs. comment count and like count,
        Histogram of video duration,
        Word cloud from video titles.

5. Clustering:
   K-Means Clustering: The code performs K-Means clustering on normalized features to group similar videos;
    Cluster Analysis: It analyzes cluster characteristics, distribution, and feature averages using heatmaps and scatter plots.

6. Video Recommendation:
   Content-Based Recommendation: The code builds a video recommendation function using TF-IDF vectorization and cosine similarity to recommend videos with similar content.
