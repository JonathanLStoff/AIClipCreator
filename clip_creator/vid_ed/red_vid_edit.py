import os
import traceback
import time

from moviepy import (
    AudioFileClip,
    CompositeAudioClip,
    CompositeVideoClip,
    ImageClip,
    VideoFileClip,
)
from moviepy.video.fx import Resize
from PIL import Image
from pydub import AudioSegment

from clip_creator.conf import (
    LOGGER,
    RED_COM_DELAY,
    REDDIT_TEMPLATE_MUS,
)
from clip_creator.utils.caption_img import (
    create_caption_images_reddit,
    create_caption_images_aiyt,
    create_caption_images_reddit_com,
)
from clip_creator.utils.scan_text import remove_non_letters, swap_words_numbers, remove_non_numbers


def get_clip_duration(video_path):
    with VideoFileClip(video_path) as clip:
        return clip.duration


def get_audio_duration(audio_path):
    if not audio_path:
        return None
    audio = AudioSegment.from_file(audio_path)
    return len(audio) / 1000.0


def create_postimg_clip(post_png_file, transcript, title, th=1920, tw=1080):
    start = 0
    title = swap_words_numbers(remove_non_letters(title.upper()))
    for _i, section in enumerate(transcript):
        start = section["start"]
        if section["text"] not in title.upper():
            LOGGER.info("section text: [%s] not in [%s]", section["text"], title)
            break
    if transcript[-1]["start"] == start:
        start = len(title) * (160 / 60)
    clip = (
        ImageClip(post_png_file, duration=start)
        .with_position("center", "center")
        .with_layer_index(4)
        .with_start(0)
        .with_effects([Resize(width=tw)])
        .with_effects([Resize(0.90)])
    )
    LOGGER.info("POST SIZE: %s", clip.size)
    return clip, start


