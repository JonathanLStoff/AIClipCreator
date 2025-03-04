from moviepy import VideoFileClip, AudioFileClip, CompositeVideoClip, ImageClip, CompositeAudioClip
from moviepy.video.fx import Resize
from pydub import AudioSegment
from clip_creator.conf import LOGGER, REDDIT_TEMPLATE_AUD, REDDIT_TEMPLATE_MUS
import os
from clip_creator.utils.caption_img import (
        create_caption_images_reddit,
        create_emojis,
        remove_curse_words,
    )
def get_clip_duration(video_path):
    with VideoFileClip(video_path) as clip:
        return clip.duration
def get_audio_duration(audio_path):
    audio = AudioSegment.from_file(audio_path)
    return len(audio) / 1000.0
def create_reddit_video(video_path, audio_path, output_path, start_time, end_time, pid, transcript, th, tw, paragraph, parts=1, part_start=[]):
    
    if parts > 1:
        for i, start_section_idx in enumerate(part_start):
            # Setup/Load Audio
            start_section = transcript[start_section_idx].get("start", 0)
            end_idx = -1 if i == parts-1 else part_start[i+1]
            end_time_sec = end_time - start_time if i == parts-1 else transcript[end_idx].get("start", 0)
            temp_audio = CompositeAudioClip(
                    [

                        # TTS Audio
                        AudioFileClip(audio_path).subclipped(start_section, end_time_sec).with_start(0),
                        # Background Music
                        AudioFileClip(REDDIT_TEMPLATE_MUS).subclipped(0, end_time_sec).with_start(0),

                    ]
                    )
            temp_audio.write_audiofile(f"tmp/audios/{pid}_aud_{i}.mp3", codec="libmp3lame")
            
            # Load the video and add the captions
            video = VideoFileClip(video_path).subclipped(start_time+start_section, min(end_time_sec + start_time, end_time)).with_audio(
                AudioFileClip(f"tmp/audios/{pid}_aud_{i}.mp3").with_start(0)
            ).with_effects([Resize(height=th, width=tw)])
            
            # Create the caption clips
            output_dir,cap_clips = create_captions(pid, paragraph=paragraph, transcript=transcript[start_section_idx:end_idx], target_size=(video.h, video.w), part=i)
            final_clip = CompositeVideoClip([video, *cap_clips])
            
            # Write the final video
            final_clip.write_videofile(output_path.replace(f"{pid}", f"{pid}_p{i}"), codec="libx264", audio_codec="libmp3lame")
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
        temp_audio.write_audiofile(f"tmp/audios/{pid}_aud.mp3", codec="libmp3lame")
        video = VideoFileClip(video_path).subclipped(start_time, end_time).with_audio(
            AudioFileClip(f"tmp/audios/{pid}_aud.mp3").with_start(0)
        ).with_effects([Resize(height=th, width=tw)])
        output_dir, cap_clips = create_captions(pid, paragraph=paragraph, transcript=transcript, target_size=(video.h, video.w))
        LOGGER.info("video type: %s", type(video))
        LOGGER.info("cap_clips: %s", type(cap_clips[-1]))
        final_clip = CompositeVideoClip([video]+cap_clips)
        final_clip.write_videofile(output_path, codec="libx264", audio_codec="libmp3lame")
        
        for file in os.listdir(output_dir):
            if pid in file:
                os.remove(os.path.join(output_dir, file))
            
def create_captions(
    prefix: str,
    paragraph: str,
    transcript: list[dict],
    target_size: tuple[int, int],
    output_dir: str = "./tmp/caps_img",
    part=0,
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
    file_to_check = f"word{len((transcript))-5}-{part}.png"
    LOGGER.info("file_to_check and pre: %s %s", file_to_check, prefix)
    not_found = True
    for file in os.listdir(output_dir):
        if file_to_check in file and prefix in file:
            not_found = False
            break
    if not_found:
        create_caption_images_reddit(prefix, transcript, target_size[1], output_dir, part)

    clip_list = []

    for i, section in enumerate(transcript):
        file_name = ""
        for file in os.listdir(output_dir):
            if f"word{i}-{part}.png" in file and prefix in file:
                file_name = file

        if i + 1 >= len(transcript):
            duration = section["duration"] + 1
        else:
            duration = transcript[i + 1]["start"] - section["start"]
            if duration > 3:
                duration = 3
        pos_y = target_size[0] * 2 / 5
        file_path = os.path.join(output_dir, file_name)
        caption_clip = ImageClip(file_path, duration=duration)
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