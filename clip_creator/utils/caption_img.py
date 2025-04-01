import logging
import os
import random
import time
import traceback
from datetime import UTC, datetime, timedelta
from queue import Queue
from random import choice, randint
from threading import Thread

from PIL import Image, ImageDraw, ImageFont
from pilmoji import Pilmoji
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm
from webdriver_manager.chrome import ChromeDriverManager

from clip_creator.conf import (
    COLOR_PAIRS,
    COLORS,
    CURSE_WORDS,
    E_FONT_PATH,
    FONT_PATH,
    LOGGER,
)
from clip_creator.utils.scan_text import dirty_remove_cuss, reddit_remove_bad_words, reddit_acronym
import re


def remove_curse_words(text: str) -> str:
    """
    Removes curse words from a given text.
    """
    # LOGGER.info("Removing curse words from text. %s", text)
    for curse_word in CURSE_WORDS:
        if isinstance(text, list):
            tmp_txt = []
            for word_d in text:
                if curse_word == word_d.get("text", "").lower():
                    word_d["text"] = "*" * len(curse_word)
                tmp_txt.append(word_d)
            text = tmp_txt
        elif isinstance(text, str):
            if curse_word in text.lower():
                tmp_txt = ""
                for word in text.split():
                    tmp_txt += (
                        "*" * len(curse_word) if curse_word == word.lower() else word
                    )
                    tmp_txt += " "
                text = tmp_txt.strip()

    return text


