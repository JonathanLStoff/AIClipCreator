import math
import re
from collections import Counter
from datetime import UTC, datetime
import traceback

from num2words import num2words

from clip_creator.conf import (
    CURSE_WORDS,
    LOGGER,
    REDDIT_ACCRO_SUB,
    REGEX_FOR_UPDATE,
    REGEX_FOR_UPDATE_RM,
    REPLACE_CURSE_WORDS_DIRT,
    REPLACE_WORDS_CLEAN,
    RM_TIMESTAMP_REGEX,
    TIMESTAMP_REGEX,
    SUB_MULTIPLY
)


def remove_markdown_links_images(text):
    """Removes markdown links and images from a string, keeping the link text."""
    link_pattern = r"\[([^\]]+)\]\(([^)]+)\)"
    image_pattern = r"!\[([^\]]*)\]\(([^)]+)\)"  # Added pattern for images

    # Remove links, keeping the link text (group 1)
    text_without_links = re.sub(link_pattern, r"\1", text)

    # Remove images (we don't keep any alt text for images in this case)
    text_without_media = re.sub(image_pattern, "", text_without_links)

    return text_without_media

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
    
    new_text = ""
    pattern_through = r"[\d,.]+-[\d,.]+"
    if re.search(pattern_through, text):
        for matchy in re.finditer(pattern_through, text):
            fixed_match = matchy.group().replace("-", " through ")
            text = text.replace(matchy.group(), fixed_match)
    words = text.split()
    last_dollar = False
    for _i, word in enumerate(words):
        
        if remove_non_numbers(word) != "":
            LOGGER.debug("maubbe Replacing %s", remove_non_numbers(word))
            LOGGER.debug(remove_non_numbers(word).isdigit())
            
            if remove_non_numbers(word).isdigit() and len(remove_non_numbers(word)) < 10:
                if ":" not in word:
                    try:
                        strings_word = re.sub(r"[\d,]+", " ", word)
                        pattern = r"[\d,]+\.\d+"
                        LOGGER.debug(
                            "Replacing %s %s",
                            str(remove_non_numbers(word)),
                            str(num2words(remove_non_numbers(word))),
                        )
                        if "- " in strings_word:
                            strings_word = strings_word.replace("-", "negative")
                            
                        if " th" in strings_word or " st" in strings_word or " nd" in strings_word or " rd" in strings_word:
                            new_word = strings_word.replace(
                                " ", str(num2words(word)) + " "
                            )
                            LOGGER.debug("th: %s", new_word)
                        
                        elif "$" in word or last_dollar:
                            if re.search(pattern, word):
                                dol_split = word.split(".")
                                LOGGER.debug("Dollar split: %s", dol_split)
                                new_word = strings_word.replace("$", "").replace(" . ", " ").replace(
                                    " ", str(num2words(remove_non_numbers(dol_split[0]))) + " dollars and " + str(num2words(remove_non_numbers(dol_split[1]))) + " cents "
                                )
                            else:
                                new_word = strings_word.replace("$", "").replace(
                                    " ", str(num2words(remove_non_numbers(word))) + " dollars "
                                )
                            LOGGER.debug("$: %s", new_word)
                            last_dollar = not last_dollar
                        else:

                            if re.search(r"\d+k", word):
                        
                                new_word = quick_replace(word, strings_word.replace("k", "thousand "))
                                
                                LOGGER.debug("k: %s", new_word)
                            elif re.search(r"\d+m" , word):
                                new_word = quick_replace(word, strings_word.replace('mil', "million "))
                                
                                LOGGER.debug("m: %s", new_word)
                            elif re.search(r"\d+b" , word):
                                new_word = quick_replace(word, strings_word.replace('b', "billion "))
                            
                                LOGGER.debug("b: %s", new_word)
                            elif re.search(r"\d+km", word):
                                new_word = quick_replace(word, strings_word.replace("km", "kilometers "))
                            else:
                                new_word = quick_replace(word, strings_word)
                            LOGGER.debug("km: %s", new_word)
                            try:
                                if len(remove_non_numbers(word)) == 4 and "thousand" in new_word:
                                    if 3000 > int(remove_non_numbers(word)) > 1300:
                                        new_word = strings_word.replace(
                                            " ",
                                            str(num2words(remove_non_numbers(word)[:2])) + " " + str(num2words(remove_non_numbers(word)[2:])) + " ",
                                            )
                            except Exception as e:
                                LOGGER.error("Error year: %s", e)
                                LOGGER.error("Word: %s", word)
                        LOGGER.debug("New word: %s", new_word)
                        new_text += new_word
                    except Exception as e:
                        LOGGER.error("Error converting to number1: %s", traceback.format_exc())
                        LOGGER.error("Word: %s", word)
                        new_text += word + " "
                else:
                    try:
                        # strings_word = re.sub(r"\d+", " ", word)
                        # LOGGER.debug(
                        #     "Replacing %s %s",
                        #     str(remove_non_numbers(word)),
                        #     str(num2words(remove_non_numbers(word))),
                        # )
                        # new_word = strings_word.replace(
                        #     " ",
                        #     " " + str(num2words(remove_non_numbers(word))) + "\n\n",
                        # )
                        # new_text += new_word
                        parts_words = word.split(":")
                        new_word = ""
                        for i, part in enumerate(parts_words):
                            if i < 2:
                                new_word += part.replace(
                                    " ", " " + str(num2words(part)) + " "
                                )
                            elif i == 2:
                                new_word += part.replace(
                                    " ", " , " + str(num2words(part)) + " seconds "
                                )
                            else:
                                LOGGER.error("The timestamp is too long: %s", word)
                        new_word += " O clock "
                    except Exception as e:
                        LOGGER.error("Error converting to number2: %s", e)
                        LOGGER.error("Word: %s", word)
            else:
                if "through" not in word:
                    last_dollar = False
                new_text += word + " "
        else:
            new_text += word + " "    
    return new_text
