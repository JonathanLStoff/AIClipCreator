import os
import logging

API_KEY = os.environ.get("YOUTUBE_API_KEY")

SECTIONS_TYPES = ["funny moments"]

LOGGER = logging.getLogger("clip_creator")
LOGGER.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
LOGGER.addHandler(console_handler)