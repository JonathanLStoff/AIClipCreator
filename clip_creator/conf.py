import logging
import os
import re
import sys
from os.path import join

import toml

API_KEY = [
    os.environ.get("YOUTUBE_API_KEY_1", "AIzaSyAkgL1ASemVitT3Rtv_Teo8Uw8kFiwloR0"),
    os.environ.get("YOUTUBE_API_KEY_2", "AIzaSyDfWHIwbwlO5GXal7_vfb4CEdfcCVHX7V8"),
    os.environ.get("YOUTUBE_API_KEY_3", "AIzaSyCEhkfwsn6hCX3l4_HnYZm4bjOjctzTb8k"),
]



SECTIONS_TYPES = ["funny moments"]

LOGGER = logging.getLogger("clip_creator")
LOGGER.setLevel(logging.INFO)
logging.getLogger('googleapicliet.discovery_cache').setLevel(logging.ERROR)
console_handler = logging.StreamHandler()
console_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
)
LOGGER.addHandler(console_handler)

CONFIG = toml.load(join("clip_creator/social/", "config.toml"))

TIKTOK_USERNAME = os.environ.get("TIKTOK_USERNAME")
TIKTOK_PASSWORD = os.environ.get("TIKTOK_PASSWORD")

TIMESTAMP_REGEX = r"^(?:[0-9]|1[0-2]):[0-5][0-9](?::[0-5][0-9])?\b(?:\s.*)?$"
RM_TIMESTAMP_REGEX = r"(?:[0-9]|1[0-2]):[0-5][0-9](?::[0-5][0-9])?"

NUM_CORES = os.cpu_count() or 1
LOGGER.info("Available CPU cores/threads: %d", NUM_CORES)

if sys.platform.startswith("win"):
    # FFMPEG_PARAMS = ["-cq", "28"]
    CODEC = "h264_nvenc"
    DOWNLOAD_FOLDER = "D:/tmp/raw"
    TMP_DOWNLOAD_FOLDER = "tmp/raw"
    TMP_CLIPS_FOLDER = "tmp/clips"
    REDDIT_TEMPLATE_FOLDER = "D:/tmp/reddit"
    CLIPS_FOLDER = "D:/tmp/clips"
    MODELS_FOLDER = "D:/models"
    WIS_DEVICE = "cuda:0"
    ANDROID_IMAGE_PATH = "D:/vbox/Lineage.vdi"
    MODEL_SPEC_FOLDERS = {
        "Systran/faster-whisper-large-v2": "D:/models/models--Systran--faster-whisper-large-v2/snapshots/f0fe81560cb8b68660e564f55dd99207059c092e",
        "facebook/seamless-m4t-v2-large": "D:/models/models--facebook--seamless-m4t-v2-large/snapshots/5f8cc790b19fc3f67a61c105133b20b34e3dcb76",
    }
    LOW_CPU_MEM = False
    USER_ACCOUNT = os.environ.get("USERPROFILE")
    USER_ACCOUNT_FOLDER = os.path.basename(USER_ACCOUNT)

    CHROME_USER_PATH = (
        f"C:/Users/{USER_ACCOUNT_FOLDER}/AppData/Local/Google/Chrome/User Data"
    )

    LOGGER.info("Running on Windows")
elif sys.platform.startswith("darwin"):
    # FFMPEG_PARAMS = ["-c:v", "h264_videotoolbox"]
    CODEC = "libx264"
    MODELS_FOLDER = "/Volumes/externalSSD/models"
    DOWNLOAD_FOLDER = "/Volumes/externalSSD/tmp/raw"
    REDDIT_TEMPLATE_FOLDER = "/Volumes/externalSSD/tmp/reddit"
    TMP_DOWNLOAD_FOLDER = "tmp/raw"
    TMP_CLIPS_FOLDER = "tmp/clips"
    CLIPS_FOLDER = "/Volumes/externalSSD/tmp/clips"
    WIS_DEVICE = "cpu"
    LOW_CPU_MEM = False
    MODEL_SPEC_FOLDERS = {
        "Systran/faster-whisper-large-v2": "/Volumes/externalSSD/models/models--Systran--faster-whisper-large-v2/snapshots/f0fe81560cb8b68660e564f55dd99207059c092e",
        "facebook/seamless-m4t-v2-large": "/Volumes/externalSSD/models/models--facebook--seamless-m4t-v2-large/snapshots/5f8cc790b19fc3f67a61c105133b20b34e3dcb76",
    }
    CHROME_USER_PATH = (
        f"/Users/{os.environ.get('USER')}/Library/Application Support/Google/Chrome"
    )
    LOGGER.info("Running on macOS")