def quick_replace(word, strings_word: str) -> str:
    pattern = r"[\d,]+\.\d+"
    try:
        if re.search(pattern, word):
            dol_split = word.split(".")
            new_word = strings_word.replace(" . ", " ").replace(
                " ", " " + str(num2words(remove_non_numbers(dol_split[0]))) + " point " + str(num2words(remove_non_numbers(dol_split[1])))
            ) + " "
        else:
            new_word = strings_word.replace(
                " ",
                " " + str(num2words(remove_non_numbers(word))) + " ",
                )+ " "
    except Exception as e:
        LOGGER.error("Error converting to number3: %s", e)
        LOGGER.error("Word: %s", word)
        new_word = word
    return new_word
def remove_non_letterstwo(text):
  """Removes all non-letter characters from a string.

  Args:
    text: The input string.

  Returns:
    The string with only letters.
  """
  return re.sub(r'[^0-9a-zA-Z]+', '', text)

def remove_non_numbers(text: str) -> str:
    """
    Removes all non-number characters from a string using regex.

    Args:
        text (str): The input string.

    Returns:
        str: A string containing only the digits from the original text.
    """
    return re.sub(r"[^\d\s]", "", text)


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
    compiled_test = ""
    
    # after building compiled_test, clean up starred phrases
    
    pat_ern = r'[*][*]?[tT][iI][tT][lL][eE][:]?[*][*]?'
    o_pat_ern = r'[*][*]?[Oo][Rr][Ii][Gg][Ii][Nn][Aa][Ll][:]?[*][*]?\N+\n'
    oo_pat_ern = r'[*]+I am NOT the Original Poster[\w\W]*[*][*]?[Oo][Rr][Ii][Gg][Ii][Nn][Aa][Ll][:]?[*][*]?.+\n' #r'[*][*]?[Ii]\s[Aa][Mm]\s[Nn][Oo][Tt]\s[Tt][Hh][Ee]\s[Oo][Rr][Ii][Gg][Ii][Nn][Aa][Ll][\n\W\w]+[*][*]?[Oo][Rr][Ii][Gg][Ii][Nn][Aa][Ll][:]?[*][*]?\N+\n'
    oop_pat_ern = r'[*]+I am not The OOP[\w\W]*[*][*]?[Oo][Rr][Ii][Gg][Ii][Nn][Aa][Ll][:]?[*][*]?.+\n'#
    if re.search(pat_ern, text):
        text = re.split(pat_ern, text)[-1]
        text = text.replace(":*", "")
        text = text.replace("*", "")
        text = text.replace(" ", " ")
    elif re.search(oo_pat_ern, text):
        text = re.sub(oo_pat_ern, "", text)
        text = text.replace(":*", "")
        text = text.replace("*", "")
        text = text.replace(" ", " ")
    elif re.search(oop_pat_ern, text):
        text = re.sub(oop_pat_ern, "", text)
        text = text.replace(":*", "")
        text = text.replace("*", "")
        text = text.replace(" ", " ")    
    _pattern = re.compile(r'(\W)\*(.*?)\*(\W)')
    def _unstar(match):
        inner = match.group(2)
        low = inner.lower()
        # skip if it mentions update, orginal, link or url
        if any(key in low for key in ('update', 'orginal', 'link', 'url')):
            return ""
        # otherwise drop the stars
        return f"{match.group(1)}{inner}{match.group(3)}"

    text = _pattern.sub(_unstar, text)
    for word in text.split():
        
        for replace_word, keep_word in REPLACE_WORDS_CLEAN.items():
            if word.lower() == replace_word:
                
                text = text.replace(word, keep_word)
    for word in text.split():
        for d_word, d_word_r in REPLACE_CURSE_WORDS_DIRT.items():
            if d_word in word.lower() and "mother" not in word.lower():
                if d_word.lower() in ['(', ')'] and remove_non_numbers(word).isdigit():
                    text = text.replace(d_word, "")
                else:
                    text = text.replace(d_word, d_word_r)
    for word in text.split():
        found_in_word = False
        found_cword = ""
        for curse_word in CURSE_WORDS:
            
            # Check
            for part_word in word.lower().split("-"):
                if remove_non_letters(part_word) == curse_word:
                    found_in_word = True
                    found_cword = curse_word
            if curse_word == remove_non_letters(word.lower()):
                found_in_word = True
                found_cword = curse_word
            # Replace    
        if not found_in_word:
            compiled_test += word + " "
        else:
            wordy = word.replace(found_cword, "beep")
            compiled_test += wordy + " "
            
    
    
    return compiled_test
