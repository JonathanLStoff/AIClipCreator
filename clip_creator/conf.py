import os
import logging
import sys

API_KEY = os.environ.get("YOUTUBE_API_KEY")

SECTIONS_TYPES = ["funny moments"]

LOGGER = logging.getLogger("clip_creator")
LOGGER.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
LOGGER.addHandler(console_handler)

TIKTOK_USERNAME = os.environ.get("TIKTOK_USERNAME")
TIKTOK_PASSWORD = os.environ.get("TIKTOK_PASSWORD")

TIMESTAMP_REGEX = r'^(?:[0-9]|1[0-2]):[0-5][0-9](?::[0-5][0-9])?\b(?:\s.*)?$'
RM_TIMESTAMP_REGEX = r'(?:[0-9]|1[0-2]):[0-5][0-9](?::[0-5][0-9])?'


if sys.platform.startswith("win"):
    DOWNLOAD_FOLDER = os.path.join(os.environ.get("USERPROFILE", "C:\\"), "Downloads")
    CLIPS_FOLDER = os.path.join(os.environ.get("USERPROFILE", "C:\\"), "Videos")
    LOGGER.info("Running on Windows")
elif sys.platform.startswith("darwin"):
    DOWNLOAD_FOLDER = "/Volumes/externalSSD/tmp/raw"
    TMP_DOWNLOAD_FOLDER = "tmp/raw"
    TMP_CLIPS_FOLDER = "tmp/clips"
    CLIPS_FOLDER = "/Volumes/externalSSD/tmp/clips"
    LOGGER.info("Running on macOS")
else:
    DOWNLOAD_FOLDER = os.path.expanduser("~/Downloads")