def create_caption_images(prefix: str, captions, max_width, output_dir="."):
    """Creates one image *per line* of wrapped text, highlighting current word.

    caption: List of dictionaries with "start" and "text" keys.
    """
    try:
        font = ImageFont.truetype(FONT_PATH, size=100)
    except Exception as e:
        print(f"Error loading font: {e}. Trying default.")
        try:
            font = ImageFont.load_default()
        except Exception as e2:
            print(f"Error loading default font: {e2}. Please install a font.")
            return

    h_padding = 30
    padding = 30
    word_spacing = 20
    outline_width = 20
    lines_text: list[list[dict]] = [[]]
    lines_index = 0

    # Find each line of text
    for i, caption in tqdm(
        enumerate(captions), total=len(captions), desc="Find each line of text"
    ):
        lines_text[lines_index].append({"text": caption.get("text", ""), "index": i})
        temp_x = h_padding
        # Create a dummy image and draw context for calculations
        dummy_img = Image.new("RGBA", (max_width * 2, max_width), color=(0, 0, 0, 0))
        dummy_draw = ImageDraw.Draw(dummy_img)

        # Build up the current line using dummy context
        for word in lines_text[lines_index]:
            bbox = dummy_draw.textbbox(
                (0, padding), word.get("text", ""), font=font, align="center"
            )
            word_width = bbox[2] - bbox[0]
            temp_x += word_width + word_spacing

        if temp_x > max_width - h_padding and len(lines_text[lines_index]) > 0:
            lines_text[lines_index].pop(-1)
            lines_index += 1
            lines_text.append([{"text": caption.get("text", ""), "index": i}])
        if (
            "." in caption.get("text", "")
            or "!" in caption.get("text", "")
            or "?" in caption.get("text", "")
        ):
            lines_index += 1
            lines_text.append([])

    # Process each line
    for j, line in tqdm(
        enumerate(lines_text), total=len(lines_text), desc="Create Images"
    ):
        img = Image.new("RGBA", (max_width * 2, max_width), color=(0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        line = remove_curse_words(line)
        # Calculate line heights
        max_ascent = 0
        max_descent = 0
        for word in line:
            bbox = draw.textbbox(
                (0, padding), word.get("text"), font=font, align="center"
            )
            ascent = padding - bbox[1]
            descent = bbox[3] - padding
            max_ascent = max(max_ascent, ascent)
            max_descent = max(max_descent, descent)
        total_height = max_ascent + max_descent

        # Create final image
        new_width = max_width
        new_height = total_height + 2 * padding
        final_img = Image.new("RGBA", (new_width, new_height), color=(0, 0, 0, 0))
        final_draw = ImageDraw.Draw(final_img)

        # Calculate word widths and total line width
        word_widths = []
        total_line_width = 0
        for word in line:
            bbox = final_draw.textbbox(
                (0, padding), word.get("text"), font=font, align="center"
            )
            w = bbox[2] - bbox[0]
            word_widths.append(w)
            total_line_width += w

        if len(line) > 1:
            total_line_width += word_spacing * (len(line) - 1)
        ran_check = randint(1, 10)
        word_to_change = None
        word_to_change_color = None
        if ran_check < 2 and len(line) > 1:
            word_to_change = randint(0, len(line) - 1)
            word_to_change_color = choice(list(COLOR_PAIRS["white"]))
            bg_choiced_color = "white"
            paired = "red"
        if ran_check < 3:
            bg_choiced_color = choice(list(COLOR_PAIRS.keys()))
            paired = choice(COLOR_PAIRS[bg_choiced_color])
        elif ran_check < 5:
            bg_choiced_color = "white"
            paired = choice(COLOR_PAIRS[bg_choiced_color])
        else:
            bg_choiced_color = "white"
            paired = "red"
        # Generate an image for each word in the line
        for i, caption_ult in enumerate(line):
            word_index = caption_ult.get("index", "")
            x = (new_width - total_line_width) // 2
            current_y = padding

            # Draw each word in the line
            for k, caption in enumerate(line):
                word = caption.get("text", "")
                color = COLORS[paired] if k == i else COLORS[bg_choiced_color]
                if word_to_change == k:
                    color = COLORS[word_to_change_color]
                # Draw outline
                for dx in range(-outline_width, outline_width + 1):
                    for dy in range(-outline_width, outline_width + 1):
                        final_draw.text(
                            (x + dx, current_y + dy),
                            word,
                            font=font,
                            fill="black",
                            align="center",
                        )

                # Draw text
                final_draw.text(
                    (x, current_y), word, font=font, fill=color, align="center"
                )
                # Key fix: Use k instead of i for word_widths index
                x += word_widths[k] + word_spacing

            filename = f"{prefix}_line{j}_word{word_index}.jpg"
            file_path = os.path.join(output_dir, filename)

            final_img.convert("RGB").save(file_path, "JPEG", quality=70)
            # print(f"Saved {file_path}")


def create_caption_images_reddit(
    prefix: str,
    captions,
    max_width,
    output_dir=".",
    part=0
):
    """Creates one image *per word* of wrapped text, highlighting current word.

    caption: List of dictionaries with "start" and "text" keys.
    """
    try:
        font = ImageFont.truetype(FONT_PATH, size=100)
    except Exception as e:
        print(f"Error loading font: {e}. Trying default.")
        try:
            font = ImageFont.load_default()
        except Exception as e2:
            print(f"Error loading default font: {e2}. Please install a font.")
            return

    h_padding = 20
    padding = 20
    max_width = max_width - padding
    word_spacing = 15
    outline_width = 5
    lines_text: list[list[dict]] = [[]]
    lines_index = 0

    # Find each line of text
    for i, caption in tqdm(
        enumerate(captions),
        total=len(captions),
        desc="Find each line of text"
    ):
        lines_text[lines_index].append({"text": caption.get("real_text", caption.get("text", "")), "index": i})
        temp_x = h_padding

        # Create a dummy image and draw context for calculations
        dummy_img = Image.new("RGBA", (max_width * 2, max_width), color=(0, 0, 0, 0))
        dummy_draw = ImageDraw.Draw(dummy_img)

        # Build up the current line using dummy context
        for word in lines_text[lines_index]:
            bbox = dummy_draw.textbbox(
                (0, padding),
                word.get("text", ""),
                font=font,
                align="center"
            )
            word_width = bbox[2] - bbox[0]
            temp_x += word_width + word_spacing


        lines_index += 1
        lines_text.append([])

    # Process each line
    for j, line in tqdm(
        enumerate(lines_text),
        total=len(lines_text),
        desc="Create Images"
    ):
        line = remove_curse_words(line)
        # Calculate line heights
        max_ascent = 0
        max_descent = 0
        for word in line:
            dummy_img = Image.new("RGBA", (max_width * 2, max_width), color=(0, 0, 0, 0))
            dummy_draw = ImageDraw.Draw(dummy_img)
            bbox = dummy_draw.textbbox(
                (0, padding),
                word.get("text"),
                font=font,
                align="center"
            )
            ascent = padding - bbox[1]
            descent = bbox[3] - padding
            max_ascent = max(max_ascent, ascent)
            max_descent = max(max_descent, descent)
        total_height = max_ascent + max_descent

        # Calculate word widths and total line width
        word_widths = []
        total_line_width = 0
        for word in line:
            dummy_img = Image.new("RGBA", (max_width * 2, max_width), color=(0, 0, 0, 0))
            dummy_draw = ImageDraw.Draw(dummy_img)
            bbox = dummy_draw.textbbox(
                (0, padding),
                word.get("text"),
                font=font,
                align="center"
            )
            w = bbox[2] - bbox[0]
            word_widths.append(w)
            total_line_width += w

        if len(line) > 1:
            total_line_width += word_spacing * (len(line) - 1)

        # Generate an image for each word in the line
        for i, caption_ult in enumerate(line):
            new_width = max_width
            new_height = total_height + 2 * padding
            final_img = Image.new("RGBA", (new_width, new_height), color=(0, 0, 0, 0))
            final_draw = ImageDraw.Draw(final_img)

            word_index = caption_ult.get("index", "")
            x = (new_width - total_line_width) // 2
            current_y = padding

            ran_check = randint(1, 10)
            word_to_change = None
            word_to_change_color = None
            if ran_check < 2 and len(line) > 1:
                word_to_change = randint(0, len(line) - 1)
                word_to_change_color = choice(list(COLOR_PAIRS["white"]))
                bg_choiced_color = "white"
                paired = "red"
            if ran_check < 3:
                bg_choiced_color = choice(list(COLOR_PAIRS.keys()))
                paired = choice(COLOR_PAIRS[bg_choiced_color])
            elif ran_check < 5:
                bg_choiced_color = "white"
                paired = choice(COLOR_PAIRS[bg_choiced_color])
            else:
                bg_choiced_color = "white"
                paired = "red"

            # Draw each word in the line
            for k, caption in enumerate(line):
                wordt: str = caption.get("text", "")
                # We only have one word a line so we can use any color, will give us a higher chance of white while still being random
                color = choice([COLORS[paired], COLORS[bg_choiced_color], "white"])
                if word_to_change == k:
                    color = COLORS[word_to_change_color]
                # Draw outline
                for dx in range(-outline_width, outline_width + 1):
                    for dy in range(-outline_width, outline_width + 1):
                        final_draw.text(
                            (x + dx, current_y + dy),
                            (str(wordt) + " ") if len(line) > k + 1 else wordt,
                            font=font,
                            fill="black",
                            align="center",
                        )

                # Draw text
                final_draw.text(
                    (x, current_y),
                    (str(wordt) + " ") if len(line) > k + 1 else wordt,
                    font=font,
                    fill=color,
                    align="center",
                )
                # Key fix: Use k instead of i for word_widths index
                x += word_widths[k] + word_spacing

            filename = f"{prefix}_line{j}_word{word_index}-{part}.png"
            file_path = os.path.join(output_dir, filename)

            final_img.save(file_path, "PNG")


def create_caption_images_reddit_com(
    prefix: str, num: int, max_width, output_dir="./tmp/caps_img", part=0
):
    """Creates one image *per line* of wrapped text, highlighting current word.

    caption: List of dictionaries with "start" and "text" keys.
    """
    try:
        font = ImageFont.truetype(FONT_PATH, size=150)
    except Exception as e:
        print(f"Error loading font: {e}. Trying default.")
        try:
            font = ImageFont.load_default()
        except Exception as e2:
            print(f"Error loading default font: {e2}. Please install a font.")
            return

    h_padding = 20
    padding = 20
    max_width = max_width - padding
    word_spacing = 15
    outline_width = 5

    final_img = Image.new("RGBA", (max_width, int(max_width / 2)), color=(0, 0, 0, 0))
    # Calculate line heights
    # Create final image
    final_draw = ImageDraw.Draw(final_img)

    # Calculate word widths and total line width
    word_widths = []
    total_line_width = 0
    bbox = final_draw.textbbox((0, padding), str(num) + ".", font=font, align="center")
    w = bbox[2] - bbox[0]
    word_widths.append(w)
    total_line_width += w

    ran_check = randint(1, 10)

    if ran_check < 3:
        bg_choiced_color = choice(list(COLOR_PAIRS.keys()))
        paired = choice(COLOR_PAIRS[bg_choiced_color])
    elif ran_check < 5:
        bg_choiced_color = "white"
        paired = choice(COLOR_PAIRS[bg_choiced_color])
    else:
        bg_choiced_color = "white"
        paired = "red"
    # Generate an image for each word in the line
    x = (max_width - total_line_width) // 2
    current_y = int(max_width / 4)

    # Draw each word in the line
    wordt: str = str(num) + "."
    color = COLORS[bg_choiced_color]
    # Draw outline
    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            final_draw.text(
                (x + dx, current_y + dy),
                wordt,
                font=font,
                fill="black",
                align="center",
            )

    # Draw text
    final_draw.text((x, current_y), wordt, font=font, fill=color, align="center")
    # Key fix: Use k instead of i for word_widths index

    filename = f"{prefix}_{num}line.png"
    file_path = os.path.join(output_dir, filename)

    final_img.save(file_path, "PNG")
    return file_path


def create_caption_images_thread(prefix: str, captions, max_width, output_dir="."):
    """Creates one image per line of wrapped text, highlighting current word using parallel processing."""
    os.makedirs(output_dir, exist_ok=True)

    try:
        font = ImageFont.truetype(FONT_PATH, size=100)
    except Exception as e:
        print(f"Error loading font: {e}. Trying default.")
        try:
            font = ImageFont.load_default()
        except Exception as e2:
            print(f"Error loading default font: {e2}. Please install a font.")
            return

    # Constants
    padding = 30
    word_spacing = 20
    outline_width = 7

    def process_image(task):
        """Worker function to process and save a single image."""
        (
            prefix,
            caption,
            current_word_idx,
            current_line,
            current_line_indices,
            start,
        ) = task

        words = caption.get("text", "").split()

        # Create an image to measure text height
        img = Image.new("RGBA", (max_width * 2, max_width), color=(0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Calculate maximum ascent and descent
        max_ascent = max_descent = 0
        for word in current_line:
            bbox = draw.textbbox((0, padding), word, font=font, align="center")
            ascent = padding - bbox[1]
            descent = bbox[3] - padding
            max_ascent = max(max_ascent, ascent)
            max_descent = max(max_descent, descent)

        total_height = max_ascent + max_descent

        # Create final image
        new_width = max_width
        new_height = total_height + 2 * padding
        final_img = Image.new("RGBA", (new_width, new_height), color=(0, 0, 0, 0))
        final_draw = ImageDraw.Draw(final_img)

        # Calculate word widths and total line width
        word_widths = []
        total_line_width = 0
        for word in current_line:
            bbox = final_draw.textbbox((0, padding), word, font=font, align="center")
            w = bbox[2] - bbox[0]
            word_widths.append(w)
            total_line_width += w

        if len(current_line) > 1:
            total_line_width += word_spacing * (len(current_line) - 1)

        # Center text horizontally
        x = (new_width - total_line_width) // 2
        current_y = padding

        # Draw each word
        for idx, word in enumerate(current_line):
            color = "red" if current_line_indices[idx] == current_word_idx else "white"

            # Draw outline
            for dx in range(-outline_width, outline_width + 1):
                for dy in range(-outline_width, outline_width + 1):
                    final_draw.text(
                        (x + dx, current_y + dy),
                        word,
                        font=font,
                        fill="black",
                        align="center",
                    )

            # Draw text
            final_draw.text((x, current_y), word, font=font, fill=color, align="center")
            x += word_widths[idx] + word_spacing

        # Save the image
        filename = f"{prefix}{start}_word{current_word_idx}.jpg"
        file_path = os.path.join(output_dir, filename)
        resized_img = final_img.resize((final_img.width // 2, final_img.height // 2), 1)
        resized_img.convert("RGB").save(file_path, "JPEG", quality=40)
        # print(f"Saved {file_path}")

    def worker():
        """Thread worker that processes tasks from the queue."""
        while True:
            task = task_queue.get()
            if task is None:
                break
            try:
                process_image(task)
            except Exception as e:
                print(f"Error processing image: {e}")
            finally:
                task_queue.task_done()

    # Create a queue and worker threads
    task_queue = Queue()
    num_threads = min(os.cpu_count() or 1, 4)  # Limit to 4 threads or CPU count
    threads = []

    for _ in range(num_threads):
        t = Thread(target=worker)
        t.start()
        threads.append(t)

    # Process captions and add tasks to queue
    for caption in captions:
        start = str(caption.get("start")).replace(".", "-")
        text = caption.get("text", "")
        words = text.split()

        for i, current_word in enumerate(words):
            current_word_index = 0

            while current_word_index < len(words):
                current_line = []
                current_line_indices = []

                # Calculate line wrapping using dummy image
                dummy_img = Image.new(
                    "RGBA", (max_width * 2, max_width), color=(0, 0, 0, 0)
                )
                dummy_draw = ImageDraw.Draw(dummy_img)

                temp_x = padding
                while current_word_index < len(words):
                    word = words[current_word_index]
                    bbox = dummy_draw.textbbox(
                        (0, padding), word, font=font, align="center"
                    )
                    word_width = bbox[2] - bbox[0]

                    if (
                        temp_x + word_width + word_spacing > max_width - padding
                        and len(current_line) > 0
                    ):
                        break

                    current_line.append(word)
                    current_line_indices.append(current_word_index)
                    temp_x += word_width + word_spacing
                    current_word_index += 1

                # If current word is in this line, add task to queue
                if current_word in current_line:
                    task_queue.put(
                        (prefix, caption, i, current_line, current_line_indices, start)
                    )

    # Add sentinel values to stop workers
    for _ in range(num_threads):
        task_queue.put(None)

    # Wait for all tasks to complete
    task_queue.join()

    # Wait for all threads to finish
    for t in threads:
        t.join()


def create_emojis(text: str, vid: str, w: int = 90, h: int = 90) -> str:
    """
    Creats image from emojis.
    args:
        text: str: text to convert to emojis
    return:
        str: image path
    """
    image_path = f"tmp/emojis_{vid}.png"
    with Image.new("RGBA", (w, h), (255, 255, 255, 0)) as image:
        font = ImageFont.truetype(E_FONT_PATH, 400)

        with Pilmoji(image) as pilmoji:
            pilmoji.text(
                xy=(0, 0), text=text.strip(), fill=None, align="center", font=font
            )
            image.save(image_path)
    return image_path


def render_html_to_png(
    post_id: str,
    title: str,
    subreddit: str,
    subreddit_id: str,
    user_id: str,
    user_name: str,
    time_ago: datetime,
    score_int: int = 0,
    comment_int: int = 0,
    lang: str = "en",
    output_png_fold: str = "./tmp",
    html_file: str = "clip_creator/utils/real_reddit.html",
):
    """
    Renders an HTML file with potential replacements to a PNG image.

    Args:
        html_file (str): Path to the input HTML file.
        output_png (str): Path to the output PNG file.
        replacements (dict, optional): Dictionary of replacements (key: old_string, value: new_string).
        *SUBREDDIT*
        *SUBREDDIT_ID*
        *USER_ID*
        *TIME_AGO* # "15 hr." ago
        *USER_NAME*
        *SCORE_INT*
        *COMMENT_INT*
        *SUB_IMG_PATH*
        *TITLE*
        *USER_IMG*
    """
    if lang == "en":
        output_png: str = f"{output_png_fold}/{post_id}_coms.png"
    else:
        output_png: str = f"{output_png_fold}/{post_id}_{lang}_coms.png"
    output_png_abs = os.path.abspath(output_png)
    html_file_abs = os.path.abspath(html_file)
    try:
        with open(html_file_abs, encoding="utf-8") as f:
            html_content = f.read()

        html_content = html_content.replace("*SUBREDDIT*", subreddit)
        html_content = html_content.replace("*SUBREDDIT_ID*", subreddit_id)
        html_content = html_content.replace("*USER_ID*", user_id)
        now = datetime.now(UTC)  # Might cause issues for time being off
        delta = now - time_ago
        years = delta.days // 365
        months = delta.days // 30
        days = delta.days
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60

        if years >= 1:
            time_diff = f"{years} year{'s' if years > 1 else ''}"
        elif months >= 1:
            time_diff = f"{months} month{'s' if months > 1 else ''}"
        elif days >= 1:
            time_diff = f"{days} day{'s' if days > 1 else ''}"
        elif hours >= 1:
            time_diff = f"{hours} hr"
        elif minutes >= 1:
            time_diff = f"{minutes} min"
        else:
            time_diff = "just now"
        img_path = os.path.join("clip_creator/utils/imgs", "amitheahole.png")
        for file in os.listdir("clip_creator/utils/imgs"):
            if file.startswith(subreddit):
                img_path = os.path.join("clip_creator/utils/imgs", file)
        html_content = html_content.replace("*TIME_AGO*", time_diff)
        if not user_name:
            user_name = "Unknown"
        html_content = html_content.replace("*USER_NAME*", ("u/" + user_name))
        html_content = html_content.replace("*SCORE_INT*", str(score_int))
        html_content = html_content.replace("*COMMENT_INT*", str(comment_int))
        html_content = html_content.replace("*SUB_IMG_PATH*", os.path.abspath(img_path))
        html_content = html_content.replace("*TITLE*", title)
        html_content = html_content.replace(
            "*USER_IMG*", os.path.abspath("clip_creator/utils/imgs/reddit.jpg")
        )
        with open("./tmp/real_reddit.html", "w", encoding="utf-8") as f:
            f.write(html_content)

        LOGGER.debug(f"Rendering HTML to PNG: {html_file_abs} -> {output_png_abs}")
        if len(title) > 60:
            lines = int(len(title) / 69)
        else:
            lines = 0
        height = 255 + 30 * lines
        LOGGER.info(f"Height: {height}")
        if height > 600:
            height = 255
        # Render HTML to PNG
        sel_renderer = SelRenderer(width=600, height=height)
        line_count = sel_renderer.render_html_to_png_selenium(
            os.path.abspath("./tmp/real_reddit.html"),
            output_png_abs,
            width=600,
            height=height,
        )
        sel_renderer.close()
        try:
            with Image.open(output_png_abs) as img:
                width, height = img.size
                # Create a mask for rounded corners
                radius = int(
                    min(width, height) * 0.2
                )  # radius is 10% of the minimum dimension
                mask = Image.new("L", (width, height), 0)
                draw = ImageDraw.Draw(mask)
                draw.rounded_rectangle((0, 0, width, height), radius=radius, fill=255)

                # Apply the mask to create transparency on the corners
                img.putalpha(mask)
                img.save(output_png_abs)
            return output_png_abs
        except Exception:
            LOGGER.error(f"Error cropping image: {traceback.format_exc()}")
        LOGGER.debug(f"HTML rendered to {output_png} successfully.")

    except Exception:
        print(f"Error rendering HTML to PNG: {traceback.format_exc()}")


def render_html_to_png_com(
    post_id: str,
    title: str,
    subreddit: str,
    subreddit_id: str,
    user_id: str,
    user_name: str,
    time_ago: datetime,
    score_int: int = 0,
    comment_int: int = 0,
    lang: str = "en",
    output_png_fold: str = "./tmp",
    html_file: str = "clip_creator/utils/real_reddit.html",
):
    """
    Renders an HTML file with potential replacements to a PNG image.

    Args:
        html_file (str): Path to the input HTML file.
        output_png (str): Path to the output PNG file.
        replacements (dict, optional): Dictionary of replacements (key: old_string, value: new_string).
        *SUBREDDIT*
        *SUBREDDIT_ID*
        *USER_ID*
        *TIME_AGO* # "15 hr." ago
        *USER_NAME*
        *SCORE_INT*
        *COMMENT_INT*
        *SUB_IMG_PATH*
        *TITLE*
        *USER_IMG*
    """
    if lang == "en":
        output_png: str = f"{output_png_fold}/{post_id}_coms.png"
    else:
        output_png: str = f"{output_png_fold}/{post_id}_{lang}_coms.png"
    output_png_abs = os.path.abspath(output_png)
    html_file_abs = os.path.abspath(html_file)
    try:
        with open(html_file_abs, encoding="utf-8") as f:
            html_content = f.read()

        html_content = html_content.replace("*SUBREDDIT*", subreddit)
        html_content = html_content.replace("*SUBREDDIT_ID*", subreddit_id)
        html_content = html_content.replace("*USER_ID*", user_id)
        now = datetime.now(UTC)  # Might cause issues for time being off
        delta = now - time_ago
        years = delta.days // 365
        months = delta.days // 30
        days = delta.days
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60

        if years >= 1:
            time_diff = f"{years} year{'s' if years > 1 else ''}"
        elif months >= 1:
            time_diff = f"{months} month{'s' if months > 1 else ''}"
        elif days >= 1:
            time_diff = f"{days} day{'s' if days > 1 else ''}"
        elif hours >= 1:
            time_diff = f"{hours} hr"
        elif minutes >= 1:
            time_diff = f"{minutes} min"
        else:
            time_diff = "just now"
        img_path = os.path.join("clip_creator/utils/imgs", "amitheahole.png")
        for file in os.listdir("clip_creator/utils/imgs"):
            if file.startswith(subreddit):
                img_path = os.path.join("clip_creator/utils/imgs", file)
        html_content = html_content.replace("*TIME_AGO*", time_diff)
        if not user_name:
            user_name = "Unknown"
        html_content = html_content.replace("*USER_NAME*", ("u/" + user_name))
        html_content = html_content.replace("*SCORE_INT*", str(score_int))
        html_content = html_content.replace("*COMMENT_INT*", str(comment_int))
        html_content = html_content.replace("*SUB_IMG_PATH*", os.path.abspath(img_path))
        html_content = html_content.replace("*TITLE*", title)
        html_content = html_content.replace(
            "*USER_IMG*", os.path.abspath("clip_creator/utils/imgs/reddit.jpg")
        )
        with open("./tmp/real_reddit.html", "w", encoding="utf-8") as f:
            f.write(html_content)

        LOGGER.debug(f"Rendering HTML to PNG: {html_file_abs} -> {output_png_abs}")
        if len(title) > 60:
            lines = int(len(title) / 69)
        else:
            lines = 0
        height = 255 + 30 * lines
        LOGGER.info(f"Height: {height}")
        if height > 600:
            height = 255
        sel_renderer = SelRenderer(width=600, height=height)
        # Render HTML to PNG
        line_count = sel_renderer.render_html_to_png_selenium(
            os.path.abspath("./tmp/real_reddit.html"),
            output_png_abs,
            width=600,
            height=height,
        )
        sel_renderer.close()
        try:
            with Image.open(output_png_abs) as img:
                width, height = img.size
                # Crop off the right 4% of the image
                height = height  # (line_count)*20
                new_right = width  # int(width * 0.96)
                cropped_img = img.crop((0, 0, new_right, (line_count) * 20))
                # Create a mask for rounded corners
                radius = int(
                    min(new_right, height) * 0.1
                )  # radius is 10% of the minimum dimension
                mask = Image.new("L", (new_right, height), 0)
                draw = ImageDraw.Draw(mask)
                draw.rounded_rectangle(
                    (0, 0, new_right, height), radius=radius, fill=255
                )

                # Apply the mask to create transparency on the corners
                cropped_img.putalpha(mask)
                cropped_img.save(output_png_abs)
            return output_png_abs
        except Exception:
            LOGGER.error(f"Error cropping image: {traceback.format_exc()}")
        LOGGER.debug(f"HTML rendered to {output_png} successfully.")

    except Exception:
        print(f"Error rendering HTML to PNG: {traceback.format_exc()}")

class SelRenderer:
    def __init__(self, width=1080, height=1920):
        logging.getLogger("selenium").setLevel(logging.CRITICAL)
        
        
    def render_html_to_png_selenium(
        self, html_file, output_png, width=1080, height=1920, comment=False, reply=False
    ):
        """
        Renders an HTML file to a PNG image using Selenium headless.

        Args:
            html_file (str): Path to the input HTML file.
            output_png (str): Path to the output PNG file.
            width (int, optional): Desired width of the viewport. Defaults to 1080.
            height (int, optional): Desired height of the viewport. Defaults to 1920.
        """
        # Set up Chrome options for headless mode
        chrome_options = Options()
        chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
        chrome_options.add_argument("--headless")  # Run Chrome in headless mode
        chrome_options.add_argument(
            f"--window-size={width},{height}"
        )  # Set window size

        # Initialize the WebDriver (replace with the path to your ChromeDriver)
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        try:
            LOGGER.debug(f"Loading HTML file: {html_file} -> {output_png}")
            driver = self.driver

            # Load the HTML file
            driver.get(html_file)
            if not comment:
                # Wait for the main comment element to be visible
                post_element = WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.TAG_NAME, "shreddit-post"))
                )

                # Scroll the element into view to ensure it's rendered
                driver.execute_script("arguments[0].scrollIntoView(true);", post_element)

                # Calculate FULL content dimensions including overflow
                content_dimensions = driver.execute_script(
                    """
                    const comment = arguments[0];
                    return {
                        width: comment.scrollWidth,
                        height: comment.scrollHeight
                    };
                """,
                    post_element,
                )

                LOGGER.debug(f"Full content dimensions: {content_dimensions}")

                # Resize window to accommodate full content (add padding for safety)
                driver.set_window_size(
                    content_dimensions["width"] + 100, content_dimensions["height"] + 350
                )

                # Re-scroll into view after resizing
                driver.execute_script("arguments[0].scrollIntoView(true);", post_element)

                # Allow time for layout to stabilize after resize
                time.sleep(0.5)
                line_count = 0
                # Capture screenshot of the entire element
                post_element.screenshot(output_png)
            elif comment:
                # Wait for the main comment element to be visible
                comment_element = WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.CLASS_NAME, "clip-paddingbox"))
                )
                if reply:
                    # Wait for nested shreddit-comment elements to load
                    WebDriverWait(driver, 10).until(
                        lambda d: len(
                            comment_element.find_elements(By.XPATH, ".//shreddit-comment")
                        )
                        >= 2
                    )
                else:
                    # Wait for shreddit-comment elements to load
                    WebDriverWait(driver, 10).until(
                        lambda d: len(
                            comment_element.find_elements(By.XPATH, ".//shreddit-comment")
                        )
                        >= 1
                    )

                # Scroll the element into view to ensure it's rendered
                driver.execute_script("arguments[0].scrollIntoView(true);", comment_element)

                # Calculate FULL content dimensions including overflow
                content_dimensions = driver.execute_script(
                    """
                    const comment = arguments[0];
                    return {
                        width: comment.scrollWidth,
                        height: comment.scrollHeight
                    };
                """,
                    comment_element,
                )

                LOGGER.debug(f"Full content dimensions: {content_dimensions}")

                # Resize window to accommodate full content (add padding for safety)
                driver.set_window_size(
                    content_dimensions["width"] + 100, content_dimensions["height"] + 350
                )

                # Re-scroll into view after resizing
                driver.execute_script("arguments[0].scrollIntoView(true);", comment_element)

                # Allow time for layout to stabilize after resize
                time.sleep(0.5)
                line_count = 0
                # Capture screenshot of the entire element
                comment_element.screenshot(output_png)
            else:
                element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "shreddit-post"))
                )

                body_dimensions = driver.execute_script("""
                    const shredditPost = document.querySelector('shreddit-post');
                    if (shredditPost) {
                        return {
                            width: shredditPost.offsetWidth,
                            height: shredditPost.offsetHeight
                        };
                    } else {
                        return {
                            width: 0,
                            height: 0
                        };
                    }
                """)

                # Get the number of lines using JavaScript
                line_count = driver.execute_script(
                    """
                    const h2 = arguments[0];
                    const lineHeight = parseInt(getComputedStyle(h2).lineHeight);
                    const height = h2.offsetHeight;
                    return Math.ceil(height / lineHeight);
                """,
                    element,
                )
                LOGGER.debug(f"Line count: {line_count}")
                width = body_dimensions["width"]
                height = body_dimensions["height"]
                LOGGER.debug(f"Body dimensions: {width}x{height}")
                driver.save_screenshot(output_png)
            
            
            self.driver.quit()
            LOGGER.debug(f"HTML rendered to {output_png} successfully.")
            return line_count
        except Exception:
            print(f"Error rendering HTML to PNG: {traceback.format_exc()}")
    def close(self):
        pass

