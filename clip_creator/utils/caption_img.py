from PIL import Image, ImageDraw, ImageFont
import os

def create_caption_images(captions, max_width, output_dir="."):
    """Creates one image *per line* of wrapped text, highlighting current word."""
    os.makedirs(output_dir, exist_ok=True)
    try:
        font = ImageFont.truetype("Vercetti Regular/Vercetti-Regular.ttf", size=100)  # Your font path
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
        start = caption.get("start").replace(".", "-")
        text = caption.get("text", "")
        words = text.split()

        for i, current_word in enumerate(words):  # Iterate through words for highlighting
            line_index = 0
            current_word_index = 0

            while current_word_index < len(words):
                current_line = []

                # Create a dummy image and draw context for calculations
                dummy_img = Image.new("RGBA", (max_width * 2, max_width), color=(0, 0, 0, 0))
                dummy_draw = ImageDraw.Draw(dummy_img)

                # Build up the current line using dummy context
                temp_x = padding
                while current_word_index < len(words):
                    word = words[current_word_index]
                    bbox = dummy_draw.textbbox((0, 0), word, font=font)
                    word_width = bbox[2] - bbox[0]

                    if temp_x + word_width + word_spacing > max_width - padding and len(current_line) > 0:
                        break  # Line is full

                    current_line.append(word)
                    temp_x += word_width + word_spacing
                    current_word_index += 1

                # Check if the current highlighted word is in this line
                if current_word in current_line:
                    # Create an image to measure text height
                    img = Image.new("RGBA", (max_width * 2, max_width), color=(0, 0, 0, 0))
                    draw = ImageDraw.Draw(img)

                    total_height = 0
                    for word in current_line:
                        bbox = draw.textbbox((0, padding), word, font=font, align="center")
                        word_height = bbox[3] - bbox[1]
                        total_height = max(total_height, word_height)

                    # Create final image based on calculated total_height
                    new_width = max_width
                    new_height = total_height + 2 * padding
                    final_img = Image.new("RGBA", (new_width, new_height), color=(0, 0, 0, 0))
                    final_draw = ImageDraw.Draw(final_img)

                    # Calculate total width of the current line
                    total_line_width = 0
                    word_widths = []
                    for word in current_line:
                        bbox = final_draw.textbbox((0, padding), word, font=font, align="center")
                        w = bbox[2] - bbox[0]
                        word_widths.append(w)
                        total_line_width += w
                    if len(current_line) > 1:
                        total_line_width += word_spacing * (len(current_line) - 1)

                    # Center the text horizontally
                    x = (new_width - total_line_width) // 2
                    y_offset = (new_height - total_height - 10) // 2
                    current_y = padding #+ y_offset

                    # Draw each word with outline and fill (highlighted word in red)
                    for idx, word in enumerate(current_line):
                        color = "red" if word == current_word else "white"
                        # Outline
                        for dx in range(-outline_width, outline_width + 1):
                            for dy in range(-outline_width, outline_width + 1):
                                final_draw.text((x + dx, current_y + dy), word, font=font, fill="black")
                        # Text
                        final_draw.text((x, current_y), word, font=font, fill=color)
                        x += word_widths[idx] + word_spacing

                    filename = f"{start}_word{i}.png"  # Unique filename
                    file_path = os.path.join(output_dir, filename)
                    final_img.save(file_path)
                    print(f"Saved {file_path}")

                    line_index += 1


if __name__ == "__main__":
    caption_list = [
        {"start": "3764.4", "text": "This is a sample caption that is very long and needs to wrap"},
        {"start": "23.8", "text": "Another caption for testing with even more words"}
    ]
    max_width = 1080  # Set maximum width for wrapping
    output_directory = "./caption_images"
    create_caption_images(caption_list, max_width, output_directory)
