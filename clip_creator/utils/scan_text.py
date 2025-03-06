import re
import math
from num2words import num2words
from collections import Counter
from datetime import datetime

from clip_creator.conf import CURSE_WORDS, LOGGER, RM_TIMESTAMP_REGEX, TIMESTAMP_REGEX, REDDIT_ACCRO_SUB, REGEX_FOR_UPDATE, REGEX_FOR_UPDATE_RM


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

def swap_words_numbers(text: str) -> str:
    """
    Swap numbers with words in a text.
    """
    words = text.split()
    for i, word in enumerate(words):
        if remove_non_numbers(word).isdigit() and remove_non_numbers(word) != "":
            text.replace(word, str(num2words(remove_non_numbers(word))) + find_gender_in_nums(word))
    return text
def remove_non_numbers(text: str) -> str:
    """
    Removes all non-number characters from a string using regex.

    Args:
        text (str): The input string.

    Returns:
        str: A string containing only the digits from the original text.
    """
    return re.sub(r'[^\d\s]', '', text)
def find_gender_in_nums(text: str) -> str:
    match = re.search(r"\d+([a-zA-Z]+)", text)
    return match.group(1) if match else ""
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
            if "fuck" in word and "mother" not in word:
                text = text.replace("fuck", "frick")
            if "sex" in word:
                text = text.replace("sex", "seggs") 
            elif curse_word == remove_non_letters(word.lower()):
                text = text.replace(word, "beep")
    return text

def remove_non_letters(text):
    """Removes all non-letter characters from a string using regex.

    Args:
        text: The input string.

    Returns:
        The string with only letters.
    """
    return re.sub(r'[^a-zA-Z0-9 ]', '', text)
def reddit_acronym(text: str) -> str:
    """
    Replace acronyms in a text.
    """
    for acronym, full in REDDIT_ACCRO_SUB.items():
        for word in text.split(" "):
            if acronym.upper() == remove_non_letters(word):
                LOGGER.info("replace %s with %s", word, full)
                text = text.replace(word, full)
    return text
def dirty_remove_cuss(text:str)->str:
    for cuss in CURSE_WORDS:
        if "fuck" in cuss:
            text.replace("fuck", "frick")
        text = text.replace(cuss, "beep")
    return text
def get_top_posts(posts, n):
    sorted_items = sorted(posts.items(), key=lambda item: item[1]['upvotes'], reverse=True)
    update_set: set = set()
    for update_check in sorted_items[:n]:
        if "update" in update_check[1]['title'].lower() and (not update_check[1].get("parent_post_id", None) or update_check[1].get("parent_post_id", None)==""):
            sorted_items.remove(update_check)
        elif update_check[1].get("parent_post_id", None):
            update_set_mini = set(update_check)
            for post in sorted_items:
                if post[0] == update_check[1].get("parent_post_id", None) or update_check[0] == post[1].get("parent_post_id", None):
                    update_set_mini.add(post)
            update_set.add(update_set_mini)
    most_upvoted = 0
    update_list = []
    for update in update_set:
        current_upvoted = 0
        for post in update:
            current_upvoted += post[1]['upvotes']
        if current_upvoted > most_upvoted:
            update_list = list(update)
            
    update_list_sorted = sorted(update_list, key=lambda x: datetime.fromisoformat(x[1]['posted_at'].replace('Z', '+00:00')))
    
    if len(update_list_sorted) > 0 and len(update_list_sorted) < n:
        for post in update_list_sorted:
            sorted_items.remove(post)
        return dict(update_list_sorted + sorted_items[:n-len(update_list_sorted)])
    elif len(update_list_sorted) > n:
        for post in update_list_sorted:
            sorted_items.remove(post)
        return dict(sorted_items[:n])
    if len(update_list_sorted) == n:
        return dict(update_list_sorted)
    return dict(sorted_items[:n])
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
def sort_and_loop_by_max_int_key(data:list[dict]) -> list[dict]:

    """
    Sorts a list of dictionaries by the 'score' key in descending order and loops through it.

    Args:
        data: A list of dictionaries, where each dictionary has a 'score' key with an integer value.
    """
    
    sorted_data = sorted(data, key=lambda x: x.get('score', 0), reverse=True) #default to 0 if score isn't there

    return sorted_data

def reg_get_og(text:str, title:str):
    '''
    Gets all links in text that lead to another post
    They need to be changed to rel links
    '''
    if not text or text == "":
        return [], text
    with open("clip_creator/utils/banned.txt") as f:
        banned = f.read().split("\n")
    for ban in banned:
        if ban in title:
            return [], None
    matches = re.findall(REGEX_FOR_UPDATE, text)
    if not matches:
        if "https" in text or "http" in text or "www" in text or ".com" in text:
            return [], None
    if "update" in title.lower() or "original" in text:
        rm_matches = re.findall(REGEX_FOR_UPDATE_RM, text)
        for match in rm_matches:
            text = text.replace(match, "")
        list_matches = [match for match in matches]
        return ([] if not matches else list_matches), text
    
    
        
    return [], text

def split_audio(duration, aligned_transcript):
    """
    Splits an audio duration into aligned_transcript with lengths between 61 and 122 seconds.
    Finds the closest start times from a list of aligned_transcript.

    Args:
        duration: The total duration of the audio in seconds (float).
        aligned_transcript: A list of dictionaries, where each dictionary has a 'start' key (float).

    Returns:
        A list of indices from the 'aligned_transcript' list that are closest to the split points.
    """

    if duration <= 0:
        return []

    if duration <= 122:
        return [0] if aligned_transcript else []

    num_parts = math.ceil(duration / 61)  # Maximum possible parts
    part_duration = duration / num_parts

    if part_duration > 122:
        num_parts = math.floor(duration / 122)
        part_duration = duration / num_parts

    split_times = [part_duration * i for i in range(num_parts + 1)]

    closest_indices = []
    for split_time in split_times:
        min_diff = float('inf')
        closest_index = -1
        for i, segment in enumerate(aligned_transcript):
            diff = abs(segment['start'] - split_time)
            if diff < min_diff:
                min_diff = diff
                closest_index = i
        closest_indices.append(closest_index)
    
    return closest_indices