def get_correct_chunk_end(chunks: dict, chunk_idx: int) -> float:
    """
    Get the correct chunk from a dictionary of chunks based on the chunk index.

    Args:
        chunks: A dictionary of chunks, where each key is a chunk index.
        chunk_idx: The index of the desired chunk.

    Returns:
        The chunk with the specified index, or an empty dictionary if the chunk is not found.
    """
    the_chunk = None
    for chunk in chunks.values():
        if chunk.get("idx") == chunk_idx:
            the_chunk = chunk
    return the_chunk.get("ascript", [])[-1]['end']

def remove_non_letters(text):
    """Removes all characters except letters, numbers, spaces, ? ! , . and newlines.

    Args:
        text: The input string.

    Returns:
        The string with only allowed characters.
    """
    text = text.replace("'", "")
    text = text.replace("’", "")
    text = text.replace("‘", "")
    text = text.replace("`", "")
    text = text.replace("´", "")
    text = text.replace("′", "")
    text = text.replace("‛", "")
    text = text.replace("‘", "")
    text = text.replace("’", "")
    text = text.replace("“", "")
    text = text.replace("”", "")
    return re.sub(r"[^a-zA-Z0-9 \?!,.'‘’‚`´′‛\n]", " ", text)


def reddit_acronym(text: str) -> str:
    """
    Replace acronyms in a text.
    """
    net_text = ""
    for word in text.split(" "):
        full_word = ""
        acro = ""
        for acronym, full in REDDIT_ACCRO_SUB.items():
            if acronym == remove_non_letters(word):
                #LOGGER.info("acronym %s found in %s", acronym, remove_non_letters(word))
                #LOGGER.info("replace %s with %s", word, full)
                acro = acronym
                full_word = full
        if acro != "":
            #LOGGER.info("replace %s with %s", word, full_word)
            net_text += word.replace(remove_non_letters(word), full_word) + " "
        else:
            net_text += word + " "
    new_text = ""
    for word in net_text.split(" "):
        found_in_word = False
        word_found = ""
        for accro, full in REPLACE_WORDS_CLEAN.items():
        
            if accro.lower() == word.lower():
                #LOGGER.info("replace %s with %s", word, full)
                found_in_word = True
                word_found = full
        if found_in_word:
            new_text += word_found + " "
        else:
            new_text += word + " "
            
    return new_text


