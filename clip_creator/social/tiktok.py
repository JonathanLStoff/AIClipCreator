import os
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from tiktok_uploader.upload import upload_video


def post_to_tiktok(
    video_path,
    title,
    schedule: datetime | None = None,

):
    """
    Posts a video to TikTok using the TikTok Open API.

    Args:
        access_token: The TikTok API access token.
        video_path: The local path to the video file.
        title: The title/caption for the TikTok post.
        privacy_level: The privacy level of the post (e.g., "PUBLIC_TO_EVERYONE", "MUTUAL_FOLLOW_FRIENDS", "SELF_ONLY").
        disable_duet: Whether to disable duets for the video.
        disable_comment: Whether to disable comments for the video.
        disable_stitch: Whether to disable stitches for the video.
        video_cover_timestamp_ms: The timestamp (in milliseconds) for the video cover image.

    Returns:
        A dictionary containing the API response, or None if an error occurs.  Prints error details to console.
    """
    cookies_list = get_tiktok_cookies()
    if not cookies_list:
        upload_video(video_path, title, username=os.environ.get("TIKTOK_USERNAME"), password=os.environ.get("TIKTOK_P"), schedule=schedule, )
    elif schedule:
        upload_video(video_path, title, username=os.environ.get("TIKTOK_USERNAME"), password=os.environ.get("TIKTOK_P"), cookies_list=cookies_list, schedule=schedule, )
    else:
        upload_video(video_path, title, cookies_list=cookies_list, )


def get_tiktok_cookies(url="https://www.tiktok.com"):
    """
    Opens TikTok in a Selenium WebDriver and retrieves all cookies as a list of dictionaries.

    Args:
        url: The URL of the TikTok website (default: "https://www.tiktok.com").

    Returns:
        A list of dictionaries, where each dictionary represents a cookie, or None if an error occurs or no cookies are found.
        Prints error details to the console.
    """
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")  # Optional: Run browser in the background

        driver = webdriver.Chrome(options=options)  # Or Firefox(), Edge(), etc.
        driver.get(url)

        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located(
                    (By.TAG_NAME, "video")
                )  # Example: wait for a video element
            )
        except:
            print("Timeout waiting for page to load. Cookies might not be available.")

        cookies_list = (
            driver.get_cookies()
        )  # Selenium already returns a list of dictionaries

        driver.quit()
        return cookies_list

    except Exception as e:
        print(f"An error occurred: {e}")
        if "driver" in locals():
            driver.quit()
        return None

if __name__ == "__main__":
    post_to_tiktok("tmp/clips/5FctraXMT-E.mp4", "#fyp #gaming #clip #fyppppppppppppp \n credit SMii7Yplus's Fortnite Counter-Strike is Crazy")
    