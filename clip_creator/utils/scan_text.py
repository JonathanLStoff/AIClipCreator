import re
from collections import Counter

from clip_creator.conf import CURSE_WORDS, LOGGER, RM_TIMESTAMP_REGEX, TIMESTAMP_REGEX


def most_common_ngrams(text, n=3):
    """
    Finds the most common n-grams (1, 2, and 3 words) in a text.

    Args:
        text: The input text string.
        n: The maximum n-gram size to consider (default is 3).

    Returns:
        A dictionary containing the most common 1-gram, 2-gram, and 3-gram.
        Returns empty strings if no n-grams are found.
    """

    # 1. Clean and tokenize the text:
    text = text.lower()  # Convert to lowercase
    text = re.sub(r"[^\w\s]", "", text)  # Remove punctuation
    words = text.split()

    # 2. Count n-grams:
    ngram_counts = Counter()
    for i in range(len(words)):
        for j in range(1, min(n, len(words) - i) + 1):  # Iterate through ngram sizes
            ngram = " ".join(words[i : i + j])
            ngram_counts[ngram] += 1

    # 3. Find the most common n-grams:
    most_common = {}
    for i in range(1, n + 1):
        most_common[f"{i}-gram"] = {}  # Initialize to empty strings
        for ngram, count in ngram_counts.most_common():
            if len(ngram.split()) == i:
                most_common[f"{i}-gram"]["word"] = ngram
                most_common[f"{i}-gram"]["count"] = count
                break  # Break after finding the first most common ngram of this length

    return most_common[f"{i}-gram"].get("word", ""), most_common[f"{i}-gram"].get(
        "count", 0
    )


def find_timestamps(text: str):
    """
    Find timestamp in a text only if exactly one timestamp is found, otherwise returns None.
    """
    timestamps = []
    for match in re.finditer(TIMESTAMP_REGEX, text):
        timestamps.append(match.group())
    return timestamps[0] if len(timestamps) == 1 else None


def convert_timestamp_to_seconds(timestamp: str) -> int | None:
    """
    Convert timestamp in the format "HH:MM:SS" to seconds.
    """
    timestamp_part = ""
    for t in timestamp.split(" "):
        if ":" in t:
            timestamp_part = t
            break
    seconds = timestamp_part.split(":")[-1]
    minutes = timestamp_part.split(":")[-2]
    hours = 0 if len(timestamp_part.split(":")) < 3 else timestamp_part.split(":")[-3]
    try:
        return int(hours) * 3600 + int(minutes) * 60 + int(seconds)
    except ValueError:
        LOGGER.error("Invalid timestamp format: %s", timestamp)
    return None


def find_timestamp_clips(raw_transcript: list, timestamp: int) -> list[dict]:
    """
    Find timestamp in a text only if exactly one timestamp is found, otherwise returns None.
    snippet from raw_transcript: {'text': 'out our other man outs right over here', 'start': 1060.84, 'duration': 3.52}

    output: [{'text': str, 'start': float, 'duration': float}]
    """
    clip = []
    item_index = 0
    for i, section in enumerate(raw_transcript):
        if int(section["start"]) > timestamp:
            break
        item_index = i

    for i, section in enumerate(raw_transcript):
        if i >= item_index and section["start"] < timestamp + 61:
            clip.append(section)
    return clip
def reddit_remove_bad_words(text: str) -> str:
    """
    Remove bad words from a text.
    """
    for word in text.split():
        for curse_word in CURSE_WORDS:
            if curse_word in word:
                text = text.replace(word, "naughty word")
    
    return text

def find_bad_words(true_transcript: list[dict], uncensored_transcript) -> (list[list[int]], list[dict]):
    """
    Find bad words in a text.
    """
    bad_words = []
    ftranscript = []
    for word_dict in true_transcript:
        word = word_dict.get("text", "").strip().lower()
        LOGGER.debug("Word: %s", word)
        if word in CURSE_WORDS:
            bad_words.append([
                int(float(word_dict.get("start", 0)) * 1000),
                int(float(word_dict.get("start", 0)) * 1000)
                + int(float(word_dict.get("duration", 1)+0.5) * 1000),
            ])
            word_dict["text"] =  "*" * len(word)
        ftranscript.append(word_dict)
    for word_dict in uncensored_transcript:
        word = word_dict.get("text", "").strip().lower()
        LOGGER.info("Word: %s", word)
        if word in CURSE_WORDS:
            bad_words.append([
                int(float(word_dict.get("start", 0)) * 1000),
                int(float(word_dict.get("start", 0)) * 1000)
                + int(float(word_dict.get("duration", 1)) * 1000),
            ])
            word_dict["text"] =  "*" * len(word)
        ftranscript.append(word_dict)
    LOGGER.info("Bad words: %s", bad_words)
    return bad_words, ftranscript


def clean_text(text: str) -> str:
    """
    Remove all substrings that match the regex pattern from text and trim off white spaces.

    Args:
        text: The text to be cleaned.
        pattern: The regex pattern whose matches will be removed from the text.

    Returns:
        The cleaned text.
    """
    cleaned = re.sub(RM_TIMESTAMP_REGEX, "", text)
    LOGGER.info("Cleaned text: %s", cleaned.strip())
    return cleaned.strip()


def sanitize_filename(filename: str) -> str:
    """
    Convert a string into a safe filename by removing or replacing illegal characters.

    Args:
        filename (str): The string to sanitize

    Returns:
        str: A sanitized string safe for use as a filename
    """
    # Define illegal characters
    # Windows reserved characters: < > : " / \ | ? *
    # Unix/Linux usually only forbids / and null
    # Also remove control characters
    illegal_chars = '<>:"/\\|?*\0'
    control_chars = "".join(map(chr, list(range(0, 32))))

    # Create a translation table
    translation_table = str.maketrans(
        illegal_chars + control_chars,  # Characters to replace
        "_" * len(illegal_chars + control_chars),  # Replace with underscores
        "",  # Characters to remove (none in this case)
    )

    # Clean the filename
    cleaned = filename.translate(translation_table)

    # Remove leading/trailing spaces and dots
    cleaned = cleaned.strip(". ")

    # Replace multiple underscores with a single one
    cleaned = re.sub(r"_+", "_", cleaned)

    # Handle empty string or all illegal characters
    if not cleaned:
        cleaned = "unnamed_file"

    # Handle Windows reserved names (CON, PRN, AUX, NUL, COM1-9, LPT1-9)
    reserved_names = {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        "COM1",
        "COM2",
        "COM3",
        "COM4",
        "COM5",
        "COM6",
        "COM7",
        "COM8",
        "COM9",
        "LPT1",
        "LPT2",
        "LPT3",
        "LPT4",
        "LPT5",
        "LPT6",
        "LPT7",
        "LPT8",
        "LPT9",
    }

    name_without_ext = cleaned.split(".")[0].upper()
    if name_without_ext in reserved_names:
        cleaned = f"_{cleaned}"

    return cleaned