def get_id_from_vfile(file: str) -> str | None:
    for i, part in enumerate(file.replace(".mp4", "").split("_")):
        if i != 0:
            if len(part) >= 6 and part.lower() != "reddit":
                return str(part)
    return None


def dirty_remove_cuss(text: str) -> str:
    if not text or text == "":
        return ""
    for cuss in CURSE_WORDS:
        if "fuck" in cuss:
            text.replace("fuck", "frick")
        text = text.replace(cuss, "beep")
    return text

def contains_number(text):
    return bool(re.search(r'\d', text))

def get_first_number(text):
    match = re.search(r'\d+', text)
    return int(match.group()) if match else None

def fix_update_order(text: str) -> str:
    '''Reddit updates are weird'''
    text_split = text.split("\-")
    re_ordered = text_split.copy()
    for i, part in enumerate(text_split):
        if part.lower().strip().startswith("update"):
            re_ordered.pop(i)
            re_ordered.append(part)
    last_no_update = 0
    new_re_ordered = re_ordered.copy()
    for i, part in enumerate(re_ordered):
        if part.lower().strip().startswith("update") and contains_number(part.lower().split("\n")[0].strip()):
            part_num = get_first_number(part.lower().split("\n")[0].strip())
            if part_num + last_no_update <= len(new_re_ordered):
                new_re_ordered.insert(part_num + last_no_update, part)
            else:
                new_re_ordered.remove(part)
                new_re_ordered.append(part)
        else:
            last_no_update = i
    return "\n".join(new_re_ordered)
def get_top_posts(posts, n):
    for pid, post in posts.items():
        for sub, multi in SUB_MULTIPLY.items():
            if sub.lower() in post["url"].lower():
                posts[pid]["ad_upvotes"] = posts[pid]["upvotes"] * multi
        if not posts[pid].get("ad_upvotes"):
            posts[pid]["ad_upvotes"] = posts[pid]["upvotes"]
            LOGGER.error("No ad upvotes for %s", post['url'])
    sorted_items = sorted(
        posts.items(), key=lambda item: item[1]["ad_upvotes"], reverse=True
    )
    post_to_remove = []
    for post in sorted_items:
        if post[1]["upvotes"] < post[1]["comments"]:
            post_to_remove.append(post)
    for post in post_to_remove:
        sorted_items.remove(post)
    update_set: set = set()
    for update_check in sorted_items[:n]:
        if "update" in remove_markdown_links_images(update_check[1]["title"]).lower() and (
            update_check[1].get("parent_post_id", None) is None
            or update_check[1].get("parent_post_id", None) == ""
        ):
            sorted_items.remove(update_check)
        elif update_check[1].get("parent_post_id", None):
            update_set_mini = set(update_check)
            for post in sorted_items:
                if post[0] == update_check[1].get(
                    "parent_post_id", None
                ) or update_check[0] == post[1].get("parent_post_id", None):
                    update_set_mini.add(post)
            update_set.add(update_set_mini)
    most_upvoted = 0
    update_list = []
    for update in update_set:
        current_upvoted = 0
        for post in update:
            current_upvoted += post[1]["upvotes"]
        if current_upvoted > most_upvoted:
            update_list = list(update)

    update_list_sorted = sorted(
        update_list,
        key=lambda x: datetime.fromisoformat(x[1]["posted_at"].replace("Z", "+00:00")),
    )
    if False:
        if len(update_list_sorted) > 0 and len(update_list_sorted) < n:
            for post in update_list_sorted:
                sorted_items.remove(post)
            return dict(update_list_sorted + sorted_items[: n - len(update_list_sorted)])
        elif len(update_list_sorted) > n:
            for post in update_list_sorted:
                sorted_items.remove(post)
            return dict(sorted_items[:n])
        if len(update_list_sorted) == n:
            return dict(update_list_sorted)
    else:
        try:
            for post in update_list_sorted:
                sorted_items.remove(post)
            items_to_remove = []
            for post in sorted_items:
                if "update" in post[1]["title"].lower() or "original" in post[1]["title"].lower():
                    items_to_remove.append(post)
            for post in items_to_remove:
                sorted_items.remove(post)
        except Exception as e:
            LOGGER.error("Error removing post: %s", e)
            LOGGER.error("Post: %s", post)
    return dict(sorted_items[:n])