def create_reddit_video(
    video_path,
    audio_path,
    output_path,
    start_time,
    end_time,
    pid,
    transcript,
    th,
    tw,
    paragraph,
    parts=1,
    part_start=None,
    post_png_file=None,
    title="",
):
    if part_start is None:
        part_start = []
    use_hi = False
    while True:
        rezivid = Resize(height=th) if use_hi else Resize(width=tw)

        try:
            clip_pt_img, end_image_time = create_postimg_clip(
                post_png_file, transcript, title, th, tw
            )

            if parts > 1:
                for i, start_section_idx in enumerate(part_start):
                    LOGGER.info("part_start: %s", part_start)
                    # repostion the clip_pt_img
                    if i != 0:
                        clip_pt_img = (
                            clip_pt_img.with_start(0)
                            .with_position("center", th / 20)
                            .with_layer_index(4)
                        )

                    # Setup/Load Audio
                    start_section = transcript[start_section_idx].get("start", 0)
                    end_idx = -1 if i == parts - 1 else part_start[i + 1]
                    end_time_sec = (
                        end_time - start_time
                        if i == parts - 1
                        else transcript[end_idx].get("start", 0)
                    )
                    temp_audio = CompositeAudioClip([
                        # TTS Audio
                        AudioFileClip(audio_path)
                        .subclipped(start_section, end_time_sec)
                        .with_start(0),
                        # Background Music
                        AudioFileClip(REDDIT_TEMPLATE_MUS)
                        .subclipped(0, end_time_sec)
                        .with_start(0),
                    ])
                    temp_audio.write_audiofile(
                        f"tmp/audios/{pid}_aud_{i}.mp3", codec="libmp3lame"
                    )

                    # Load the video and add the captions
                    video = (
                        VideoFileClip(video_path)
                        .subclipped(
                            start_time + start_section,
                            min(end_time_sec + start_time, end_time),
                        )
                        .with_audio(
                            AudioFileClip(f"tmp/audios/{pid}_aud_{i}.mp3").with_start(0)
                        )
                        .with_effects([rezivid])
                    )
                    LOGGER.info("rsize: %s", rezivid.new_size)

                    # Create the caption clips
                    output_dir, cap_clips, _, _ = create_captions(
                        pid,
                        paragraph=paragraph,
                        transcript=transcript[start_section_idx:end_idx],
                        target_size=(video.h, video.w),
                        part=i,
                        end_image_time=end_image_time,
                        parts_offset=start_section,
                    )
                    final_clip = CompositeVideoClip([video, clip_pt_img, *cap_clips])

                    # Write the final video
                    final_clip.write_videofile(
                        output_path.replace(f"{pid}", f"{pid}_p{i}"),
                        codec="libx264",
                        audio_codec="libmp3lame",
                    )
                    for file in os.listdir(output_dir):
                        if pid in file:
                            os.remove(os.path.join(output_dir, file))

            else:
                temp_audio = CompositeAudioClip([
                    # TTS Audio
                    AudioFileClip(audio_path).with_start(0),
                    # Background Music
                    AudioFileClip(REDDIT_TEMPLATE_MUS)
                    .subclipped(0, (end_time - start_time))
                    .with_start(0),
                ])

                temp_audio.write_audiofile(
                    f"tmp/audios/{pid}_aud.mp3", codec="libmp3lame"
                )
                video = (
                    VideoFileClip(video_path)
                    .subclipped(start_time, end_time)
                    .with_audio(
                        AudioFileClip(f"tmp/audios/{pid}_aud.mp3").with_start(0)
                    )
                    .with_effects([rezivid])
                )
                LOGGER.info("Pvideo: %s", video.size)

                output_dir, cap_clips, _, _ = create_captions(
                    pid,
                    paragraph=paragraph,
                    transcript=transcript,
                    target_size=(tw, th),
                    end_image_time=end_image_time,
                )
                LOGGER.info("Pvideo: %s", video.size)
                final_clip = CompositeVideoClip([video, clip_pt_img, *cap_clips])
                LOGGER.info("Pfinal_clip: %s", final_clip.size)
                final_clip.write_videofile(
                    output_path,
                    pixel_format="yuv420p",
                    codec="libx264",
                    audio_codec="libmp3lame",
                    ffmpeg_params=[
                        #"-crf",
                        #"23",
                        "-vf",
                        "format=yuv420p",  # Force video format conversion
                        "-profile:v",
                        "baseline",  # Set the H.264 profile to baseline
                        "-loglevel", 
                        "quiet"
                    ],
                )

                for file in os.listdir(output_dir):
                    if pid in file:
                        os.remove(os.path.join(output_dir, file))
            try:
                os.remove(post_png_file)
            except:
                pass
        except Exception as e:
            if "divisible by 2" in str(e):
                LOGGER.error("Error: %s", e)
                use_hi = not use_hi
                continue
            else:
                break
        break

def create_postimg_clip_aiyt(post_png_file, transcript, title, th=1920, tw=1080, adjust=0, first_part=False, title_len=0):
    start = 0
    title = swap_words_numbers(remove_non_letters(title.upper()))

    clip = (
        ImageClip(post_png_file, duration=title_len)
        .with_position("center", "center")
        .with_layer_index(4)
        .with_start(0)
        .with_effects([Resize(width=tw)])
        .with_effects([Resize(0.90)])
    )
    LOGGER.info("POST SIZE: %s", clip.size)
    
    return clip, start
