import argparse
import json
import os
import time
import traceback

from datetime import datetime

from clip_creator.ai import ask_if_comment_in_transcript, find_sections, create_clip_description
from clip_creator.conf import (
    CLIPS_FOLDER,
    DOWNLOAD_FOLDER,
    LOGGER,
    SECTIONS_TYPES,
    TMP_CLIPS_FOLDER,
    TMP_DOWNLOAD_FOLDER,
    ERRORS_TYPES
)
from clip_creator.db.db import (
    add_video_entry,
    create_database,
    create_or_update_clip,
    find_clip,
    add_clip_info,
    get_all_video_ids,
    get_all_videos_df,
    get_all_clips_df,
    update_post_status,
    add_error_log
)
from clip_creator.social.reddit import check_top_comment, search_reddit
from clip_creator.social.custom_tiktok import upload_video_tt
from clip_creator.social.insta import InstaGramUp
from clip_creator.utils.files import copy_to_tmp, save_space
from clip_creator.utils.path_setup import check_and_create_dirs, get_unused_videos
from clip_creator.utils.schedules import get_timestamps
from clip_creator.utils.scan_text import (
    clean_text,
    convert_timestamp_to_seconds,
    find_timestamp_clips,
    find_timestamps,
    most_common_ngrams,
    sanitize_filename,
)
from clip_creator.utils.text_to_video import find_text_sec
from clip_creator.utils.video_tools import convert_webm_to_mp4
from clip_creator.video_edit import edit_video
from clip_creator.youtube import (
    Download,
    get_comments,
    get_subscriptions_videos,
    get_top_comment,
    get_transcript,
    get_video_info,
    join_transcript,
)


