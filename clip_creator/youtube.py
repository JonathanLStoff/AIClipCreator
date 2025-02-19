import os
from datetime import UTC, datetime, timedelta

# import subprocess
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
import isodate
import youtube_transcript_api
from googleapiclient.discovery import build
from yt_dlp import YoutubeDL

from clip_creator.conf import API_KEY, LOGGER

YOUTUBE = build("youtube", "v3", developerKey=API_KEY)


def Download(video_id: str, path: str = "videos", filename: str | None = None):
    link = f"https://www.youtube.com/watch?v={video_id}"
    with YoutubeDL() as ydl:
        ydl.download([link])
    for file in os.listdir("./"):
        if video_id in file:
            os.rename(file, f"{path}/{filename}.{file.split('.')[-1]}")

    LOGGER.info("Download is completed successfully")


def subscriptions():
    request = YOUTUBE.subscriptions().list(
        part="snippet",
        channelId="UCq0LuNd6o2XTTEdSkQPhGxw",
    )
    response = request.execute()
    return response.get("items", [])


def get_latest_videos(channel_id):
    """Gets the latest videos from a YouTube channel."""
    request = YOUTUBE.search().list(
        part="snippet", channelId=channel_id, order="date", maxResults=10
    )
    response = request.execute()
    list_videos = []

    for entry in response.get("items", []):
        if is_duration_over_minutes(get_video_len(entry["id"]["videoId"]), 15):
            list_videos.append(entry)

    return list_videos


def is_duration_over_minutes(duration_iso8601, length: int = 15):
    """
    Checks if a duration in ISO 8601 format is over 15 minutes.

    Args:
        duration_iso8601: The duration string in ISO 8601 format (e.g., "PT14M20S").

    Returns:
        True if the duration is over 15 minutes, False otherwise.  Returns None if the input is invalid.
    """
    try:
        duration = isodate.parse_duration(duration_iso8601)
        total_seconds = duration.total_seconds()
        return total_seconds > (length * 60)  # 15 minutes * 60 seconds/minute
    except isodate.ISO8601Error:  # Handle invalid duration format
        print("Invalid ISO 8601 Duration Format")
        return False
    except Exception as e:  # Catch any other potential errors
        print(f"An error occurred: {e}")
        return False


def get_subscriptions_videos():
    """Gets the latest videos from the user's YouTube subscriptions."""
    subscriptions_list = subscriptions()
    videos = []
    for subscription in subscriptions_list:
        channel_id = subscription["snippet"]["resourceId"]["channelId"]
        dt_object = datetime.strptime(
            subscription["snippet"]["publishedAt"], "%Y-%m-%dT%H:%M:%S.%fZ"
        ).replace(tzinfo=UTC)

        if datetime.now(UTC) - dt_object > timedelta(minutes=10) and datetime.now(
            UTC
        ) - dt_object < timedelta(days=1):
            videos.extend(get_latest_videos(channel_id))

    return videos


def search_videos(query, time_range=7):
    """Searches YouTube videos within a specified time range."""
    now = datetime.now(UTC)
    published_after = (
        (now - timedelta(days=time_range)).isoformat().replace("+00:00", "Z")
    )

    request = YOUTUBE.search().list(
        q=query,
        part="snippet",
        type="video",
        publishedAfter=published_after,
        order="relevance",
        maxResults=50,
    )
    response = request.execute()
    return response.get("items", [])