def render_html_to_png_comment(
    post_id: str,
    chunk_id: str,
    chunk: dict,
    comt_above:int,
    comment_json: dict | None = None,
    reply: bool = False,
    output_png_fold: str = "./tmp/caps_img",
    html_file: str = "clip_creator/utils/real_reddit_com.html",
    html_file_reply: str = "clip_creator/utils/real_reddit_comrpl.html",
) -> list:
    """
    Renders an HTML file with potential replacements to a PNG image.

    Args:
        html_file (str): Path to the input HTML file.
        output_png (str): Path to the output PNG file.
        replacements (dict, optional): Dictionary of replacements (key: old_string, value: new_string).

        _comrpl:
        *AUTHOR_NAME1*
        *AUTHOR_NAME2*
        *TEXT1*
        *TEXT2*
        *TIME_AGO1*
        *TIME_AGO2* # 2025-02-18T19:30:59.979000+0000
        *SCORE1*
        *SCORE2*
        *ABS_IMAGE1*
        *ABS_IMAGE2*

        _com:
        *ABS_IMAGE* # Path to profile image (probably reddit.jpg)
        *AUTHOR_NAME1*
        *TEXT1*
        *TIME_AGO1*
        *SCORE1*
    """
    def remove_special_chars(s: str) -> str:
        return re.sub(r'[^A-Za-z0-9 ]+', '', s)
    def contains_numbers(word: str) -> bool:
        return any(char.isdigit() for char in word)
    def is_alphanumeric(char: str) -> bool:
        """
        Returns True if the character is a letter or a number.
        """
        return char.isalnum()
    # dirty_remove_cuss()
    idx = 0
    chars = None
    all_words = reddit_remove_bad_words(
                                comment_json.get("content","") + (
                                   (" " + comment_json.get("best_reply",{}).get("content", "")) if comment_json.get("best_reply",{}).get("upvotes", 0) > comt_above else ""
                                )
                                ).split()
    LOGGER.debug(f"Words: {all_words}")
    debug_pairs = []
    for i, script_step in enumerate(chunk.get("ascript", [])):
        
        if chars:
            LOGGER.debug(f"rem {chars} chars for {script_step.get('text')}")
            chars -= 1
            if chars <= 0:
                chars = None
            else:
                continue
        if i == 0:
            LOGGER.debug(f"Skipping 0: {script_step.get('text')}")
            # skip 0 because it is the number of the item
            continue
        if idx >= len(all_words):
            LOGGER.debug(f"Index out of bounds: {idx} >= {len(all_words)}")
            break
        word = all_words[idx]
        
        LOGGER.debug(f"Word: {word} and Script step: {script_step.get('text')}")
        if script_step.get("text") != remove_special_chars(word.upper()):
            LOGGER.debug(f'{reddit_acronym(word).upper()} ?? {script_step.get("text")}')
            
            if reddit_acronym(word).upper() == script_step.get("text"):
                LOGGER.debug(f"Acronym match: {word} == {script_step.get('text')}")
                if i+len(remove_special_chars(word.upper())) <= len(chunk["ascript"])-1:
                    chunk["ascript"][i]["chars"] = len(remove_special_chars(word.upper())) # Number of chars to highlight
                else:
                    chunk["ascript"][i]["chars"] = len(chunk["ascript"]) - i
                debug_str = ""
                for j in range(chunk["ascript"][i]["chars"]):
                    debug_str += chunk["ascript"][i+j]["text"] + " "
                debug_pairs.append((word, debug_str))
                idx += 1
                chars = chunk["ascript"][i].get("chars", None)
                continue
            if contains_numbers(word) or word.isdigit():
                LOGGER.debug(f"has numbers: {word}")
                if "s" in word.lower():
                    idx += 1
                    chars = chunk["ascript"][i].get("chars", None)
                    continue
                else:
                    if i+len(remove_special_chars(word.upper())) <= len(chunk["ascript"])-1:
                        chunk["ascript"][i]["chars"] = len(remove_special_chars(word.upper())) # Number of chars to highlight
                    else:
                        chunk["ascript"][i]["chars"] = len(chunk["ascript"]) - i
                    debug_str = ""
                    for j in range(chunk["ascript"][i]["chars"]):
                        debug_str += chunk["ascript"][i+j]["text"] + " "
                    debug_pairs.append((word, debug_str))
                    idx += 1
                    chars = chunk["ascript"][i].get("chars", None)
                    continue
            LOGGER.debug(f"Word mismatch: {word} != {script_step.get('text')}")
        else:
            debug_pairs.append((word, script_step.get("text")))
            idx += 1
            chars = chunk["ascript"][i].get("chars", None)
            continue
    LOGGER.debug(f"Debug pairs: {debug_pairs}")
    chars = None
    current_idx = 0
    abs_images = []
    # Setup Random Avatars
    avatars = os.listdir("clip_creator/utils/imgs/users")
    ava1name = random.choice(avatars)
    avatars.remove(ava1name)

    ava1 = os.path.abspath(
        os.path.join("clip_creator/utils/imgs/users", ava1name)
    )
    ava2 = os.path.abspath(
        os.path.join("clip_creator/utils/imgs/users", random.choice(avatars))
    )
    color = "red"
    sel_renderer = SelRenderer(width=600, height=600)
    for i, script_step in enumerate(chunk.get("ascript", [])):
            
        chars = script_step.get("chars", chars)
        
        ran_check = randint(1, 10)
        if ran_check < 3 and not chars:
            color = choice(list(COLOR_PAIRS["white"]))
        elif not chars:
            color = "red"    
        LOGGER.debug(f"Highlighting {script_step.get('chars')} chars for {script_step.get('text')}")
        if i == 0:
            continue # skip 0 because it is the number of the item
        if comment_json is None:
            comment_json = {}
        try:
            html_file_abs = os.path.abspath(html_file if not reply else html_file_reply)
            LOGGER.debug(f"HTML file: {html_file_abs}")
            output_png: str = f"{output_png_fold}/{post_id}_{chunk_id}_{i}post.png"
            output_png_abs = os.path.abspath(output_png)

            with open(html_file_abs, encoding="utf-8") as f:
                html_content = f.read()
            total_content = comment_json.get("content", "")
            html_content = html_content.replace(
                "*AUTHOR_NAME1*", dirty_remove_cuss(comment_json.get("author", ""))
            )
            html_content = html_content.replace(
                "*TIME_AGO1*", comment_json.get("posted_at", "")
            )
            if current_idx < len(reddit_remove_bad_words(comment_json.get("content", ""))):
                text_one = reddit_remove_bad_words(comment_json.get("content", ""))
                LOGGER.info(f"Text one: {text_one}")
                LOGGER.info(f"Current index: {current_idx}")
                current_word = text_one.split()[current_idx]
                if chars:
                    LOGGER.debug(f"CHARSZ: {chars}")
                    total_chars = len(remove_special_chars(current_word))
                    LOGGER.debug(f"CHARSZ total: {total_chars}")
                    current_widx = total_chars - chars
                    LOGGER.debug(f"CHARSZ idx: {current_widx}")
                    chars_found = 0
                    cw_idx = 0
                    for k, ch in enumerate(current_word):
                        if is_alphanumeric(ch):
                            chars_found += 1
                            if chars_found == current_widx + 1:
                                cw_idx = k
                                break
                    current_word = current_word[:cw_idx] + f"<span style='color:{color}'>" + current_word[cw_idx] + "</span>" + current_word[cw_idx+1:]        
                    chars -= 1
                    LOGGER.debug(f"CHARSZ end: {chars}")
                    if chars <= 0:
                        chars = None
                    text_one_tmp = text_one.split()[:current_idx] + [current_word] + text_one.split()[current_idx+1:]
                else:
                    text_one_tmp = text_one.split()[:current_idx] + [f"<span style='color:{color}'>{current_word}</span>"] + text_one.split()[current_idx+1:]
                text_one = " ".join(text_one_tmp)
                html_content = html_content.replace(
                    "*TEXT1*", text_one
                )
            else:
                html_content = html_content.replace(
                    "*TEXT1*", reddit_remove_bad_words(comment_json.get("content", ""))
                )
            html_content = html_content.replace(
                "*SCORE1*", str(comment_json.get("upvotes", ""))
            )
            if reply:
                total_content += " " + comment_json.get("best_reply", {}).get("content", "")
                html_content = html_content.replace(
                    "*AUTHOR2*",
                    dirty_remove_cuss(comment_json.get("best_reply", {}).get("author", "")),
                )
                html_content = html_content.replace(
                    "*TIME_AGO2*", comment_json.get("best_reply", {}).get("posted_at", "")
                )
                if current_idx < len(reddit_remove_bad_words(comment_json.get("content", ""))):
                    html_content = html_content.replace(
                        "*TEXT2*",
                        reddit_remove_bad_words(
                            comment_json.get("best_reply", {}).get("content", "")
                        ),
                    )
                
                else:
                    text_two = reddit_remove_bad_words(comment_json.get("best_reply", {}).get("content", ""))
                    current_word = text_two.split()[current_idx]
                    if chars:
                        total_chars = len(remove_special_chars(current_word)) - 1
                        current_widx = total_chars - chars
                        chars_found = 0
                        cw_idx = 0
                        for k, ch in enumerate(current_word):
                            if is_alphanumeric(ch):
                                chars_found += 1
                                if chars_found == current_widx:
                                    cw_idx = k
                                    break
                        current_word = current_word[:cw_idx] + f"<span style='color:{color}'>" + current_word[cw_idx] + "</span>" + current_word[cw_idx+1:]        
                        chars -= 1
                        LOGGER.debug(f"CHARSZ: {chars}")
                        if chars <= 0:
                            chars = None
                        text_two_tmp = text_one.split()[:current_idx] + [current_word] + text_one.split()[current_idx+1:]
                    else:
                        text_two_tmp = text_two.split()[:current_idx] + [f"<span class='biggerj' style='color:{color}'>{current_word}</span>"] + text_two.split()[current_idx+1:]
                    text_two = " ".join(text_two_tmp)
                    html_content = html_content.replace(
                        "*TEXT2*", text_two
                    )
                html_content = html_content.replace(
                    "*SCORE2*", str(comment_json.get("best_reply", {}).get("upvotes", ""))
                )
                
                html_content = html_content.replace("*ABS_IMAGE1*", ava1)
                html_content = html_content.replace("*ABS_IMAGE2*", ava2)
            else:
                
                html_content = html_content.replace("*ABS_IMAGE*", ava1)
            with open("./tmp/real_reddit_com.html", "w", encoding="utf-8") as f:
                f.write(html_content)

            LOGGER.debug(f"Rendering HTML to PNG: {html_file_abs} -> {output_png_abs}")
            if len(total_content) > 99:
                lines = int(len(total_content) / 99)
            else:
                lines = 0
            height = 255 + 30 * lines
            LOGGER.debug(f"Height: {height}")
            if height > 800:
                height = 255
            # Render HTML to PNG
            
            line_count = sel_renderer.render_html_to_png_selenium(
                os.path.abspath("./tmp/real_reddit_com.html"),
                output_png_abs,
                width=600,
                height=height,
                comment=True,
                reply=reply,
            )
            if not os.path.exists(output_png_abs):
                raise Exception("Image not found")
            try:
                with Image.open(output_png_abs) as img:
                    img = img.convert("RGBA")
                    width, height = img.size

                    # Create a mask for rounded corners
                    radius = int(
                        min(width, height) * 0.1
                    )  # radius is 10% of the minimum dimension
                    mask = Image.new("L", (width, height), 0)
                    draw = ImageDraw.Draw(mask)
                    draw.rounded_rectangle((0, 0, width, height), radius=radius, fill=255)

                    # Apply the mask to create transparency on the corners
                    img.putalpha(mask)
                    img.save(output_png_abs)
                if not os.path.exists(output_png_abs):
                    raise Exception("Image not found after save")
                abs_images.append(output_png_abs)
                if not chars:
                    current_idx += 1
            except Exception as e:
                LOGGER.error(f"Error cropping image: {e}")
                if not os.path.exists(output_png_abs):
                    raise e
            LOGGER.info(f"HTML rendered to {output_png} successfully.")

        except Exception as e:
            LOGGER.info(f"Error rendering HTML to PNG: {traceback.format_exc()}")
            if not os.path.exists(output_png_abs):
                raise e
    sel_renderer.close()
    return abs_images
