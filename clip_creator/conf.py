import logging
import os
import re
import sys
from os.path import join

import toml

API_KEY = [
    os.environ.get("YOUTUBE_API_KEY_1", ""),
    os.environ.get("YOUTUBE_API_KEY_2", ""),
    os.environ.get("YOUTUBE_API_KEY_3", ""),
]


SECTIONS_TYPES = ["funny moments"]

LOGGER = logging.getLogger("clip_creator")
LOGGER.setLevel(logging.INFO)
logging.getLogger("googleapiclient.discovery_cache").setLevel(logging.ERROR)
console_handler = logging.StreamHandler()
console_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
)
LOGGER.addHandler(console_handler)

# Add file handler to save logs to /logs/loggername.log

file_handler = logging.FileHandler("logs/clip_creator.log")
file_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
)
LOGGER.addHandler(file_handler)
LOGGER.info("==================Logger initialized======================")
CONFIG = toml.load(join("clip_creator/social/", "config.toml"))

TIKTOK_USERNAME = os.environ.get("TIKTOK_USERNAME")
TIKTOK_PASSWORD = os.environ.get("TIKTOK_PASSWORD")

TIMESTAMP_REGEX = r"^(?:[0-9]|1[0-2]):[0-5][0-9](?::[0-5][0-9])?\b(?:\s.*)?$"
RM_TIMESTAMP_REGEX = r"(?:[0-9]|1[0-2]):[0-5][0-9](?::[0-5][0-9])?"
DB_PATH = "aiclipcreator.db"
NUM_CORES = os.cpu_count() or 1
LOGGER.info("Available CPU cores/threads: %d", NUM_CORES)
BLUESTACKS_INSTANCE = "clipsphone"

if sys.platform.startswith("win"):
    # FFMPEG_PARAMS = ["-cq", "28"]
    CODEC = "h264_nvenc"
    BLUESTACKS_PATH = r"C:/Program Files/BlueStacks_nxt/HD-Player.exe"
    ADB_DEVICE = "ZY22H5JP3S"
    DOWNLOAD_FOLDER = "D:/tmp/raw"
    TMP_DOWNLOAD_FOLDER = "tmp/raw"
    TMP_CLIPS_FOLDER = "tmp/clips"
    REDDIT_TEMPLATE_AUD = "D:/tmp/reddit/reddit_music.mp3"
    REDDIT_TEMPLATE_MUS = "D:/tmp/reddit/reddit_clip_music.wav"
    REDDIT_TEMPLATE_BG = "D:/tmp/reddit"
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
    ADB_PATH_EXE = "adb"
    ADB_SHELL = True
    CHROME_USER_PATH = (
        f"C:/Users/{USER_ACCOUNT_FOLDER}/AppData/Local/Google/Chrome/User Data"
    )
    BACKUP_FOLDER = "D:/tmp/backup"
    LOGGER.info("Running on Windows")
elif sys.platform.startswith("darwin"):
    # FFMPEG_PARAMS = ["-c:v", "h264_videotoolbox"]
    CODEC = "libx264"
    ADB_SHELL = True
    BLUESTACKS_PATH = r"C:/Program Files/BlueStacks_nxt/HD-Player.exe"
    ADB_PATH_EXE = "/opt/homebrew/bin/adb"
    ADB_DEVICE = "ZY22H5JP3S"
    MODELS_FOLDER = "/Volumes/externalSSD/models"
    DOWNLOAD_FOLDER = "/Volumes/externalSSD/tmp/raw"
    REDDIT_TEMPLATE_AUD = "/Volumes/externalSSD/tmp/reddit/reddit_music.mp3"
    REDDIT_TEMPLATE_MUS = "/Volumes/externalSSD/tmp/reddit/reddit_clip_music.wav"
    REDDIT_TEMPLATE_BG = "/Volumes/externalSSD/tmp/reddit"
    ANDROID_IMAGE_PATH = "/Volumes/externalSSD/vbox/Lineage.vdi"
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
    BACKUP_FOLDER = "/Volumes/externalSSD/tmp/backup"
    LOGGER.info("Running on macOS")
else:
    DOWNLOAD_FOLDER = os.path.expanduser("~/Downloads")

ADB_PATH = "/storage/self/primary"
FONT_PATH = "fonts/WorkSans-Bold.ttf"

E_FONT_PATH = "fonts/NotoColorEmoji-Regular.ttf"

if not os.path.exists("fonts/NotoColorEmoji-Regular.ttf"):
    LOGGER.error(
        "Please download the font:"
        " https://fonts.google.com/noto/specimen/Noto+Color+Emoji"
    )
    LOGGER.error("And place it in the fonts folder")
    sys.exit(1)