def is_trending(video_id):
    """Checks if a video is trending (a simplified approach)."""
    # Note: The YouTube Data API v3 does not directly provide a "trending" flag.
    # Trending status is dynamic and algorithm-driven. This function uses a proxy
    # by checking if a video has a high view count relative to its age.  This is not definitive.
    try:
        request = YOUTUBE.videos().list(part="statistics,snippet", id=video_id)
        response = request.execute()
        items = response.get("items", [])
        if items:
            video_stats = items[0]["statistics"]
            view_count = int(video_stats.get("viewCount", 0))

            # Very basic trending proxy. You'll likely need to refine this based on your needs.
            # Consider using other signals like likeCount, commentCount, and video duration
            # along with viewCount and upload date for a more robust "trending" metric.
            published_at_str = items[0]["snippet"]["publishedAt"]
            published_at = isodate.parse_datetime(published_at_str)
            age_in_days = (datetime.utcnow() - published_at).days
            if age_in_days > 0:  # Avoid division by 0
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
    """Gets transcript, link, likes, views, creator, and video name for a video."""
    try:
        request = YOUTUBE.videos().list(part="snippet,statistics", id=video_id)
        response = request.execute()
        if response.get("items"):
            video_data = response["items"][0]
            snippet = video_data.get("snippet", {})
            statistics = video_data.get("statistics", {})

            creator = snippet.get("channelTitle", "Unknown")
            view_count = statistics.get("viewCount", 0)
            like_count = statistics.get("likeCount", 0)
            video_name = snippet.get("title", "Unknown")
        else:
            creator = "Unknown"
            view_count = 0
            like_count = 0
            video_name = "Unknown"

        return {
            "creator": creator,
            "views": view_count,
            "likes": like_count,
            "video_name": video_name,
        }
    except Exception as e:
        LOGGER.info(f"Error getting video info: {e}")
        return None


def get_video_len(video_id):
    """Gets transcript, link, likes, views, creator, and video name for a video."""
    try:
        request = YOUTUBE.videos().list(part="contentDetails", id=video_id)
        response = request.execute()
        if response.get("items"):
            return response["items"][0]["contentDetails"]["duration"]
        else:
            return "PT11M20S"
    except Exception as e:
        LOGGER.info(f"Error getting video info: {e}")
        return None


def get_transcript(video_id):
    """Gets the transcript of a YouTube video."""
    try:
        transcript = youtube_transcript_api.YouTubeTranscriptApi.get_transcript(
            video_id
        )
        # Format transcript as a string:
        # transcript_text = " ".join([entry['text'] for entry in transcript])
        return transcript
    except youtube_transcript_api.TranscriptsDisabled:
        LOGGER.info("Transcripts are disabled for this video.")
    except youtube_transcript_api.NoTranscriptFound:
        LOGGER.info("No transcript found for this video.")
    except Exception as e:
        LOGGER.info(f"Error getting transcript: {e}")


def join_transcript(transcript):
    """Join the transcript into a single string."""
    return " ".join([entry["text"] for entry in transcript])


def get_comments(video_id, max_comments=100):  # Added max_comments
    """Gets comments for a video."""
    try:
        comments = []
        request = YOUTUBE.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=max_comments,  # Limit the number of comments retrieved
        )
        while request:
            response = request.execute()
            for item in response.get("items", []):
                comment = item["snippet"]["topLevelComment"]["snippet"]
                comments.append({
                    "author": comment.get("authorDisplayName", "Unknown"),
                    "text": comment.get("textOriginal", ""),
                    "likeCount": comment.get("likeCount", 0),
                })
            if "nextPageToken" in response:
                request = YOUTUBE.commentThreads().list_next(request, response)
            else:
                request = None  # No more pages
        return comments
    except Exception as e:
        LOGGER.info(f"Error getting comments: {e}")
        return []


def get_top_comment(comments: list[dict], max_words: int, creator: str) -> str:
    """Get the top comment from a list of comments."""
    top_comment = ""
    top_comment_upvotes = 0
    for comment in comments:
        words = comment["text"].split()
        if (
            len(words) <= max_words
            and comment["text"].lower() != "[removed]"
            and "Top comment" not in comment["text"]
            and comment["author"] != creator
        ):
            upvotes = comment.get("likeCount", 0)
            if upvotes > top_comment_upvotes:
                LOGGER.info("Top comment found: %s, vid creator: %s", comment, creator)
                top_comment = str(comment["text"])
                top_comment_upvotes = upvotes
    print(top_comment_upvotes)
    return top_comment


if __name__ == "__main__":
    comments = get_comments("Rivbvb2JDCw")
    print(comments)
    print(get_top_comment(comments, 10))
