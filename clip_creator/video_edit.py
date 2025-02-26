import math
import os
import re
import traceback
from random import randint

import numpy as np
import torch
from moviepy import (
    AudioFileClip,
    ColorClip,
    CompositeVideoClip,
    ImageClip,
    TextClip,
    VideoFileClip,
)
from moviepy.video.fx import Crop, Resize
from pydub import AudioSegment
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
from clip_creator.utils.scan_text import find_bad_words
from clip_creator.conf import (
    CODEC,
    E_FONT_PATH,
    EMOJIS_RE,
    FONT_PATH,
    LOGGER,
    LOW_CPU_MEM,
    NUM_CORES,
    WIS_DEVICE,
)
from clip_creator.utils.caption_img import create_caption_images, remove_curse_words


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
    if text.strip() != "":   
        emojis, text = extract_emojis(text)
        text = remove_curse_words(text)
    
    audio_file = f"./tmp/audio_{prefix}.mp3"
    outputa_file = f"./tmp/audioo_{prefix}.mp3"
    clip = VideoFileClip(input_file).subclipped(start_time, end_time)
    full_length = clip.duration
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
    if text.strip() != "":
        rotate_tilt = randint(-10, 10)
        text_commm = TextClip( # img_width, img_height = size
            font=FONT_PATH,
            method="caption",
            size=(
                (
                    int(tw * 0.93)
                    if lines_total > 1
                    else int(((tw / max_chars) * len(text)))
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
        ).rotated(rotate_tilt, expand=True)
        pos_x = (
            cropped_clip.w / 2
            - (
                int(target_h * 0.93)
                if lines_total > 1
                else int(((target_h / max_chars) * len(text)) / 2)
            )
        ) / 3
        text_commm_pos = text_commm.with_position((pos_x, int(th / 7)))
        if len(emojis) > 5:
            emojis = emojis[:5]
        
        if len(emojis) > 0:
            # Emoji text clip
            emoji_commm = TextClip( #img_width, img_height = size
                font=E_FONT_PATH,
                method="caption",
                size=(
                    int(len(emojis) * pixels_per_char),
                    int(pixels_per_char * 1.5),
                ),
                text=emojis.strip(),
                margin=(5, 20),
                font_size=90,
                bg_color="white",
                color=(255, 0, 0),
                duration=cropped_clip.duration,
            ).with_position((text_commm.w/2, int((th / 7) - (text_commm.size[1]/2)))).rotated(rotate_tilt, expand=True) #Place above normal text.
    cropped_clip.audio.write_audiofile(
        audio_file, codec="libmp3lame"
    )
    
    #########################################
    # Make my own transcription for captions
    #########################################
    number_runs = math.ceil(cropped_clip.duration / 30)
    true_transcript = []
    for i in range(number_runs):
        segment_start = i * 30
        with AudioFileClip(audio_file) as full_audio:
            segment_end = min((i + 1) * 30, full_audio.duration)
            segment_file = f"./tmp/audios/audio_{prefix}_segment_{i}.mp3"
            segment = full_audio.subclipped(segment_start, segment_end)
            segment.write_audiofile(segment_file, codec="libmp3lame", logger=None)

        transcript_segment = get_word_timestamps_openai(segment_file, audio_clip_length=full_audio.duration,device=WIS_DEVICE, time_add=(i * 30))
        # Adjust timestamps for the segment offset
        true_transcript.extend(transcript_segment)
        os.remove(segment_file)
        
    true_transcript, audio_file = censor_words(true_transcript, audio_file, outputa_file)
    if text.strip() != "" and len(emojis) > 0:
        final_clip = CompositeVideoClip(
            [
                cropped_clip.with_position("center").with_effects([Resize(0.7)]),
                text_commm_pos,
                emoji_commm,
            ],
            size=target_size,
        )
    elif text.strip() != "":
        final_clip = CompositeVideoClip(
            [cropped_clip.with_position("center").with_effects([Resize(0.7)]), text_commm_pos],
            size=target_size,
        )
    else:
        final_clip = cropped_clip.with_position("center").with_effects([Resize(0.7)])
        
    output_dir_img, clip_list = create_captions(
        prefix, true_transcript, target_size
    )
    
    final_clip = CompositeVideoClip(
        [final_clip.with_layer_index(2), *clip_list],
        bg_color=(0, 0, 0),
        size=target_size,
    )
    final_clip = final_clip.subclipped(0, full_length).with_audio(AudioFileClip(audio_file))
    final_clip.write_videofile(
        output_file, codec=CODEC, preset="fast", ffmpeg_params=["-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k"], threads=NUM_CORES
    )
    # Remove caption images
    for img in os.listdir(output_dir_img):
        if prefix in str(img):
            os.remove(os.path.join(output_dir_img, img))
    os.remove(audio_file)
    return output_file, true_transcript

def censor_words(transcript, audio_file, output_file):
    
    ts_bw, ftranscript = find_bad_words(transcript)
    audio_file_out = mute_sections(audio_file, output_file, ts_bw)
    return ftranscript, audio_file_out

def mute_sections(input_file, output_file, mute_section):
    """
    Mute specific sections of an MP3 file
    
    Parameters:
    input_file (str): Path to input MP3 file
    output_file (str): Path to save the edited file
    mute_sections (list): List of tuples with (start_ms, end_ms) to mute
    """
    # Load the audio file
    audio = AudioSegment.from_file(input_file, format="mp3")
    
    # Convert audio to numpy array for easier manipulation
    samples = np.array(audio.get_array_of_samples())
    
    # Get frame rate and channels info
    frame_rate = audio.frame_rate
    channels = audio.channels
    
    # Calculate samples per millisecond
    samples_per_ms = frame_rate * channels / 1000
    
    # Mute the specified sections
    for start_ms, end_ms in mute_section:
        # Convert milliseconds to sample indices
        start_sample = int(start_ms * samples_per_ms)
        end_sample = int(end_ms * samples_per_ms)
        
        # Ensure indices are within bounds
        start_sample = max(0, start_sample)
        end_sample = min(len(samples), end_sample)
        
        # Set the samples in the section to zero (mute)
        samples[start_sample:end_sample] = 0
    
    # Create a new audio segment from the modified samples
    modified_audio = audio._spawn(samples.tobytes())
    
    # Export the modified audio
    modified_audio.export(output_file, format="mp3")
    LOGGER.info(f"Successfully created edited file: {output_file}")
    return output_file
def extract_emojis(text):
    """
    Finds and returns all emojis in a given string as a single string,
    and returns the text with emojis removed.

    Args:
        text (str): The input string.

    Returns:
        tuple: A tuple containing:
            - A string of all emojis found, concatenated.
            - The input string with emojis removed.
    """
    emoji_pattern = EMOJIS_RE
    emojis = emoji_pattern.findall(text)
    emoji_string = "".join(emojis)  # Concatenate emojis into a single string
    text_without_emojis = emoji_pattern.sub("", text)  # Remove emojis from text
    return emoji_string, text_without_emojis
def create_captions(
    prefix: str,
    transcript: list[dict],
    target_size: tuple[int, int],
    output_dir: str = "./tmp/caps_img"
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
                - 'text' (str): The caption word for the segment.
                - 'start' (str): The start time of the segment, used for naming image files.
                - 'duration' (float): The duration of the caption segment.
        video_obj (VideoFileClip): The video clip (from moviepy) onto which the caption images
            will be overlaid.
        output_dir (str, optional): The directory path where the generated caption images are
            saved. Defaults to "./tmp/caps_img".
    Returns:
        VideoFileClip: The modified video clip with the caption image clips composited on top.
    """
    
    
    create_caption_images(prefix, transcript, target_size[0], output_dir)
    
    clip_list = []
    
    for i, section in enumerate(transcript):
        file_name = ""
        for file in os.listdir(output_dir):
            if f"word{i}.jpg" in file and prefix in file:
                file_name = file
        #if section["end"] > video_obj.duration:
            
        if i+1>=len(transcript):
            duration = section["duration"] + 1
        else:
            duration = transcript[i+1]["start"] - section["start"]
            #LOGGER.info("transcript[i+1]: %s", transcript[i+1])
            if duration > 3:
                duration = 3
                
        file_path = os.path.join(output_dir, file_name)
        caption_clip = ImageClip(file_path, duration=duration)
        # Position the image so that its center is at 6/7th of the video’s height.
        pos_y = int(target_size[1] * 11 / 14 - caption_clip.h / 2)
        caption_clip = caption_clip.with_start(section["start"]).with_position(("center", pos_y)).with_layer_index(1)

        # Composite the caption image onto the video.
        clip_list.append(caption_clip)


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

def get_word_timestamps_openai(audio_path, time_add, model_name="facebook/seamless-m4t-v2-large", device="cuda:0", audio_clip_length:float=0, compute_type:str="float16", chunk_length_s:int=20):  # Use "cpu" if no GPU
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
    retries = 0
    while True:
        device = "cuda:0" if torch.cuda.is_available() else "cpu"
        torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

        model_id = "openai/whisper-large-v3-turbo"

        model = AutoModelForSpeechSeq2Seq.from_pretrained(
            model_id,
            torch_dtype=torch_dtype,
            low_cpu_mem_usage=LOW_CPU_MEM,
            use_safetensors=True,
            attn_implementation="eager"
        )
        model.to(device)

        processor = AutoProcessor.from_pretrained(model_id)

        pipe = pipeline(
            "automatic-speech-recognition",
            model=model,
            tokenizer=processor.tokenizer,
            feature_extractor=processor.feature_extractor,
            torch_dtype=torch_dtype,
            device=device,
            stride_length_s=chunk_length_s * 0.15,  # 15% overlap for better continuity
            chunk_length_s=chunk_length_s,
        )

        result = pipe(
            audio_path,
            batch_size=8,
            return_timestamps="word",
        )
        LOGGER.debug("Transcription %s", result)
        # Check if length is greater than 10 seconds and has at least 3 words
        length_a = get_audio_length(audio_path)
        
        if length_a > 10 and len(result['chunks']) < 3 and retries < 3:
            retries += 1
            continue
        break
    outout = []
    for r in result['chunks']:
        
        start, end = r['timestamp']
        new_start = time_add+start
        new_end = time_add+audio_clip_length if not end else time_add+end
        
        new_duration = audio_clip_length - start if not end else (end - start if end - start > 0 else 0.1)
        outout.append({
            "text": r['text'],
            "start": new_start,
            "end": new_end,
            "duration": new_duration,
        })
    return outout
def get_audio_length(file_path)->float:
    """
    Get the length of an audio file in both milliseconds and formatted time
    
    Parameters:
    file_path (str): Path to the audio file
    
    Returns:
    tuple: (length_ms, formatted_length)
    """
    try:
        audio = AudioSegment.from_file(file_path)
        length_ms = len(audio)
        formatted_length = (length_ms/1000)
        return float(formatted_length)
    except Exception as e:
        LOGGER.info(f"Error getting audio length: {e}")
        return 0
def fix_video_grb(input_file):
    """
    Fixes the color space of a video file.
    Parameters:
        • input_file  : path to the input video file.
        • output_file : where to write the fixed video.
    """
    clip = VideoFileClip(input_file)
    output_file = input_file.replace(".mp4", "_fixed.mp4")
    clip.write_videofile(output_file, codec="libx264", preset="fast", ffmpeg_params=["-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k"], threads=NUM_CORES)

if __name__ == "__main__":
    file_fix = [
        "tmp/clips/5FctraXMT-E.mp4",
        "tmp/clips/_96ADhbwQJU.mp4",
        "tmp/clips/gu4vGTxm6gg.mp4",
        "tmp/clips/uDqN4MIdIXQ.mp4",
                ]
    for file in file_fix:
        fix_video_grb(file)