else:
    DOWNLOAD_FOLDER = os.path.expanduser("~/Downloads")


FONT_PATH = "fonts/WorkSans-Bold.ttf"

E_FONT_PATH = "fonts/NotoColorEmoji-Regular.ttf"

if not os.path.exists("fonts/NotoColorEmoji-Regular.ttf"):
    LOGGER.error(
        "Please download the font:"
        " https://fonts.google.com/noto/specimen/Noto+Color+Emoji"
    )
    LOGGER.error("And place it in the fonts folder")
    sys.exit(1)

COLORS = {
    "black": (0, 0, 0, 255),
    "white": (255, 255, 255, 255),
    "red": (255, 0, 0, 255),
    "green": (0, 255, 0, 255),
    "blue": (0, 0, 255, 255),
    "yellow": (255, 255, 0, 255),
    "orange": (255, 165, 0, 255),
    "purple": (128, 0, 128, 255),
}
# Key is default color, value the highlight color
COLOR_PAIRS = {
    "yellow": ["blue", "green", "purple", "white", "red"],
    "white": ["green", "blue", "purple", "orange", "yellow", "red"],
    "blue": ["green", "red", "purple", "orange", "yellow", "white"],
}

YT_MAX_RETRIES = 3

GOOGLE_ACCOUNT_NAME = "clipcityai@gmail.com"


POSTABLE_TIMES = [
    [  # Monday
        [""],  # Time frame 1
        [""],  # Time frame 2
        [""],  # Time frame 3
    ],
]

ERRORS_TYPES = ["minor", "major", "critical"]

EMOJIS_RE = re.compile(
    "["
    "\U0001f600-\U0001f64f"  # emoticons
    "\U0001f300-\U0001f5ff"  # symbols & pictographs
    "\U0001f680-\U0001f6ff"  # transport & map symbols
    "\U0001f1e0-\U0001f1ff"  # flags (iOS)
    "\U00002702-\U000027b9"  # various symbols
    "\U00002702-\U000027b0"
    "\U000024c2-\U0001f251"
    "\U0001f926-\U0001f937"
    "\U00010000-\U0010ffff"
    "\u2640-\u2642"
    "\u2600-\u2b55"
    "\u23cf"
    "\u23e9"
    "\u231a"
    "\u23f3"
    "\u2328"
    "\u2388"
    "\u2389"
    "]+",
    flags=re.UNICODE,
)

CURSE_WORDS = (
    open("clip_creator/utils/OffensiveWords-comma-separated-text.txt").read().split(",")
)

SUB_REDDITS = [ 
    "amitheasshole",
    "confessions",
    "stories",
    "todayilearned",
    "unpopularopinion",
    "AITAH",
    
]
SUB_REDDITS_COM = [ 
    "askreddit",
    "nostupidquestions",

]
REDDIT_ACCRO_SUB = {
    "AITA ": "am I the a hole ",
    "TIL ": "today I learned "

    
}
TTS_VOICES = [
    ("af_heart",1.5),
    ("am_adam",1.35),
]
BAD_WORD_SUB = "[\u00a0__\u00a0]"
REDDIT_DOMAIN = "https://www.reddit.com/svc/shreddit/community-more-posts/hot/?t=DAY&name="
REDDIT_POST_DOMAIN = "https://www.reddit.com" # + /[0]r/[1]stories/[2]comments/[3]1izveyu/sounds_too_cheesy_to_be_real_but_it_is/
# example use: REDDIT_DOMAIN+"amitheasshole"