def get_top_posts_coms(posts:dict, n):

    for pid, post in posts.items():
        if post["upvotes"] < post["comments"]:
            posts[pid]["upvotes"] = posts[pid]["upvotes"] - post["comments"]
    return [
        key
        for key, _ in sorted(
            posts.items(), key=lambda item: item[1].get("upvotes", 0), reverse=True
        )[:n]
    ]

def get_top_posts_aiyt(posts:dict, n):

    
    return [
        key
        for key, _ in sorted(
            posts.items(), key=lambda item: item[1].get("views", 0), reverse=True
        )[:n]
    ]
def find_bad_words(
    true_transcript: list[dict], uncensored_transcript
) -> (list[list[int]], list[dict]):
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
                + int(float(word_dict.get("duration", 1) + 0.5) * 1000),
            ])
            word_dict["text"] = "*" * len(word)
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
            word_dict["text"] = "*" * len(word)
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


def sort_and_loop_by_max_int_key(data: list[dict]) -> list[dict]:
    """
    Sorts a list of dictionaries by the 'score' key in descending order and loops through it.

    Args:
        data: A list of dictionaries, where each dictionary has a 'score' key with an integer value.
    """

    sorted_data = sorted(
        data, key=lambda x: x.get("score", 0), reverse=True
    )  # default to 0 if score isn't there

    return sorted_data


def sort_and_loop_by_max_int_key_coms(data: list[dict]) -> list[dict]:
    """
    Sorts a list of dictionaries by the 'score' key in descending order and loops through it.

    Args:
        data: A list of dictionaries, where each dictionary has a 'score' key with an integer value.
    """

    sorted_data = sorted(
        data, key=lambda x: x.get("upvotes", 0), reverse=True
    )  # default to 0 if score isn't there

    return sorted_data


def reg_get_og(text: str, title: str):
    """
    Gets all links in text that lead to another post
    They need to be changed to rel links
    """
    if not text or text == "":
        return [], text
    with open("clip_creator/utils/banned.txt") as f:
        banned = f.read().split(",")
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
        list_matches = list(matches)
        return ([] if not matches else list_matches), text

    return [], text


def replace_word_ignoring_punctuation(text, old_word, new_word):
    """
    Replaces a word in a text if it is equal to another word,
    ignoring punctuation when checking equality, and keeping
    punctuation after replacing.

    Args:
        text: The input text.
        old_word: The word to be replaced.
        new_word: The word to replace with.

    Returns:
        The text with the word replaced.
    """

    # Remove punctuation from old_word for comparison
    old_word_no_punct = re.sub(r"[^\w\s]", "", old_word)

    # Define a regular expression pattern to match the word with optional punctuation
    pattern = r"\b" + re.escape(old_word_no_punct) + r"([.,!?;:]*)"

    # Replace the word with the new word, keeping the original punctuation
    return re.sub(pattern, new_word + r"\1", text)


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
    split_times.append(0)
    closest_indices = []
    for split_time in split_times:
        min_diff = float("inf")
        closest_index = -1
        for i, segment in enumerate(aligned_transcript):
            diff = abs(segment["start"] - split_time)
            if diff < min_diff:
                min_diff = diff
                closest_index = i
        closest_indices.append(closest_index)

    return closest_indices


def str_to_datetime(datetime_str):
    """
    Converts a datetime string in the format "%Y-%m-%dT%H:%M:%S.%f+0000" to a datetime object.

    Args:
        datetime_str: The datetime string to convert.

    Returns:
        A datetime object, or None if the string is invalid.
    """
    try:
        dt_object = datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%S.%f+0000")
        # Ensure the datetime object is timezone-aware and in UTC:
        return dt_object.replace(tzinfo=UTC)
    except ValueError:
        return None