def create_reddit_video_aiyt(
    video_path,
    audio_path,
    output_path,
    start_time,
    end_time,
    pid,
    transcript,
    th,
    tw,
    part_start=None,
    part_end=None,
    adjust=0,
    first_part=False,
    post_png_file=None,
    title="",
    title_len=0,
):
    if part_start is None:
        part_start = []
    use_hi = False
    while True:
        rezivid = Resize(height=th) if use_hi else Resize(width=tw)

        try:
            clip_pt_img, end_image_time = create_postimg_clip_aiyt(
                post_png_file, transcript, title, th, tw, adjust, first_part, title_len
            )

            
            temp_audio = CompositeAudioClip([
                # TTS Audio
                AudioFileClip(audio_path).subclipped(part_start, part_end).with_start(0),
                # Background Music
                AudioFileClip(REDDIT_TEMPLATE_MUS)
                .subclipped(0, (part_end - part_start))
                .with_start(0),
            ])
            LOGGER.info("temp_audio: %s", temp_audio.duration)
            LOGGER.info("temp_audio: start %s, end %s", part_start, part_end)
            temp_audio.write_audiofile(
                f"tmp/audios/{pid}_aud.mp3", codec="libmp3lame"
            )
            video = (
                VideoFileClip(video_path)
                .subclipped(start_time, end_time)
                .with_audio(
                    AudioFileClip(f"tmp/audios/{pid}_aud.mp3").with_start(0)
                )
                .with_effects([rezivid])
            )
            LOGGER.info("Pvideo: %s", video.size)

            output_dir, cap_clips, _, _ = create_captions_aiyt(
                pid,
                transcript=transcript,
                target_size=(tw, th),
                end_image_time=end_image_time,
                adjust=adjust,
                title_len=title_len,
            )
            LOGGER.info("Pvideo: %s", video.size)
            final_clip = CompositeVideoClip([video, clip_pt_img, *cap_clips])
            LOGGER.info("Pfinal_clip: %s", final_clip.size)
            
            final_clip.write_videofile(
                output_path,
                pixel_format="yuv420p",
                codec="libx264",
                audio_codec="libmp3lame",
                ffmpeg_params=[
                    #"-crf",
                    #"23",
                    "-vf",
                    "format=yuv420p",  # Force video format conversion
                    "-profile:v",
                    "baseline",  # Set the H.264 profile to baseline
                    "-loglevel", 
                    "quiet"
                ],
            )

            for file in os.listdir(output_dir):
                if pid in file:
                    os.remove(os.path.join(output_dir, file))
            try:
                os.remove(post_png_file)
            except:
                pass
        except Exception as e:
            if "divisible by 2" in str(e):
                LOGGER.error("Error: %s", e)
                use_hi = not use_hi
                continue
            else:
                LOGGER.error("Error: %s", traceback.format_exc())
                break
            
        break


