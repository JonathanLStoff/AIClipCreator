import os
from random import randint
import librosa
import whisperx
from moviepy import ColorClip, CompositeVideoClip, ImageClip, TextClip, VideoFileClip, AudioFileClip
from moviepy.video.fx import Crop, Resize

from clip_creator.conf import CODEC, FFMPEG_PARAMS, LOGGER, NUM_CORES, FONT_PATH
from clip_creator.utils.caption_img import create_caption_images, create_caption_images_thread


def edit_video(
    prefix: str,
    input_file,
    output_file,
    zoom=1.0,
    target_size=(720, 1280),
    start_time=0,
    end_time=60,
    text: str = "",
    transcript: list[dict] | None = None,
):
    """
    Crops a landscape video to a portrait orientation and “zooms in” on the center portion.
    The final video has a black background. Parameters:
      • input_file   : path to the input video file.
      • output_file  : where to write the edited video.
      • zoom         : zoom factor (>1 zooms in more on a smaller crop area).
      • target_size  : tuple (width, height) for the portrait video.
    """
    audio_file = f"./tmp/audio_{prefix}.mp3"
    clip = VideoFileClip(input_file).subclipped(start_time, end_time)
    LOGGER.info(f"Video duration: {end_time-start_time} seconds")
    iw, ih = clip.size
    target_h, target_w = target_size
    target_aspect = target_w / target_h

    # Determine the maximum crop that fits the input with the target aspect.
    if ih * target_aspect <= iw:
        # Use full height.
        base_crop_w = ih * target_aspect
        base_crop_h = ih
    else:
        # Use full width.
        base_crop_w = iw
        base_crop_h = iw / target_aspect

    # Apply zoom: a zoom factor > 1 means we crop a smaller region
    crop_w = base_crop_w / zoom
    crop_h = base_crop_h / zoom

    # Center crop coordinates.
    center_x, center_y = iw / 2, ih / 2
    x1 = center_x - crop_w / 2
    y1 = center_y - crop_h / 2
    x2 = center_x + crop_w / 2
    y2 = center_y + crop_h / 2

    cropped = Crop(x1=x1, y1=y1, x2=x2, y2=y2)
    cropped_clip = cropped.apply(clip)

    tw, th = target_size
    # Create a black background and composite the result on it.
    # background = ColorClip(size=target_size, color=(0, 0, 0), duration=cropped_clip.duration).with_fps(cropped_clip.fps)
    # final_clip = background.overlay(cropped_clip, position=("center", "center"))
    # 3 words per line unless the total of those words is less than 19
    pixels_per_char = 90
    lines_total = 0
    chars_in_line = 0
    max_chars = 19
    for i, _chared in enumerate(text):
        chars_in_line += 1
        if chars_in_line > max_chars:
            lines_total += 1
            chars_in_line = 0
        if lines_total > 6:
            text = text[:i] + "..."
            break
    text_commm = TextClip(
        font=FONT_PATH,
        method="caption",
        size=(
            (
                int(target_h * 0.93)
                if lines_total > 1
                else int(((target_h / max_chars) * len(text)) / 2)
            ),
            int(
                lines_total * pixels_per_char
                if lines_total > 1
                else int(pixels_per_char * 1.2)
            ),
        ),
        text=text,
        margin=(5, 30),
        font_size=90,
        bg_color="white",
        color=(0, 0, 0),
        duration=cropped_clip.duration,
    ).rotated(randint(-10, 10), expand=True)
    pos_x = (
        cropped_clip.w / 2
        - (
            int(target_h * 0.93)
            if lines_total > 1
            else int(((target_h / max_chars) * len(text)) / 2)
        )
    ) / 3
    text_commm_pos = text_commm.with_position((pos_x, int(th / 7)))
    cropped_clip.audio.write_audiofile(
        audio_file, codec="libmp3lame"
    )
    
    ######################################
    # Make my own transcription for captions
    ######################################
    true_transcript = get_word_timestamps(audio_file, device="cpu")
    LOGGER.info(f"Transcript: {true_transcript}")
    exit()
    final_clip = CompositeVideoClip(
        [
            cropped_clip.with_position("center").with_effects([Resize(0.7)]),
            text_commm_pos,
        ],
        size=target_size,
    )
    output_dir_img, clip_list = create_captions(
        prefix, true_transcript, final_clip, ffmpeg_params=FFMPEG_PARAMS
    )
    
    final_clip = CompositeVideoClip(
        [final_clip.with_layer_index(2), *clip_list],
        bg_color=(0, 0, 0),
    )
    final_clip = final_clip.with_audio(AudioFileClip(audio_file))
    final_clip.write_videofile(
        output_file, codec=CODEC, preset="fast", ffmpeg_params=FFMPEG_PARAMS, threads=NUM_CORES
    )
    # Remove caption images
    for img in os.listdir(output_dir_img):
        if prefix in str(img):
            os.remove(os.path.join(output_dir_img, img))
    os.remove(audio_file)


