import os

from PIL import Image, ImageDraw, ImageFont


def create_caption_images(prefix: str, captions, max_width, output_dir="."):
    """Creates one image *per line* of wrapped text, highlighting current word."""
    # TODO: Make this parralel
    os.makedirs(output_dir, exist_ok=True)
    try:
        font = ImageFont.truetype(
            "Vercetti Regular/Vercetti-Regular.ttf", size=100
        )  # Your font path
    except Exception as e:
        print(f"Error loading font: {e}. Trying default.")
        try:
            font = ImageFont.load_default()
        except Exception as e2:
            print(f"Error loading default font: {e2}. Please install a font.")
            return

    padding = 30
    word_spacing = 20
    outline_width = 7

    for caption in captions:
        start = str(caption.get("start")).replace(".", "-")
        text = caption.get("text", "")
        words = text.split()

        for i, current_word in enumerate(
            words
        ):  # Iterate through words for highlighting
            line_index = 0
            current_word_index = 0

            while current_word_index < len(words):
                current_line = []
                current_line_indices = []  # Keep track of word indices in the line

                # Create a dummy image and draw context for calculations
                dummy_img = Image.new(
                    "RGBA", (max_width * 2, max_width), color=(0, 0, 0, 0)
                )
                dummy_draw = ImageDraw.Draw(dummy_img)

                # Build up the current line using dummy context
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
                        break  # Line is full

                    current_line.append(word)
                    current_line_indices.append(current_word_index)  # Add index
                    temp_x += word_width + word_spacing
                    current_word_index += 1

                # Check if the current highlighted word is in this line
                if current_word in current_line:
                    # Create an image to measure text height
                    img = Image.new(
                        "RGBA", (max_width * 2, max_width), color=(0, 0, 0, 0)
                    )
                    draw = ImageDraw.Draw(img)

                    max_ascent = 0
                    max_descent = 0
                    for word in current_line:
                        bbox = draw.textbbox(
                            (0, padding), word, font=font, align="center"
                        )
                        ascent = (
                            padding - bbox[1]
                        )  # Distance from baseline (padding) to top
                        descent = bbox[3] - padding  # Distance from baseline to bottom
                        max_ascent = max(max_ascent, ascent)
                        max_descent = max(max_descent, descent)
                    total_height = max_ascent + max_descent
                    # Create final image based on calculated total_height
                    new_width = max_width
                    new_height = total_height + 2 * padding
                    final_img = Image.new(
                        "RGBA", (new_width, new_height), color=(0, 0, 0, 0)
                    )
                    final_draw = ImageDraw.Draw(final_img)

                    # Calculate total width of the current line
                    total_line_width = 0
                    word_widths = []
                    for word in current_line:
                        bbox = final_draw.textbbox(
                            (0, padding), word, font=font, align="center"
                        )
                        w = bbox[2] - bbox[0]
                        word_widths.append(w)
                        total_line_width += w
                    if len(current_line) > 1:
                        total_line_width += word_spacing * (len(current_line) - 1)

                    # Center the text horizontally
                    x = (new_width - total_line_width) // 2
                    y_offset = (new_height - total_height - 10) // 2
                    current_y = padding  # + y_offset

                    # Draw each word with outline and fill (highlighted word in red)
                    for idx, word in enumerate(current_line):
                        color = (
                            "red" if current_line_indices[idx] == i else "white"
                        )  # Use index for comparison
                        # Outline
                        for dx in range(-outline_width, outline_width + 1):
                            for dy in range(-outline_width, outline_width + 1):
                                final_draw.text(
                                    (x + dx, current_y + dy),
                                    word,
                                    font=font,
                                    fill="black",
                                    align="center",
                                )

                        # Text
                        final_draw.text(
                            (x, current_y), word, font=font, fill=color, align="center"
                        )
                        x += word_widths[idx] + word_spacing

                    filename = f"{prefix}{start}_word{i}.jpg"  # Unique filename
                    file_path = os.path.join(output_dir, filename)
                    resized_img = final_img.resize(
                        (final_img.width // 2, final_img.height // 2), 1
                    )
                    resized_img.convert("RGB").save(file_path, "JPEG", quality=40)
                    print(f"Saved {file_path}")

                    line_index += 1


def create_caption_images_thread(prefix: str, captions, max_width, output_dir="."):
    """Creates one image per line of wrapped text, highlighting current word using parallel processing."""
    os.makedirs(output_dir, exist_ok=True)

    try:
        font = ImageFont.truetype("Vercetti Regular/Vercetti-Regular.ttf", size=100)
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
        print(f"Saved {file_path}")

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


if __name__ == "__main__":
    caption_list = [
        {
            "start": 3764.4,
            "text": "This is a sample caption that is very long and needs to wrap",
        },
        {"start": 23.8, "text": "Another caption for testing with even more words"},
    ]
    max_width = 1080  # Set maximum width for wrapping
    output_directory = "./caption_images"
    create_caption_images(caption_list, max_width, output_directory)