def render_html_to_png_comment_backup(
    post_id: str,
    chunk_id: str,
    chunk: dict,
    comment_json: dict | None = None,
    reply: bool = False,
    output_png_fold: str = "./tmp/caps_img",
    html_file: str = "clip_creator/utils/real_reddit_com.html",
    html_file_reply: str = "clip_creator/utils/real_reddit_comrpl.html",
) -> str | None:
    """
    Renders an HTML file with potential replacements to a PNG image.

    Args:
        html_file (str): Path to the input HTML file.
        output_png (str): Path to the output PNG file.
        replacements (dict, optional): Dictionary of replacements (key: old_string, value: new_string).

        _comrpl:
        *AUTHOR_NAME1*
        *AUTHOR_NAME2*
        *TEXT1*
        *TEXT2*
        *TIME_AGO1*
        *TIME_AGO2* # 2025-02-18T19:30:59.979000+0000
        *SCORE1*
        *SCORE2*
        *ABS_IMAGE1*
        *ABS_IMAGE2*

        _com:
        *ABS_IMAGE* # Path to profile image (probably reddit.jpg)
        *AUTHOR_NAME1*
        *TEXT1*
        *TIME_AGO1*
        *SCORE1*
    """
    
    if comment_json is None:
        comment_json = {}
    try:
        html_file_abs = os.path.abspath(html_file if not reply else html_file_reply)
        LOGGER.debug(f"HTML file: {html_file_abs}")
        output_png: str = f"{output_png_fold}/{post_id}_{chunk_id}_post.png"
        output_png_abs = os.path.abspath(output_png)

        with open(html_file_abs, encoding="utf-8") as f:
            html_content = f.read()
        total_content = comment_json.get("content", "")
        html_content = html_content.replace(
            "*AUTHOR_NAME1*", dirty_remove_cuss(comment_json.get("author", ""))
        )
        html_content = html_content.replace(
            "*TIME_AGO1*", comment_json.get("posted_at", "")
        )
        
        html_content = html_content.replace(
            "*TEXT1*", reddit_remove_bad_words(comment_json.get("content", ""))
        )
        html_content = html_content.replace(
            "*SCORE1*", str(comment_json.get("upvotes", ""))
        )
        if reply:
            total_content += " " + comment_json.get("best_reply", {}).get("content", "")
            html_content = html_content.replace(
                "*AUTHOR2*",
                dirty_remove_cuss(comment_json.get("best_reply", {}).get("author", "")),
            )
            html_content = html_content.replace(
                "*TIME_AGO2*", comment_json.get("best_reply", {}).get("posted_at", "")
            )
            html_content = html_content.replace(
                "*TEXT2*",
                reddit_remove_bad_words(
                    comment_json.get("best_reply", {}).get("content", "")
                ),
            )
            html_content = html_content.replace(
                "*SCORE2*", str(comment_json.get("best_reply", {}).get("upvotes", ""))
            )
            # Setup Random Avatars
            avatars = os.listdir("clip_creator/utils/imgs/users")
            ava1name = random.choice(avatars)
            avatars.remove(ava1name)

            ava1 = os.path.abspath(
                os.path.join("clip_creator/utils/imgs/users", ava1name)
            )
            ava2 = os.path.abspath(
                os.path.join("clip_creator/utils/imgs/users", random.choice(avatars))
            )
            html_content = html_content.replace("*ABS_IMAGE1*", ava1)
            html_content = html_content.replace("*ABS_IMAGE2*", ava2)
        else:
            avatars = os.listdir("clip_creator/utils/imgs/users")
            ava1 = os.path.abspath(
                os.path.join("clip_creator/utils/imgs/users", random.choice(avatars))
            )
            html_content = html_content.replace("*ABS_IMAGE*", ava1)
        with open("./tmp/real_reddit_com.html", "w", encoding="utf-8") as f:
            f.write(html_content)

        LOGGER.debug(f"Rendering HTML to PNG: {html_file_abs} -> {output_png_abs}")
        if len(total_content) > 99:
            lines = int(len(total_content) / 99)
        else:
            lines = 0
        height = 255 + 30 * lines
        LOGGER.debug(f"Height: {height}")
        if height > 800:
            height = 255
        # Render HTML to PNG
        sel_renderer = SelRenderer(width=600, height=600)
        line_count = sel_renderer.render_html_to_png_selenium(
            os.path.abspath("./tmp/real_reddit_com.html"),
            output_png_abs,
            width=600,
            height=height,
            comment=True,
            reply=reply,
        )
        sel_renderer.close()
        if not os.path.exists(output_png_abs):
            raise Exception("Image not found")
        try:
            with Image.open(output_png_abs) as img:
                img = img.convert("RGBA")
                width, height = img.size

                # Create a mask for rounded corners
                radius = int(
                    min(width, height) * 0.1
                )  # radius is 10% of the minimum dimension
                mask = Image.new("L", (width, height), 0)
                draw = ImageDraw.Draw(mask)
                draw.rounded_rectangle((0, 0, width, height), radius=radius, fill=255)

                # Apply the mask to create transparency on the corners
                img.putalpha(mask)
                img.save(output_png_abs)
            if not os.path.exists(output_png_abs):
                raise Exception("Image not found after save")
            return output_png_abs
        except Exception as e:
            LOGGER.error(f"Error cropping image: {e}")
            if not os.path.exists(output_png_abs):
                raise e
        LOGGER.info(f"HTML rendered to {output_png} successfully.")

    except Exception as e:
        LOGGER.info(f"Error rendering HTML to PNG: {traceback.format_exc()}")
        if not os.path.exists(output_png_abs):
            raise e
    return None