def create_captions(
    prefix: str,
    transcript: list[dict],
    video_obj: VideoFileClip,
    output_dir: str = "./tmp/caps_img",
    ffmpeg_params: list | None = None,
):
    """
    Creates caption image clips from a transcript and overlays them onto a video clip.
    This function generates caption images for each section in the transcript (by calling
    an external function 'create_caption_images'), then creates individual image clips for
    each word in the section. Each image clip is placed at a fixed vertical position on the
    video (6/7th of the video height, centered horizontally) and is composited over the
    existing video clip. The duration of each caption clip is evenly divided among the words
    in the section's text.
    Args:
        transcript (list[dict]): A list of dictionaries where each dictionary represents a
            segment of the transcript. Each dictionary should contain:
                - 'text' (str): The caption text for the segment.
                - 'start' (str): The start time of the segment, used for naming image files.
                - 'duration' (float): The duration of the caption segment.
        video_obj (VideoFileClip): The video clip (from moviepy) onto which the caption images
            will be overlaid.
        output_dir (str, optional): The directory path where the generated caption images are
            saved. Defaults to "./tmp/caps_img".
    Returns:
        VideoFileClip: The modified video clip with the caption image clips composited on top.
    """
    if ffmpeg_params is None:
        ffmpeg_params = ["-c:v", "h264_videotoolbox"]
    create_caption_images(prefix, transcript, video_obj.size[0], output_dir)
    clip_list = []
    clip_start_time = 0
    first_start_time = transcript[0]["start"]
    
    for _i, section in enumerate(transcript):
        clip_start_time = section["start"] - first_start_time
        for j in range(len(section["text"].split())):
            file_name = f"{prefix}{str(section['start']).replace('.', '-')}_word{j}.jpg"

            file_path = os.path.join(output_dir, file_name)
            duration = section["duration"] / len(section["text"].split())
            # Create an image clip from the generated file with duration matching the video.
            caption_clip = ImageClip(file_path, duration=duration)

            caption_clip = caption_clip.with_effects([Resize(2)])
            # Position the image so that its center is at 6/7th of the video’s height.
            pos_y = int(video_obj.h * 6 / 7 - caption_clip.h / 2)
            caption_clip = caption_clip.with_start(clip_start_time).with_position(("center", pos_y)).with_layer_index(1)

            # Composite the caption image onto the video.
            clip_list.append(caption_clip)
            clip_start_time += duration

    return output_dir, clip_list


def get_first_frame_screenshot(input_file, screenshot_path):
    """
    Extracts the first frame from the video and saves it as an image.
    Parameters:
        • input_file     : path to the input video file.
        • screenshot_path: file path for the output image.
    """
    clip = VideoFileClip(input_file)
    # Save the first frame at time t = 0.0 seconds.
    clip.save_frame(screenshot_path, t=0.0)


def crop_video_by_coords(input_file, output_file, x1, y1, x2, y2):
    """
    Crops a video using the provided top-left (x1, y1) and bottom-right (x2, y2) coordinates.
    Parameters:
        • input_file  : path to the input video file.
        • output_file : where to write the cropped video.
        • x1, y1      : coordinates of the top-left corner of the crop box.
        • x2, y2      : coordinates of the bottom-right corner of the crop box.
    """
    clip = VideoFileClip(input_file)
    cropped_clip = clip.crop(x1=x1, y1=y1, x2=x2, y2=y2)
    cropped_clip.write_videofile(output_file, codec="libx264")


