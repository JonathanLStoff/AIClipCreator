import logging
import os
import sys

API_KEY = [
    os.environ.get("YOUTUBE_API_KEY_1"),
    os.environ.get("YOUTUBE_API_KEY_2"),
    os.environ.get("YOUTUBE_API_KEY_3")
    ]

SECTIONS_TYPES = ["funny moments"]

LOGGER = logging.getLogger("clip_creator")
LOGGER.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
LOGGER.addHandler(console_handler)


TIKTOK_USERNAME = os.environ.get("TIKTOK_USERNAME")
TIKTOK_PASSWORD = os.environ.get("TIKTOK_PASSWORD")

TIMESTAMP_REGEX = r"^(?:[0-9]|1[0-2]):[0-5][0-9](?::[0-5][0-9])?\b(?:\s.*)?$"
RM_TIMESTAMP_REGEX = r"(?:[0-9]|1[0-2]):[0-5][0-9](?::[0-5][0-9])?"

NUM_CORES = os.cpu_count() or 1
LOGGER.info("Available CPU cores/threads: %d", NUM_CORES)

if sys.platform.startswith("win"):
    #FFMPEG_PARAMS = ["-cq", "28"]
    CODEC = "h264_nvenc"
    DOWNLOAD_FOLDER = "D:/tmp/raw"
    TMP_DOWNLOAD_FOLDER = "tmp/raw"
    TMP_CLIPS_FOLDER = "tmp/clips"
    CLIPS_FOLDER = "D:/tmp/clips"
    MODELS_FOLDER = "D:/models"
    WIS_DEVICE = "cuda:0"
    
    MODEL_SPEC_FOLDERS =  {
        "Systran/faster-whisper-large-v2":"D:/models/models--Systran--faster-whisper-large-v2/snapshots/f0fe81560cb8b68660e564f55dd99207059c092e",
        "facebook/seamless-m4t-v2-large":"D:/models/models--facebook--seamless-m4t-v2-large/snapshots/5f8cc790b19fc3f67a61c105133b20b34e3dcb76"
    }
    LOW_CPU_MEM = False
    USER_ACCOUNT = os.environ.get("USERPROFILE")
    USER_ACCOUNT_FOLDER = os.path.basename(USER_ACCOUNT)
    
    CHROME_USER_PATH = f"C:/Users/{USER_ACCOUNT_FOLDER}/AppData/Local/Google/Chrome/User Data/Default"
    
    LOGGER.info("Running on Windows")
elif sys.platform.startswith("darwin"):
    #FFMPEG_PARAMS = ["-c:v", "h264_videotoolbox"]
    CODEC = "libx264"
    MODELS_FOLDER = "/Volumes/externalSSD/models"
    DOWNLOAD_FOLDER = "/Volumes/externalSSD/tmp/raw"
    TMP_DOWNLOAD_FOLDER = "tmp/raw"
    TMP_CLIPS_FOLDER = "tmp/clips"
    CLIPS_FOLDER = "/Volumes/externalSSD/tmp/clips"
    WIS_DEVICE = "cpu"
    LOW_CPU_MEM = False
    MODEL_SPEC_FOLDERS =  {
        "Systran/faster-whisper-large-v2":"/Volumes/externalSSD/models/models--Systran--faster-whisper-large-v2/snapshots/f0fe81560cb8b68660e564f55dd99207059c092e",
        "facebook/seamless-m4t-v2-large":"/Volumes/externalSSD/models/models--facebook--seamless-m4t-v2-large/snapshots/5f8cc790b19fc3f67a61c105133b20b34e3dcb76"
    }
    CHROME_USER_PATH = f"/Users/{os.environ.get('USER')}/Library/Application Support/Google/Chrome"
    LOGGER.info("Running on macOS")
else:
    DOWNLOAD_FOLDER = os.path.expanduser("~/Downloads")


FONT_PATH = "Vercetti Regular/WorkSans-Bold.ttf"

COLORS = {
    "black": (0, 0, 0, 255),
    "white": (255, 255, 255, 255),
    "red": (255, 0, 0, 255),
    "green": (0, 255, 0, 255),
    "blue": (0, 0, 255, 255),
    "yellow": (255, 255, 0, 255),
    "orange": (255, 165, 0, 255),
    "purple": (128, 0, 128, 255)
}
# Key is default color, value the highlight color
COLOR_PAIRS = {
    
    "yellow": ["blue", "green", "purple", "white", "red"],
    "white": ["green", "blue", "purple", "orange", "yellow", "red"],
    "blue": ["green", "red", "purple", "orange", "yellow", "white"],
    
    }

YT_MAX_RETRIES = 3

GOOGLE_ACCOUNT_NAME = "clipcityai@gmail.com"