def main():
    """This is a full service to collect information from youtube, find good videos, and then find sections in the videos to edit.
    It then finds the sections in the original transcript and returns the timestamps for the sections.
    After that it edits the video and returns the edited video.
    """
    parser = argparse.ArgumentParser(description="AI Clip Creator")
    parser.add_argument(
        "--noretrieve",
        action="store_true",
        help="Retrieve new videos from YouTube if not set",
    )
    parser.add_argument("--numvid", type=int, help="Path to the input video")
    parser.add_argument(
        "--noai", action="store_true", help="Retrieve new videos from YouTube if set"
    )
    parser.add_argument("--inputvideoid", type=str, help="Path to the input video")
    parser.add_argument(
        "--skiptimecheck", action="store_true", help="Retrieve new videos from YouTube if set"
    )
    args = parser.parse_args()
    LOGGER.info("Arguments: %s", args)
    #####################################
    # Set up paths
    #####################################
    errors_lot:dict[str,dict[str,str]] = {}
    check_and_create_dirs()
    #####################################
    # Create database
    #####################################
    create_database()
    used_videos = get_all_video_ids()
    video_df_info = get_all_videos_df()
    un_used_videos, un_used_videos_li = get_unused_videos(used_videos, raw_dir=DOWNLOAD_FOLDER)
    #####################################
    # Get videos and transcripts
    #####################################
    videos = []
    LOGGER.info("Used Videos: %s", used_videos)
    if not args.noretrieve:
        # get hot videos
        print("Retrieving videos")
        if args.inputvideoid != "" and args.inputvideoid is not None:
            print("Input video id: %s", args.inputvideoid)
            videos.append({"id": {"videoId": args.inputvideoid}})
        else:
            # videos.extend(search_videos("gaming", time_range=1))
            videos.extend(un_used_videos)
            videos.extend(get_subscriptions_videos(used_ids=used_videos+un_used_videos_li, skip_time_check=args.skiptimecheck, video_df_info=video_df_info))
            LOGGER.info("Videos: %s", videos)
            if args.numvid:
                videos = videos[: args.numvid]
        # filter out non trending videos
        # videos = [video for video in videos if is_trending(video['id']['videoId'])]
    else:
        videos.extend(un_used_videos)
    with open("running_videos.json", "w") as f:
        tmp_vid_list = [vid['id']['videoId'] for vid in videos]
        json.dump(tmp_vid_list, f)
    ################################
    # Get Transcripts
    ################################    
    raw_transcripts = {}
    formated_transcripts = {}
    for video in videos:
        errors_lot[video["id"]["videoId"]] = {}
        try:
            LOGGER.info("getting transcript for video id: %s", video["id"]["videoId"])
            raw_transcripts[video["id"]["videoId"]] = get_transcript(
                video["id"]["videoId"]
            )  # {'text': 'out our other man outs right over here', 'start': 1060.84, 'duration': 3.52}
            formated_transcripts[video["id"]["videoId"]] = "disabled" if "disabled" == raw_transcripts[video["id"]["videoId"]] else join_transcript(
                raw_transcripts[video["id"]["videoId"]]
            )
        except Exception as e:
            LOGGER.error("Error getting transcript: %s, for %s", traceback.format_exc(), video["id"]["videoId"])
            errors_lot[video["id"]["videoId"]][ERRORS_TYPES[2]] = f"Error getting transcript {traceback.format_exc()}"
    

    ######################################
    # Get video info
    ######################################

    video_info = {}
    LOGGER.info(formated_transcripts)
    for id, script in formated_transcripts.items():
        try:
            if id in video_df_info.index:
                
                video_info[id] = {
                "creator": video_df_info.loc[id]['video_creator'],
                "views": video_df_info.loc[id]['views'],
                "likes": video_df_info.loc[id]['likes'],
                "video_name": video_df_info.loc[id]['name'],
            }
            else:
                video_info[id] = get_video_info(id)
            LOGGER.info("Video Info: %s", video_info[id])
        except Exception as e:
            LOGGER.error("Error getting video info: %s, for %s", traceback.format_exc(), id)
            errors_lot[id][ERRORS_TYPES[1]] = f"Error getting video info {traceback.format_exc()}"

    ######################################
    # Reddit Comments
    ######################################
    top_reddit_comment = {}
    posts_url = {}
    reddit_comments = {}
    for id, script in formated_transcripts.items():
        try:
            top_posts = search_reddit(videoid=id)
            top_reddit_comment[id], reddit_comments[id], posts_url[id] = check_top_comment(
                top_posts, 10
            )
            LOGGER.info("Top Reddit Comment: %s", top_reddit_comment[id])
        except Exception as e:
            LOGGER.error("Error getting reddit comments: %s, for %s", traceback.format_exc(), id)
            errors_lot[id][ERRORS_TYPES[0]] = f"Error getting reddit comments {traceback.format_exc()}"
    ######################################
    # Youtube Comments
    ######################################
    yt_comments = {}
    top_yt_comment = {}
    for id, script in formated_transcripts.items():
        try:
            yt_comments[id] = get_comments(id)
            top_yt_comment[id] = get_top_comment(
                yt_comments[id], 10, video_info[id]["creator"]
            )
            LOGGER.info("Top YT Comment: %s", top_yt_comment[id])
        except Exception as e:
            LOGGER.error("Error getting youtube comments: %s, for %s", traceback.format_exc(), id)
            errors_lot[id][ERRORS_TYPES[1]] = f"Error getting youtube comments {traceback.format_exc()}"
    #########################################
    # Compile comments into words and counts
    #########################################
    most_common_videos = {}
    for id, script in formated_transcripts.items():
        try:
            running_words = ""
            for comment in reddit_comments[id]:
                running_words += comment["text"]
                running_words += " "
            for comment in yt_comments[id]:
                running_words += comment["text"]
                running_words += " "

            all_ngrams = {"1-gram": {}, "2-gram": {}, "3-gram": {}}
            (
                all_ngrams["1-gram"]["word"],
                all_ngrams["1-gram"]["count"],
            ) = most_common_ngrams(running_words, 1)
            (
                all_ngrams["2-gram"]["word"],
                all_ngrams["2-gram"]["count"],
            ) = most_common_ngrams(running_words, 2)
            (
                all_ngrams["3-gram"]["word"],
                all_ngrams["3-gram"]["count"],
            ) = most_common_ngrams(running_words, 3)
            most_common_videos[id]: dict = all_ngrams
        except Exception as e:
            LOGGER.error("Error getting common words: %s, for %s", traceback.format_exc(), id)
            errors_lot[id][ERRORS_TYPES[0]] = f"Error getting common words {traceback.format_exc()}"
    ######################################
    # Add to DB
    ######################################
    for id, script in raw_transcripts.items():
        try:
            data_entry = {
                "id": id,
                "name": video_info[id]["video_name"],
                "transcript": json.dumps(script),
                "one_word_most_used": most_common_videos[id]["1-gram"]["word"],
                "one_word_count": most_common_videos[id]["1-gram"]["count"],
                "two_word_most_used": most_common_videos[id]["2-gram"]["word"],
                "two_word_count": most_common_videos[id]["2-gram"]["count"],
                "three_word_most_used": most_common_videos[id]["3-gram"]["word"],
                "three_word_count": most_common_videos[id]["3-gram"]["count"],
                "views": video_info[id]["views"],
                "likes": video_info[id]["likes"],
                "top_yt_comment": top_yt_comment[id],
                "top_reddit_comment": top_reddit_comment[id],
                "reddit_url": posts_url[id],
                "video_creator": video_info[id]["creator"],
            }
            add_video_entry(data_entry)
        except Exception as e:
            LOGGER.error("Error adding data: %s, for %s", traceback.format_exc(), id)
            errors_lot[id][ERRORS_TYPES[1]] = f"Error add_video_entry data {traceback.format_exc()}"
        # LOGGER.info("Added data %s", data_entry)

    ######################################
    # Find Timestamps #1 Reason to CLIP
    ######################################
    timestamps = {}
    for id, script in formated_transcripts.items():
        try:
            timestamps[id] = find_timestamps(top_yt_comment[id])
            if timestamps[id]:
                top_yt_comment[id] = clean_text(top_yt_comment[id])
                timestamps[id] = convert_timestamp_to_seconds(timestamps[id])
                LOGGER.info("Timestamp in sec: %s", timestamps[id])
        except Exception as e:
            LOGGER.error("Error finding timestamps: %s, for %s", traceback.format_exc(), id)
            errors_lot[id][ERRORS_TYPES[1]] = f"Error finding timestamps {traceback.format_exc()}"
            timestamps[id] = None

    ######################################
    # Get length of timestamps
    ######################################
    clips = {}
    for id, script in raw_transcripts.items():
        try:
            if timestamps[id]: # Add more checks
                if "disabled" != script:
                    clips[id] = find_timestamp_clips(script, timestamps[id])
                else:
                    LOGGER.info("Transcript is disabled, add download and transcribe function here")
                    clips[id] = None
            else:
                clips[id] = None
            LOGGER.info("Clips: %s", clips[id])
        except Exception as e:
            LOGGER.error("Error finding clips: %s, for %s", traceback.format_exc(), id)
            errors_lot[id][ERRORS_TYPES[1]] = f"Error finding clips {traceback.format_exc()}"
            clips[id] = None
        
    #######################################
    # Use ai to describe the video
    #######################################  
    video_descriptions = {}
    if not args.noai:
        for id, script in raw_transcripts.items():
            video_descriptions[id] = create_clip_description(f"{DOWNLOAD_FOLDER}/{id}.mp4", script)
            
    
    ######################################
    # Find comment section in video #2 Reason to CLIP
    ######################################
    comment_in_transcript = {}
    if not args.noai:
        for id, script in formated_transcripts.items():
            comment_in_transcript[id] = ask_if_comment_in_transcript(
                script, top_yt_comment[id]
            )
            LOGGER.info("Comment in transcript: %s", comment_in_transcript[id])

    ######################################
    # Find Videos based on conditions
    # 1. Comment in transcript
    # 2. Timestamp
    # 3. AI
    ######################################

    ######################################
    # Use AI to find sections #Last Reason to CLIP
    ######################################
    if not args.noai:
        found_sections = {}
        starting_timestamps = {}
        for id, script in video_descriptions.items():
            for type_phases in SECTIONS_TYPES:
                found_sections[id] = find_sections(script, type_phases)
                starting_timestamps[id] = find_text_sec(
                    raw_transcripts[id], found_sections[id]
                )
    ######################################
    # Download videos
    ######################################

    for id, script in formated_transcripts.items():
        try:
            if clips[id]:
                if not os.path.exists(f"{DOWNLOAD_FOLDER}/{id}.mp4"):
                    LOGGER.info("not found: %s, downloading", f"{DOWNLOAD_FOLDER}/{id}.mp4")
                    Download(id, path=TMP_DOWNLOAD_FOLDER, filename=id)
                    # Convert webm to mp4
                    convert_webm_to_mp4(
                        f"{TMP_DOWNLOAD_FOLDER}/{id}.webm",
                        f"{DOWNLOAD_FOLDER}/{id}.mp4",
                    )
                    os.remove(f"{TMP_DOWNLOAD_FOLDER}/{id}.webm")
                time.sleep(5)
        except Exception as e:
            LOGGER.error("Error downloading video: %s, for %s", traceback.format_exc(), id)
            errors_lot[id][ERRORS_TYPES[2]] = f"Error downloading video {traceback.format_exc()}"


    ######################################
    # Format Clips into chunks
    ######################################
    clips_chunks = {}
    for id, clip in clips.items():
        if clip:
            if (not find_clip(id, int(float(clip[0]["start"])))) or args.inputvideoid:
                clips_chunks[id] = {
                    "start": float(clip[0]["start"]),
                    "end": float(clip[-1]["start"]) + float(clip[0]["duration"]),
                }
            else:
                clips_chunks[id] = None
        else:
            clips_chunks[id] = None
            
    ######################################
    # Best overall comment
    ######################################
    best_comment = {}
    for id, script in formated_transcripts.items():
        best_comment[id] = str(top_yt_comment[id])
        if reddit_comments[id]:
            best_comment[id] = str(top_reddit_comment[id])
    ######################################
    # Compile Description
    ######################################
    descriptions = {}
    for id, script in formated_transcripts.items():
        
        descriptions[id] = (
            "#fyp #gaming #clip #fyppppppppppppp\ncredit"
            f" {video_info[id]['creator']}'s {video_info[id]['video_name']}"
        )
    
    ######################################
    # Edit Videos
    ######################################
    clip_paths = {}
    true_transcripts = {}
    
    for id, clip in clips.items():
        if clip and clips_chunks[id]:
            if ERRORS_TYPES[2] in errors_lot[id].keys():
                continue
            try:
                LOGGER.info(
                    "FOLDERS: %s %s",
                    f"{DOWNLOAD_FOLDER}/{id}.mp4",
                    f"{CLIPS_FOLDER}/{id}.mp4",
                )
                copy_to_tmp(
                    f"{DOWNLOAD_FOLDER}/{id}.mp4", f"{TMP_DOWNLOAD_FOLDER}/{id}.mp4"
                )
                clip_paths[id],true_transcripts[id] = edit_video(
                    sanitize_filename(id),
                    f"{TMP_DOWNLOAD_FOLDER}/{id}.mp4",
                    f"{TMP_CLIPS_FOLDER}/{id}.mp4",
                    target_size=(1080, 1920),
                    start_time=clips_chunks[id]["start"],
                    end_time=clips_chunks[id]["end"],
                    text=best_comment[id],
                    transcript=clips[id],
                )
                save_space(
                    f"{DOWNLOAD_FOLDER}/{id}.mp4",
                    f"{TMP_DOWNLOAD_FOLDER}/{id}.mp4",
                    f"{CLIPS_FOLDER}/{id}.mp4",
                    f"{TMP_CLIPS_FOLDER}/{id}.mp4",
                )
                clip_paths[id] = f"{CLIPS_FOLDER}/{id}.mp4"
                clip_dict = {
                    "video_id": id,
                    "start_time": int(clips_chunks[id]["start"]),
                    "end_time": int(clips_chunks[id]["end"]),
                    "clip_transcript": json.dumps(clip),
                }
                create_or_update_clip(clip_dict)
                with open(clip_paths[id].replace("mp4", "txt"), "w") as f:
                    f.write(descriptions[id])
            except Exception as e:
                LOGGER.error("Error editing video: %s, for %s", traceback.format_exc(), id)
                errors_lot[id][ERRORS_TYPES[2]] = f"Error editing video {traceback.format_exc()}"
                clip_paths[id] = None
    for id, clipy in clips.items():
        if clipy:
            if ERRORS_TYPES[2] in errors_lot[id].keys():
                continue
            clip_info = {
                "video_id": id,
                "clip_path": clip_paths[id],
                "description": descriptions[id],
                "true_transcript": json.dumps(true_transcripts[id]),
                "title": best_comment[id],
            }
            add_clip_info(clip_info)
    LOGGER.info("Descriptions: %s", descriptions)
    ########################################
    # Check for unused clips
    ########################################
    clips_df = get_all_clips_df()
    for clip in clips_df.to_dict(orient="records"):
        if not clip["post_tiktok"] and os.path.exists(f"{CLIPS_FOLDER}/{clip['video_id']}.mp4"):
            clip_paths[clip["video_id"]] = f"{CLIPS_FOLDER}/{clip['video_id']}.mp4"
            descriptions[clip["video_id"]] = open(f"{CLIPS_FOLDER}/{clip['video_id']}.txt", "r").read()
            clips[clip["video_id"]] = json.loads(clip["clip_transcript"])
            clip_info = {
                "video_id": clip["video_id"],
                "clip_path": clip_paths[clip["video_id"]],
                "description": descriptions[clip["video_id"]],
                #"true_transcript": json.dumps(true_transcripts[id]),
                #"title": best_comment[id],
            }
            add_clip_info(clip_info)
    ########################################
    # Calc time to post
    ########################################
    schedules = {}
    number_clips = 0
    for id, clip in clips.items():
        if clip:
            number_clips += 1
    allsched = get_timestamps(number_clips-1)
    allsched_idx = 0
    for id, clip in clips.items():
        if ERRORS_TYPES[2] in errors_lot[id].keys():
            continue
        if clip:
            if allsched_idx < len(allsched):

                schedules[id] = allsched[allsched_idx]
                allsched_idx += 1
            else:
                LOGGER.error("Not enough timestamps for %s", id)
                schedules[id] = None
        else:
            schedules[id] = None
    
        
    ########################################
    # Post to TikTok & Instagram
    ########################################
    insta = InstaGramUp()
    for id, clipy in clips.items():
        try:
            if ERRORS_TYPES[2] in errors_lot[id].keys():
                    continue
            if clipy:
                upload_video_tt(clip_paths[id], schedules[id], descriptions[id], submit=True)
                update_post_status(id, "tiktok", schedules[id].strftime("%Y-%m-%d %H:%M:%S"))
                #insta.upload_to_insta(clip_paths[id], descriptions[id])
                #update_post_status(id, "instagram", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        except Exception as e:
            LOGGER.error("Error posting to social media: %s, for %s", traceback.format_exc(), id)
            errors_lot[id][ERRORS_TYPES[2]] = f"Error posting to social media {traceback.format_exc()}"
    
    ########################################
    # Log Errors
    ########################################
    for id, errors in errors_lot.items():
        for error_type, error in errors.items():
            add_error_log(id, error_type, error)

if __name__ == "__main__":
    
    main()