def create_postimg_clip_com(chunks: dict, tw=1080, th=1920):
    start = 0
    title_img_stop = 0
    clips_list = []
    paths = []
    full_transcript = []
    for cid, chunk in chunks.items():
        if chunk["idx"] != 0:
            skip_next = False
            for i, script_p in enumerate(chunk["ascript"]):
                if skip_next:
                    skip_next = False
                    continue
                if i == 0:
                    
                    if chunk['idx'] > 10 and not chunk["idx"] % 10 == 0 and not len(chunk["ascript"]) <= 1:
                        LOGGER.info("script length: %s", len(chunk["ascript"]))
                        script_p["real_text"] = str(chunk["idx"])+"."
                        script_p["end"] = chunk["ascript"][i+1]["end"]
                        script_p["duration"] += chunk["ascript"][i+1]["duration"]
                        skip_next = True
                    else:
                        script_p["real_text"] = str(chunk["idx"])+"."
                script_p["start"] += chunk["start"]
                script_p["end"] += chunk["start"]
                full_transcript.append(script_p)
            
            # num_img = create_caption_images_reddit_com(cid, chunk["idx"], int(tw * 0.9))
            # num_img_clip = (
            #     ImageClip(
            #         num_img,
            #         duration=chunk["ascript"][1]["start"]
            #         - chunk["ascript"][0]["start"],
            #     )
            #     .with_position("center", "center")
            #     .with_layer_index(4)
            #     .with_effects([Resize(width=tw)])
            #     .with_effects([Resize(0.90)])
            #     .with_start(chunk["start"])
            # )
            # clips_list.append(num_img_clip)
            # paths.append(num_img)
            # if not chunk["img"]:
            #     LOGGER.error("No image found for chunk %s", chunk.keys())
            #     raise Exception(f"No image found for chunk {cid}")
            # paths.extend(chunk["img"])
            # # CHANGE THIS TO WORK WITH THE LIST OF img:
            # for i, script_p in enumerate(chunk["ascript"]):
            #     if i > len(chunk["img"]) - 1:
            #         break
            #     if i == len(chunk["ascript"])-1:
            #         duration = chunk["audio_length"] + RED_COM_DELAY
            #     else:
            #         duration = chunk["ascript"][i+1]["start"] - script_p["start"]
            #     clips_list.append(
            #         ImageClip(
            #             chunk["img"][i],
            #             duration=duration#((chunk["audio_length"] + RED_COM_DELAY)
            #             #- chunk["ascript"][1]["start"]
            #             #- chunk["ascript"][0]["start"]) + script_p["start"],
            #         )
            #         .with_position("center", "center")
            #         .with_layer_index(4)
            #         .with_effects([Resize(width=tw)])
            #         .with_effects([Resize(0.90)])
            #         .with_start(
            #             (
            #                 chunk["start"]
            #                 + (
            #                     chunk["ascript"][1]["start"] 
            #                     - chunk["ascript"][0]["start"]
            #                     )
            #                 )
            #                 + script_p["start"]
            #         )
            #     )
        else:
            if not chunk["img"]:
                LOGGER.error("No image found for chunk %s", chunk.keys())
                raise Exception(f"No image found for chunk {cid}")
            clips_list.append(
                ImageClip(chunk["img"], duration=chunk["audio_length"] + RED_COM_DELAY)
                .with_position("center", "center")
                .with_layer_index(4)
                .with_effects([Resize(width=tw)])
                .with_effects([Resize(0.90)])
                .with_start(chunk["start"])
            )
            paths.append(chunk["img"])
        start += chunk["audio_length"] + RED_COM_DELAY
        LOGGER.debug("reddit img SIZE: %s", clips_list[-1].size)
    
    
    return clips_list, paths, full_transcript, title_img_stop


def load_audio_clips(chunks):
    audio_clip_list = []
    paths = []
    for _cid, chunk in chunks.items():
        audio_clip = AudioFileClip(chunk["auFile"]).with_start(chunk["start"])
        audio_clip_list.append(audio_clip)
        paths.append(chunk["auFile"])
    return audio_clip_list, paths


def create_reddit_video_com(
    video_path, output_path, start_time, end_time, pid, th, tw, chunks=None, lang:str="en"
):
    if chunks is None:
        chunks = {}
    use_hi = False
    while True:
        LOGGER.info("chunks: %s", len(chunks.keys()))
        rezivid = Resize(height=th) if use_hi else Resize(width=tw)

        try:
            clip_pt_imgs, paths_to_remove, transcript, end_image_time = create_postimg_clip_com(chunks, tw, th)
            
            _, cap_clips, more_paths, ending_caps = create_captions(
                    f"{pid}_{lang}_",
                    paragraph="paragraph",
                    transcript=transcript,
                    target_size=(tw, th),
                    end_image_time=end_image_time,
                )
            audio_clip_list, paths_to_remove_au = load_audio_clips(chunks)
            paths_to_remove.extend(more_paths)
            temp_audio = CompositeAudioClip(
                [AudioFileClip(REDDIT_TEMPLATE_MUS).subclipped(0, end_time - start_time).with_start(0), *audio_clip_list]
            )

            temp_audio.write_audiofile(f"tmp/audios/{pid}_aud.mp3", codec="libmp3lame")
            video = (
                VideoFileClip(video_path)
                .subclipped(start_time, end_time)
                .with_audio(AudioFileClip(f"tmp/audios/{pid}_aud.mp3").with_start(0))
                .with_effects([rezivid])
            )
            LOGGER.info("Pvideo: %s", video.size)

            LOGGER.info("Pvideo: %s", video.size)
            final_clip = CompositeVideoClip([video, *clip_pt_imgs, *cap_clips])
            if ending_caps < video.duration:
                final_clip = final_clip.subclipped(0, ending_caps)
            LOGGER.info("Pfinal_clip: %s", final_clip.size)
            final_clip.write_videofile(
                output_path,
                pixel_format="yuv420p",
                codec="libx264",
                audio_codec="libmp3lame",
                ffmpeg_params=[
                    #"-crf",
                    #"23",
                    "-vf",
                    "format=yuv420p",  # Force video format conversion
                    "-profile:v",
                    "baseline",  # Set the H.264 profile to baseline
                    "-loglevel", 
                    "quiet"
                ],
            )
            time.sleep(1)
            
            try:
                
                for path in paths_to_remove:
                    os.remove(path)
                for path in paths_to_remove_au:
                    os.remove(path)
                os.remove(f"tmp/audios/{pid}_aud.mp3")
            except:
                pass
        except Exception as e:
            if "divisible by 2" in str(e):
                LOGGER.error("Error: %s", e)
                use_hi = not use_hi
                continue
            else:
                LOGGER.error("Error: %s", traceback.format_exc())
                break

        break