if __name__ == "__main__":
    render_html_to_png(
        "test",
        "test title, I need this to be verry long to test the multiple lines issue. iff"
        " i continue to misspell words it will be longer. I also beleive that the moon"
        " landing was real. HA, u didn't think I would take that approach did you????",
        "test",
        "test",
        "test",
        "test",
        datetime.now(UTC) - timedelta(hours=3),
        100,
        100,
        "en",
    )
    # LOGGER.setLevel(logging.DEBUG)
    # render_html_to_png_comment(
    #     "test",
    #     "uuid",
    #     comt_above=99999999,
    #     chunk={"ascript": [{"text": "ONE"}, {"text":"TWEENTY"}, {"text":"FOUR"}, {"text":"SEVEN"}, {"text": "SAME"}, {"text": "SEVENTY"}, {"text":"SIX"}, {"text": "REASON"}, {"text": "MORNING", "start": 1.625, "end": 1.885, "duration": 0.26}, {"text": "PEOPLE", "start": 1.905, "end": 2.166, "duration": 0.2609999999999999}, {"text": "ARE", "start": 2.206, "end": 2.326, "duration": 0.1200000000000001}, {"text": "GOOD", "start": 2.367, "end": 2.607, "duration": 0.2400000000000002}, {"text": "MORAL", "start": 2.768, "end": 3.028, "duration": 0.26000000000000023}, {"text": "PEOPLE", "start": 3.068, "end": 3.369, "duration": 0.30100000000000016}, {"text": "AND", "start": 3.409, "end": 3.51, "duration": 0.10099999999999998}, {"text": "NIGHT", "start": 3.55, "end": 3.73, "duration": 0.18000000000000016}, {"text": "OWLS", "start": 3.871, "end": 4.091, "duration": 0.2200000000000002}, {"text": "ARE", "start": 4.131, "end": 4.232, "duration": 0.10099999999999998}, {"text": "LAZY", "start": 4.272, "end": 4.593, "duration": 0.32099999999999973}, {"text": "LAYABOUTS", "start": 4.633, "end": 5.074, "duration": 0.44099999999999984}, {"text": "MOST", "start": 5.515, "end": 5.696, "duration": 0.18100000000000005}, {"text": "VOCAL", "start": 5.756, "end": 6.017, "duration": 0.2610000000000001}, {"text": "GROUP", "start": 6.057, "end": 6.277, "duration": 0.21999999999999975}, {"text": "WINS", "start": 6.317, "end": 6.598, "duration": 0.2809999999999997}]},
    #     comment_json={"author": "hexagon_heist", "upvotes": 1487, "content": "24/7 Same 76 reason morning people are good, moral people and night owls are lazy layabouts. Most vocal group wins.", "parent_id": "t3_1jhpqwp", "posted_at": "2025-03-23T03:07:13.000000+0000", "best_reply": {}, "reply": {}, "comments_above_rpl": 99999999},
    #     reply=False,
    # )
    # caption_list = [
    #     {"text": "on", "start": 40.298, "end": 40.439, "duration": 0.14099999999999824},
    #     {
    #         "text": "them",
    #         "start": 40.479,
    #         "end": 40.659,
    #         "duration": 0.17999999999999972,
    #     },
    #     {
    #         "text": "when",
    #         "start": 40.719,
    #         "end": 40.919,
    #         "duration": 0.19999999999999574,
    #     },
    #     {"text": "I", "start": 40.979, "end": 41.059, "duration": 0.0799999999999983},
    #     {"text": "win", "start": 41.139, "end": 41.399, "duration": 0.259999999999998},
    #     {"text": "the", "start": 41.459, "end": 41.62, "duration": 0.16099999999999426},
    #     {
    #         "text": "round.",
    #         "start": 41.64,
    #         "end": 42.04,
    #         "duration": 0.3999999999999986,
    #     },
    #     {
    #         "text": "Sign",
    #         "start": 42.28,
    #         "end": 42.681,
    #         "duration": 0.40099999999999625,
    #     },
    # ]
    # max_width = 1080  # Set maximum width for wrapping
    # output_directory = r"tmp\caps_img"
    # prefix = "test_"
    # create_caption_images(prefix, caption_list, max_width, output_directory)
