import os
import base64
import imgkit
import traceback
from datetime import datetime, timezone
from queue import Queue
from random import choice, randint
from threading import Thread
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from PIL import Image, ImageDraw, ImageFont
from pilmoji import Pilmoji
from tqdm import tqdm
from datetime import timedelta
from PIL import Image

from clip_creator.conf import (
    COLOR_PAIRS,
    COLORS,
    CURSE_WORDS,
    E_FONT_PATH,
    FONT_PATH,
    LOGGER,
)


def remove_curse_words(text: str) -> str:
    """
    Removes curse words from a given text.
    """
    # LOGGER.info("Removing curse words from text. %s", text)
    for curse_word in CURSE_WORDS:
        if isinstance(text, list):
            tmp_txt = []
            for word_d in text:
                if curse_word in word_d.get("text", "").lower():
                    word_d["text"] = "*" * len(curse_word)
                tmp_txt.append(word_d)
            text = tmp_txt
        elif isinstance(text, str):
            if curse_word in text.lower():
                tmp_txt = ""
                for word in text.split():
                    tmp_txt += "*" * len(curse_word) if curse_word in word.lower() else word
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
def create_caption_images_reddit(prefix: str, captions, max_width, output_dir=".", part=0):
    """Creates one image *per line* of wrapped text, highlighting current word.

    caption: List of dictionaries with "start" and "text" keys.
    """
    try:
        font = ImageFont.truetype(FONT_PATH, size=70)
    except Exception as e:
        print(f"Error loading font: {e}. Trying default.")
        try:
            font = ImageFont.load_default()
        except Exception as e2:
            print(f"Error loading default font: {e2}. Please install a font.")
            return

    h_padding = 20
    padding = 20
    word_spacing = 15
    outline_width = 5
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

            filename = f"{prefix}_line{j}_word{word_index}-{part}.png"
            file_path = os.path.join(output_dir, filename)

            final_img.save(file_path, "PNG")

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


def render_html_to_png(post_id:str, title:str, subreddit:str, subreddit_id:str, user_id:str, user_name:str, time_ago:datetime, score_int:int=0, comment_int:int=0, output_png_fold:str="./tmp",html_file:str="clip_creator/utils/real_reddit.html"):
    """
    Renders an HTML file with potential replacements to a PNG image.

    Args:
        html_file (str): Path to the input HTML file.
        output_png (str): Path to the output PNG file.
        replacements (dict, optional): Dictionary of replacements (key: old_string, value: new_string).
    """
    output_png:str=f"{output_png_fold}/{post_id}_post.png"
    output_png_abs = os.path.abspath(output_png)
    html_file_abs = os.path.abspath(html_file)
    try:
        with open(html_file_abs, 'r', encoding='utf-8') as f:
            html_content = f.read()

        html_content= html_content.replace("*SUBREDDIT*", subreddit)
        html_content= html_content.replace("*SUBREDDIT_ID*", subreddit_id)
        html_content= html_content.replace("*USER_ID*", user_id)
        now = datetime.now(timezone.utc) # Might cause issues for time being off
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
        html_content= html_content.replace("*USER_NAME*", user_name)
        html_content= html_content.replace("*SCORE_INT*", str(score_int))
        html_content= html_content.replace("*COMMENT_INT*", str(comment_int))
        html_content= html_content.replace("*SUB_IMG_PATH*", os.path.abspath(img_path))
        html_content= html_content.replace("*TITLE*", title)
        html_content= html_content.replace("*USER_IMG*", os.path.abspath("clip_creator/utils/imgs/reddit.jpg"))
        with open("./tmp/real_reddit.html", 'w', encoding='utf-8') as f:
            f.write(html_content)
            

        LOGGER.info(f"Rendering HTML to PNG: {html_file_abs} -> {output_png_abs}")
        if len(title) > 60:
            lines = int(len(title)/60)
        else:
            lines = 0
        height = 255 + 40*lines
        LOGGER.info(f"Height: {height}")
        if height > 600:
            height = 255
        # Render HTML to PNG
        render_html_to_png_selenium(os.path.abspath("./tmp/real_reddit.html"), output_png_abs, width=600, height=height)

        try:
            with Image.open(output_png_abs) as img:
                width, height = img.size
                # Crop off the right 4% of the image
                new_right = width * 0.96
                cropped_img = img.crop((0, 0, new_right, height))
                cropped_img.save(output_png_abs)
                return output_png_abs
        except Exception as e:
            LOGGER.error(f"Error cropping image: {e}")
        LOGGER.info(f"HTML rendered to {output_png} successfully.")

    except Exception as e:
        print(f"Error rendering HTML to PNG: {traceback.format_exc()}")
def render_html_to_png_selenium(html_file, output_png, width=1080, height=1920):
    """
    Renders an HTML file to a PNG image using Selenium headless.

    Args:
        html_file (str): Path to the input HTML file.
        output_png (str): Path to the output PNG file.
        width (int, optional): Desired width of the viewport. Defaults to 1080.
        height (int, optional): Desired height of the viewport. Defaults to 1920.
    """

    try:
        # Set up Chrome options for headless mode
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Run Chrome in headless mode
        chrome_options.add_argument(f'--window-size={width},{height}')  # Set window size

        # Initialize the WebDriver (replace with the path to your ChromeDriver)
        service = Service(ChromeDriverManager().install()) 
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # Load the HTML file
        driver.get(html_file)

        # Take the screenshot
        driver.save_screenshot(output_png)

        # Close the browser
        driver.quit()

        print(f"HTML rendered to {output_png} successfully.")

    except Exception as e:
        print(f"Error rendering HTML to PNG: {traceback.format_exc()}")
if __name__ == "__main__":
    render_html_to_png(
        "test", 
        "AITAH for not wanting to share my winnings with my family?",
        "AITAH", 
        "t3_1g371fk", 
        "t2_hi68qemi", 
        "4dagoodtimes", 
        datetime.now() - timedelta(hours=3), 
        score_int=43547, 
        comment_int=4555555555555,
    )
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

