from moviepy import VideoFileClip, AudioFileClip, CompositeVideoClip, ImageClip, CompositeAudioClip
from moviepy.video.fx import Resize
from pydub import AudioSegment
from clip_creator.conf import LOGGER, REDDIT_TEMPLATE_AUD, REDDIT_TEMPLATE_MUS
import os
from clip_creator.utils.caption_img import (
        create_caption_images,
        create_emojis,
        remove_curse_words,
    )
def get_clip_duration(video_path):
    with VideoFileClip(video_path) as clip:
        return clip.duration
def get_audio_duration(audio_path):
    audio = AudioSegment.from_file(audio_path)
    return len(audio) / 1000.0
def create_reddit_video(video_path, audio_path, output_path, start_time, end_time, pid, transcript, th, tw, paragraph, parts=1):
    
    if parts > 1:
        for i in range(parts):
            temp_audio = CompositeAudioClip(
                    [

                        # TTS Audio
                        AudioFileClip(audio_path).subclipped(i*61, min((1+i)*61, (end_time-start_time))).with_start(0),
                        # Background Music
                        AudioFileClip(REDDIT_TEMPLATE_MUS).subclipped(0, min((1+i)*61, (end_time-start_time))).with_start(0),

                    ]
                    )
            temp_audio.write_audiofile(f"tmp/audios/{pid}_aud_{i}.wav")
            video = VideoFileClip(video_path).subclipped(start_time+61*i, min(start_time+61*(i+1), end_time)).with_audio(
                AudioFileClip(f"tmp/audios/{pid}_aud_{i}.wav").with_start(0)
            ).with_effects([Resize(height=th, width=tw)])
            output_dir,cap_clips = create_captions(pid, paragraph=paragraph, transcript=transcript, target_size=(th, tw))
            LOGGER.info("video type: %s", type(video))
            LOGGER.info("cap_clips: %s", type(cap_clips[-1]))
            final_clip = CompositeVideoClip([video, *cap_clips])
            final_clip.write_videofile(output_path.replace(f"{pid}", f"{pid}_p{i}"), codec="libx264")
            for file in os.listdir(output_dir):
                if pid in file:
                    os.remove(os.path.join(output_dir, file))
    else:
        temp_audio = CompositeAudioClip(
                [

                    # TTS Audio
                    AudioFileClip(audio_path).with_start(0),
                    # Background Music
                    AudioFileClip(REDDIT_TEMPLATE_MUS).subclipped(0, (end_time-start_time)).with_start(0),
                    
                    
                ])
        temp_audio.write_audiofile(f"tmp/audios/{pid}_aud.wav")
        video = VideoFileClip(video_path).subclipped(start_time, end_time).with_audio(
            AudioFileClip(f"tmp/audios/{pid}_aud.wav").with_start(0)
        ).with_effects([Resize(height=th, width=tw)])
        output_dir, cap_clips = create_captions(pid, paragraph=paragraph, transcript=transcript, target_size=(th, tw))
        LOGGER.info("video type: %s", type(video))
        LOGGER.info("cap_clips: %s", type(cap_clips[-1]))
        final_clip = CompositeVideoClip([video]+cap_clips)
        final_clip.write_videofile(output_path, codec="libx264")
        
        for file in os.listdir(output_dir):
            if pid in file:
                os.remove(os.path.join(output_dir, file))
            
def create_captions(
    prefix: str,
    paragraph: str,
    transcript: list[dict],
    target_size: tuple[int, int],
    output_dir: str = "./tmp/caps_img",
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
    file_to_check = f"word{len((paragraph.split()))-5}.jpg"
    LOGGER.info("file_to_check and pre: %s %s", file_to_check, prefix)
    not_found = True
    for file in os.listdir(output_dir):
        if file_to_check in file and prefix in file:
            not_found = False
            break
    if not_found:
        create_caption_images(prefix, transcript, target_size[0], output_dir)

    clip_list = []

    for i, section in enumerate(transcript):
        file_name = ""
        for file in os.listdir(output_dir):
            if f"word{i}.jpg" in file and prefix in file:
                file_name = file
        # if section["end"] > video_obj.duration:

        if i + 1 >= len(transcript):
            duration = section["duration"] + 1
        else:
            duration = transcript[i + 1]["start"] - section["start"]
            # LOGGER.info("transcript[i+1]: %s", transcript[i+1])
            if duration > 3:
                duration = 3

        file_path = os.path.join(output_dir, file_name)
        caption_clip = ImageClip(file_path, duration=duration)
        # Position the image so that its center is at 6/7th of the video’s height.
        pos_y = int(target_size[1] / 2 - caption_clip.h)
        caption_clip = (
            caption_clip.with_start(section["start"])
            .with_position(("center", pos_y))
            .with_layer_index(1)
        )

        # Composite the caption image onto the video.
        clip_list.append(caption_clip)

    return output_dir, clip_list
    
if __name__ == "__main__":
    video_path = "path/to/your/video.mp4"  # Replace with your video file path
    duration = get_clip_duration(video_path)
    print(f"Video duration: {duration} seconds")