def crop_video_into_another(
    background_file, overlay_file, output_file, zoom=1.0, position="center"
):
    """
    Crops the overlay video (using the specified zoom factor) and composites it onto the background video.
    Parameters:
        • background_file: path to the background video.
        • overlay_file   : path to the video to be cropped and overlaid.
        • output_file    : where to write the composited video.
        • zoom           : zoom factor (>1 crops a smaller region from the overlay).
        • position       : position for the overlay (any valid moviepy position, e.g., "center", (x, y)).
    """
    bg_clip = VideoFileClip(background_file)
    ov_clip = VideoFileClip(overlay_file)

    # Determine crop dimensions on the overlay clip.
    iw, ih = ov_clip.size
    crop_w = iw / zoom
    crop_h = ih / zoom

    # Calculate center crop coordinates.
    center_x, center_y = iw / 2, ih / 2
    x1 = center_x - crop_w / 2
    y1 = center_y - crop_h / 2
    x2 = center_x + crop_w / 2
    y2 = center_y + crop_h / 2

    cropped_overlay = ov_clip.fx(vfx.crop, x1=x1, y1=y1, x2=x2, y2=y2)
    # cropped_overlay = ov_clip.crop(x1=x1, y1=y1, x2=x2, y2=y2)

    # Ensure the overlay duration matches the background's.
    cropped_overlay = cropped_overlay.set_duration(bg_clip.duration)

    # Composite the cropped overlay over the background at the given position.
    composite_clip = CompositeVideoClip(
        [bg_clip, cropped_overlay.set_position(position)], size=bg_clip.size
    )
    composite_clip.write_videofile(output_file, codec="libx264")


def add_text_to_video(
    video_path,
    text,
    font,
    fontsize,
    color,
    outline_color,
    outline_width,
    position,
    rotation,
):
    """
    Adds text to a video with customizable rotation, position, outline, and font.

    Args:
        video_path: Path to the video file.
        text: The text to be added.
        font: The font to use (e.g., "Arial", "Impact", path to a .ttf file).
        fontsize: The font size.
        color: The text color (e.g., "white", "red", "#00FF00").
        outline_color: The color of the text outline.
        outline_width: The width of the text outline.
        position: The position of the text (e.g., "center", ("left", "top"), (x,y) coordinates).
        rotation: The rotation angle in degrees (e.g., 0, 90, 180).
    """

    try:
        clip = VideoFileClip(video_path)
    except Exception as e:
        print(f"Error opening video: {e}")
        return

    txt_clip = TextClip(
        text,
        font=font,
        fontsize=fontsize,
        color=color,
        stroke_color=outline_color,  # Outline color
        stroke_width=outline_width,
    )  # Outline width

    txt_clip = txt_clip.set_pos(position).set_duration(clip.duration).rotate(rotation)

    final_clip = CompositeVideoClip([clip, txt_clip])

    # You can choose the output video codec and quality
    output_path = "output_video.mp4"  # or any other name/path
    final_clip.write_videofile(
        output_path, codec="libx264", fps=clip.fps, audio_codec="aac"
    )  # Adjust codec if needed

    clip.close()  # Close the video clip to release resources
    final_clip.close()  # Close the final clip
    print(f"Video with text saved to {output_path}")


def get_word_timestamps(audio_path, model_name="medium", device="cuda"):  # Use "cpu" if no GPU
    """
    Gets word-level timestamps from an audio clip using WhisperX.

    Args:
        audio_path: Path to the audio file.
        model_name: The Whisper model size to use ("tiny", "base", "small", "medium", "large-v1", "large-v2").
        device: "cuda" for GPU or "cpu" for CPU.

    Returns:
        A list of dictionaries, where each dictionary contains:
            "word": The word.
            "start": Start time of the word in seconds (float).
            "end": End time of the word in seconds (float).
        Returns an empty list if there's an error.
    """
    try:
        # 1. Load audio
        LOGGER.info(f"Loading audio from {audio_path}")
        audio, sr = librosa.load(audio_path)  # librosa handles various audio formats

        # 2. Load WhisperX model
        model = whisperx.load_model(model_name, device)
        LOGGER.info(f"Transcribing audio using {model_name} model")
        # 3. Transcribe the audio
        result = model.transcribe(audio, batch_size=8)  # Adjust batch_size if needed
        LOGGER.info("Transcription complete")
        # 4. Align the transcript to the audio (important for accurate timestamps)
        model_align, metadata = whisperx.load_align_model(model_name, device)
        result = whisperx.align(result["segments"], model_align, metadata, audio, device, return_metadata=False)

        word_timestamps = []
        for segment in result["segments"]:
            for word_info in segment["words"]:
                word = word_info["word"]
                start = word_info["start"]
                end = word_info["end"]
                word_timestamps.append({
                    "text": word,
                    "start": start,
                    "end": end,
                    "duration": end - start,
                })

        return word_timestamps

    except Exception as e:
        print(f"An error occurred: {e}")
        return []
# Example usage:
if __name__ == "__main__":
    input_video_path = "input_video.mp4"  # Replace with your landscape video file
    output_video_path = "output_portrait.mp4"
    edit_video(input_video_path, output_video_path, zoom=1.2, target_size=(720, 1280))
