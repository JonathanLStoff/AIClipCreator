import re
from clip_creator.conf import LOGGER, TIMESTAMP_REGEX
from collections import Counter
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
    text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
    words = text.split()

    # 2. Count n-grams:
    ngram_counts = Counter()
    for i in range(len(words)):
        for j in range(1, min(n, len(words) - i) + 1):  # Iterate through ngram sizes
            ngram = " ".join(words[i:i + j])
            ngram_counts[ngram] += 1

    # 3. Find the most common n-grams:
    most_common = {}
    for i in range(1, n + 1):
        most_common[f"{i}-gram"] = {} #Initialize to empty strings
        for ngram, count in ngram_counts.most_common():
            if len(ngram.split()) == i:
                most_common[f"{i}-gram"]["word"] = ngram
                most_common[f"{i}-gram"]["count"] = count
                break #Break after finding the first most common ngram of this length

    return most_common[f"{i}-gram"]["word"], most_common[f"{i}-gram"]["count"]

def find_timestamps(text: str):
    '''
    Find timestamp in a text only if exactly one timestamp is found, otherwise returns None.
    '''
    timestamps = []
    for match in re.finditer(TIMESTAMP_REGEX, text):
        timestamps.append(match.group())
    return timestamps[0] if len(timestamps) == 1 else None
def convert_timestamp_to_seconds(timestamp: str)->int|None:
    '''
    Convert timestamp in the format "HH:MM:SS" to seconds.
    '''
    timestamp_part = ""
    for t in timestamp.split(" "):
        if ":" in t:
            timestamp_part = t
            break
    seconds = timestamp_part.split(':')[-1]
    minutes = timestamp_part.split(':')[-2]
    hours = 0 if len(timestamp_part.split(':')) < 3 else timestamp_part.split(':')[-3]
    try:
        return int(hours) * 3600 + int(minutes) * 60 + int(seconds)
    except ValueError:
        LOGGER.error("Invalid timestamp format: %s", timestamp)
    return None
def find_timestamp_clips(raw_transcript: list, timestamp:int)->list[dict]:
    '''
    Find timestamp in a text only if exactly one timestamp is found, otherwise returns None.
    snippet from raw_transcript: {'text': 'out our other man outs right over here', 'start': 1060.84, 'duration': 3.52}
    
    output: [{'text': str, 'start': float, 'duration': float}]
    '''
    clip = []
    item_index = 0
    for i, section in enumerate(raw_transcript):
        if int(section['start']) > timestamp:
            break
        item_index = i
        
    for i, section in enumerate(raw_transcript):
        if i >= item_index and section['start'] < timestamp + 61:
            clip.append(section)
    return clip
