import os
from datetime import datetime, timedelta, timezone
from pytube import YouTube
from clip_creator.conf import LOGGER

import isodate
import youtube_transcript_api
from googleapiclient.discovery import build

from clip_creator.conf import API_KEY

YOUTUBE = build('youtube', 'v3', developerKey=API_KEY)




def Download(video_id:str):
    link = f"https://www.youtube.com/watch?v={video_id}"
    youtubeObject = YouTube(link)
    youtubeObject = youtubeObject.streams.get_highest_resolution()
    try:
        youtubeObject.download()
    except:
        LOGGER.info("An error has occurred")
    LOGGER.info("Download is completed successfully")

def search_videos(query, time_range=7):
    """Searches YouTube videos within a specified time range."""
    now = datetime.now(timezone.utc)
    published_after = (now - timedelta(days=time_range)).isoformat().replace('+00:00', 'Z')

    request = YOUTUBE.search().list(
        q=query,
        part='snippet',
        type='video',
        publishedAfter=published_after,
        order='relevance',
        maxResults=50
    )
    response = request.execute()
    return response.get('items', [])


def is_trending(video_id):
    """Checks if a video is trending (a simplified approach)."""
    # Note: The YouTube Data API v3 does not directly provide a "trending" flag.
    # Trending status is dynamic and algorithm-driven. This function uses a proxy
    # by checking if a video has a high view count relative to its age.  This is not definitive.
    try:
        request = YOUTUBE.videos().list(
            part='statistics,snippet',
            id=video_id
        )
        response = request.execute()
        items = response.get('items', [])
        if items:
            video_stats = items[0]['statistics']
            view_count = int(video_stats.get('viewCount', 0))

            # Very basic trending proxy. You'll likely need to refine this based on your needs.
            # Consider using other signals like likeCount, commentCount, and video duration
            # along with viewCount and upload date for a more robust "trending" metric.
            published_at_str = items[0]['snippet']['publishedAt']
            published_at = isodate.parse_datetime(published_at_str)
            age_in_days = (datetime.utcnow() - published_at).days
            if age_in_days > 0: # Avoid division by 0
                views_per_day = view_count / age_in_days
                if views_per_day > 10000:  # Arbitrary threshold. Adjust as needed.
                    return True
            return False
        else:
            return False
    except Exception as e:
        LOGGER.info(f"Error checking trending status: {e}")
        return False



def get_video_info(video_id):
    """Gets transcript, link, and comments for a video."""
    try:
        transcript = get_transcript(video_id)
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        comments = get_comments(video_id)
        return {
            "transcript": transcript,
            "link": video_url,
            "comments": comments
        }
    except Exception as e:
        LOGGER.info(f"Error getting video info: {e}")
        return None

def get_transcript(video_id):
    """Gets the transcript of a YouTube video."""
    try:
        transcript = youtube_transcript_api.YouTubeTranscriptApi.get_transcript(video_id)
        # Format transcript as a string:
        #transcript_text = " ".join([entry['text'] for entry in transcript])
        return transcript
    except youtube_transcript_api.TranscriptsDisabled:
        return "Transcripts are disabled for this video."
    except youtube_transcript_api.NoTranscriptFound:
        return "No transcript found for this video."
    except Exception as e:
        return f"Error getting transcript: {e}"

def join_transcript(transcript):
    """Join the transcript into a single string."""
    return " ".join([entry['text'] for entry in transcript])

def get_comments(video_id, max_comments=50):  # Added max_comments
    """Gets comments for a video."""
    try:
        comments = []
        request = YOUTUBE.commentThreads().list(
            part='snippet',
            videoId=video_id,
            maxResults=max_comments  # Limit the number of comments retrieved
        )
        while request:
            response = request.execute()
            for item in response.get('items', []):
                comment = item['snippet']['topLevelComment']['snippet']
                comments.append({
                    'author': comment.get('authorDisplayName', 'Unknown'),
                    'text': comment.get('textOriginal', '')
                })
            if 'nextPageToken' in response:
                request = YOUTUBE.commentThreads().list_next(request, response)
            else:
                request = None  # No more pages
        return comments
    except Exception as e:
        LOGGER.info(f"Error getting comments: {e}")
        return []


# Example usage:
search_results = search_videos("Python programming tutorial")

for item in search_results:
  video_id = item['id']['videoId']
  if is_trending(video_id):
        video_info = get_video_info(video_id)
        if video_info:
            LOGGER.info(f"Trending Video: {item['snippet']['title']}")
            LOGGER.info(f"Link: {video_info['link']}")
            LOGGER.info("Transcript:", video_info['transcript'][:500] + "...") # Print a snippet
            LOGGER.info("Comments:", video_info['comments'][:5])  #Print a few comments
            LOGGER.info("-" * 20)