def create_captions(
    prefix: str,
    paragraph: str,
    transcript: list[dict],
    target_size: tuple[int, int],
    output_dir: str = "./tmp/caps_img",
    part=0,
    end_image_time=0,
    parts_offset=0,
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
    file_to_check = f"word{len(transcript)-5}-{part}.png"
    LOGGER.info("file_to_check and pre: %s %s", file_to_check, prefix)
    not_found = True
    for file in os.listdir(output_dir):
        if file_to_check in file and prefix in file:
            not_found = False
            break
    if not_found:
        create_caption_images_reddit(
            prefix, transcript, int(target_size[0] * 0.9), output_dir, part
        )

    clip_list = []
    files_to_remove = []
    ending = 0
    for i, section in enumerate(transcript):
        file_name = ""
        for file in os.listdir(output_dir):
            if f"word{i}-{part}.png" in file and prefix in file:
                file_name = file
                files_to_remove.append(file)
                break
        if file_name == "":
            LOGGER.error("file_name not found: %s", f"word{i}-{part}.png")
            continue
        if i + 1 >= len(transcript):
            duration = section["duration"] + 0.5
        else:
            duration = transcript[i + 1]["start"] - section["start"]
            if duration > 3:
                duration = 3
        pos_y = target_size[1] * 2 / 6
        file_path = os.path.join(output_dir, file_name)
        try:
            fix_img_size(file_path, target_size[0], target_size[1])
        except Exception as e:
            LOGGER.error("Error fixing image size: %s", e)
        # LOGGER.info("file_path: %s", file_path)
        caption_clip = ImageClip(file_path, duration=duration)
        if section["start"] < end_image_time:
            continue
        caption_clip = (
            caption_clip.with_start(section["start"] - parts_offset)
            .with_position(("center", pos_y))
            .with_layer_index(1)
        )
        if (section["start"] - parts_offset) + duration > ending:
            ending = section["start"] + duration
        if caption_clip.w > target_size[0]:
            widthy = target_size[0] * 0.95
            widthy = int(widthy)
            if widthy % 2 != 0:
                widthy += 1
            caption_clip = caption_clip.with_effects([
                Resize(height=caption_clip.h, width=widthy)
            ])
        if caption_clip.h % 2 != 0:
            caption_clip = caption_clip.with_effects([
                Resize(height=caption_clip.h + 1, width=caption_clip.w)
            ])
        if caption_clip.w % 2 != 0:
            caption_clip = caption_clip.with_effects([
                Resize(height=caption_clip.h, width=caption_clip.w + 1)
            ])
        # Composite the caption image onto the video.
        clip_list.append(caption_clip)

    return output_dir, clip_list, files_to_remove, ending
def create_captions_aiyt(
    prefix: str,
    transcript: list[dict],
    target_size: tuple[int, int],
    output_dir: str = "./tmp/caps_img",
    part=0,
    end_image_time=0,
    adjust=0,
    title_len=0,
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
    file_to_check = f"word{len(transcript)-5}.png"
    # LOGGER.info("file_to_check and pre: %s %s", file_to_check, prefix)
    # not_found = True
    # for file in os.listdir(output_dir):
    #     if file_to_check in file and prefix in file:
    #         not_found = False
    #         break
    # if not_found:
    create_caption_images_aiyt(
        prefix, transcript, int(target_size[0] * 0.9), output_dir, adjust=adjust
    )

    clip_list = []
    files_to_remove = []
    ending = 0
    for i, section in enumerate(transcript):
        file_name = ""
        # skip if during the title part
        if title_len > section["start"] - adjust:
            continue
        for file in os.listdir(output_dir):
            if f"word{i}.png" in file and prefix in file:
                file_name = file
                files_to_remove.append(file)
                break
        if file_name == "":
            LOGGER.error("file_name not found: %s", f"word{i}.png")
            continue
        if i + 1 >= len(transcript):
            duration = section["duration"] + 0.5
        else:
            duration = (transcript[i + 1]["start"]-adjust) - (section["start"]-adjust)
            if duration > 3:
                duration = 3
        pos_y = target_size[1] * 2 / 6
        file_path = os.path.join(output_dir, file_name)
        try:
            fix_img_size(file_path, target_size[0], target_size[1])
        except Exception as e:
            LOGGER.error("Error fixing image size: %s", e)
        # LOGGER.info("file_path: %s", file_path)
        caption_clip = ImageClip(file_path, duration=duration)
        #LOGGER.info("caption_clip duration: %s", duration)
        #if (section["start"]-adjust) < end_image_time:
            #LOGGER.info("Skipping caption clip for section: %s", section)
            #continue
        #LOGGER.info("caption_clip start: %s", section["start"] - adjust)
        caption_clip = (
            caption_clip.with_start(section["start"] - adjust)
            .with_position(("center", pos_y))
            .with_layer_index(1)
        )
        if (section["start"] - adjust) + duration > ending:
            ending = section["start"] + duration
        
        if caption_clip.w > target_size[0]:
            widthy = target_size[0] * 0.95
            widthy = int(widthy)
            if widthy % 2 != 0:
                widthy += 1
            caption_clip = caption_clip.with_effects([
                Resize(height=caption_clip.h, width=widthy)
            ])
        if caption_clip.h % 2 != 0:
            caption_clip = caption_clip.with_effects([
                Resize(height=caption_clip.h + 1, width=caption_clip.w)
            ])
        if caption_clip.w % 2 != 0:
            caption_clip = caption_clip.with_effects([
                Resize(height=caption_clip.h, width=caption_clip.w + 1)
            ])
        # Composite the caption image onto the video.
        clip_list.append(caption_clip)

    return output_dir, clip_list, files_to_remove, ending


def fix_img_size(image_path, width, height):
    with Image.open(image_path) as img:
        if img.size[0] >= width:
            LOGGER.info("fix_img_size: %s", img.size)
            ration = width / img.size[0]
            height = int(img.size[1] * ration)
            img = img.resize((int(width * 0.95), int(height * 0.95)), resample=1)
            img.save(image_path)


def check_meta(video_path):
    """
    Checks if a video uses 4:2:0 chroma subsampling.

    Args:
        video_path (str): The path to the video file.

    Returns:
        bool: True if the video uses 4:2:0, False if it uses 4:4:4 or another format, or None if an error occurs.
    """
    try:
        return

    except Exception as e:
        LOGGER.info(f"Error checking chroma subsampling: {e}")
        return None


if __name__ == "__main__":
    video_path = (  # Replace with your video file path
        "D:/tmp/clips/reddites_1j4xwhl.mp4"
    )
    duration = check_meta(video_path)
    print(f"Video duration: {duration} seconds")