POSSIBLE_TRANSLATE_LANGS = [
    "es",  # spanish
]
POSSIBLE_TRANSLATE_LANGS_TTS = {
    "es": {  # spanish
        "es": "e",
        "tts": [
            ("ef_dora", 1.4),
            ("em_alex", 1.2),
        ],
        "profile": "Reddit ciudad",
        "username": "reddit_city_span",
    }
}
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
    "AITAH",
    "tifu",
    "TwoHotTakes",
    "relationship_advice",
    "BestofRedditorUpdates",
]
SUB_REDDITS_COM = [
    "askreddit",
    "nostupidquestions",
    "AskMen",
]
SUB_MULTIPLY = {
    "TwoHotTakes": 3.0,
    "relationship_advice": 1.0,
    "BestofRedditorUpdates":2.0,
    "askreddit": 1.0,
    "amitheasshole":1.0,
    "confessions":2.2,
    "stories":2.2,
    "AITAH":1.0,
    "tifu":0.9,
}
REDDIT_ACCRO_SUB = {
    "AITA": "am I the a hole",
    "AITAH": "am I the a hole",
    "TIL": "today I learned",
    "WIBTA": "would I be the a hole",
    "YTA": "you're the a hole",
    "NTA": "not the a hole",
    "WIBTAH": "would I be the a hole",
    "TIFU": "today I fricked up",
    "SIL": "sister in law",
    "BIL": "brother in law",
    "MIL": "mother in law",
    "FIL": "father in law",
    "IDC": "I don't care",
    "IDK": "I don't know",
    "IMO": "in my opinion",
    "IMHO": "in my humble opinion",
    "IIRC": "if I recall correctly",
    "TL;DR": "too long didn't read",
    "ELI5": "explain like I'm 5",
    "NSFW": "not safe for work",
    "TLDR": "too long didn't read",
    "OC": "original content",
    "24/7": "twenty four seven",
}
TTS_VOICES = [
    ("af_heart", 1.5),
    ("am_adam", 1.3),
]
BAD_WORD_SUB = "[\u00a0__\u00a0]"
REDDIT_DOMAIN = (
    "https://www.reddit.com/svc/shreddit/community-more-posts/hot/?t=DAY&name="
)
TOP_REDDIT_DOMAIN = (
    "https://www.reddit.com/svc/shreddit/community-more-posts/top/?t=month&name=" # can be t=all, t=DAY, t=week, t=month, t=year, t=all
)
REDDIT_POST_DOMAIN = (  # + /[0]r/[1]stories/[2]comments/[3]1izveyu/sounds_too_cheesy_to_be_real_but_it_is/
    "https://www.reddit.com"
)
# example use: REDDIT_DOMAIN+"amitheasshole"

REGEX_FOR_UPDATE = r"https:\/\/www\.reddit\.com[^\s]+"
REGEX_FOR_UPDATE_RM = r".*www\.reddit\.com[^\s]*.*"

# WK_SCHED = [
#     ["06:00", "16:50", "18:35","22:40"], # Monday
#     ["06:00", "16:50", "18:55", "23:30"], # Tuesday
#     ["06:00", "18:00", "22:15", "22:40"], # Wednesday
#     ["06:00", "16:20", "21:05", "23:55"], # Thursday
#     ["06:00", "17:00", "21:35", "23:50"], # Friday
#     ["06:00", "17:10", "20:10", "23:20"], # Saturday
#     ["06:00", "17:35", "20:50", "23:30"], # Sunday
# ]
WK_SCHED = [
    ["23:50", "23:50", "23:50", "23:50"],  # Monday
    ["23:50", "23:50", "23:50", "23:50"],  # Tuesday
    ["23:50", "23:50", "23:50", "23:50"],  # Wednesday
    ["23:50", "23:50", "23:50", "23:50"],  # Thursday
    ["23:50", "23:50", "23:50", "23:50"],  # Friday
    ["23:50", "23:50", "23:50", "23:50"],  # Saturday
    ["23:50", "23:50", "23:50", "23:50"],  # Sunday
]
WK_SCHED_COM = [
    ["23:50", "23:50", "23:50", "23:50"],  # Monday
    ["23:50", "23:50", "23:50", "23:50"],  # Tuesday
    ["23:50", "23:50", "23:50", "23:50"],  # Wednesday
    ["23:50", "23:50", "23:50", "23:50"],  # Thursday
    ["23:50", "23:50", "23:50", "23:50"],  # Friday
    ["23:50", "23:50", "23:50", "23:50"],  # Saturday
    ["23:50", "23:50", "23:50", "23:50"],  # Sunday
]
RED_COM_DELAY = 0.2
# Find and replace all text.
REPLACE_CURSE_WORDS_DIRT = {
    "&": " and ",
    "*": " star ",
    "(": " parenthesis, ",
    ")": ".",
    "@": " at ",
    "#": " hashtag ",
    "%": " percent",
    "/": " ",
    "fuck": "frick",
    "he's": "he is",
    "she's": "she is",
    "you're": "you are",
    "they're": "they are",
    "we're": "we are",
    "it's": "its",
    "that's": "thats",
    "there's": "theres",
    "what's": "what is",
    "who's": "whos",
    "can't": "cant",
    "won't": "will not",
    "wouldn't": "wouldnt",
    "shouldn't": "shouldnt",
    "couldn't": "couldnt",
    "didn't": "didnt",
    "murder": "unalive",
    "sex": "seggs",
    "asshole": "a hole",
    "died": "unalived",
    "killed": "unalived",
    "10s": " teens",
    "20s": " twenties",
    "30s": " thirties",
    "40s": " forties",
    "50s": " fifties",
    "60s": " sixties",
    "70s": " seventies",
    "80s": " eighties",
    "90s": " nineties",
    "commit suicide": "unalive myself",
    "committed suicide": "unalive themselves",
    "suicide": "unalive",
    "suicidal thoughts": "thoughts of unalive",
    "suicidal": "thoughts of unalive",
    "edibles": "brownies",
    "an edible": "a brownie",
    "smoke pot": "blase it",
    "pussy": "kitty",
    "vagina": "kitty",
    "boobs": "bobs",
    "fiancée": "fiansay",
    "fiancé": "fiansay",
    "ex-": "ex ",
    
}
# This will only replace if they are the same
REPLACE_WORDS_CLEAN = {
    "dead":"unalive",
    "dying":"unalived",
    "rape": "grape",
    "rapist": "grapist",
    
}
