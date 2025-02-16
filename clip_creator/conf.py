import os
import logging

API_KEY = os.environ.get("YOUTUBE_API_KEY_3")

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