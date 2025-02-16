import json
import os
from clip_creator.db.db import create_database, add_video_entry
from clip_creator.utils.path_setup import check_and_create_dirs
from clip_creator.video_edit import edit_video
from clip_creator.conf import SECTIONS_TYPES, LOGGER
from clip_creator.youtube import search_videos, get_transcript, join_transcript, Download, is_trending, get_comments, get_top_comment, get_video_info, get_subscriptions_videos
from clip_creator.social.reddit import check_top_comment, search_reddit
from clip_creator.ai import find_sections, ask_if_comment_in_transcript
from clip_creator.utils.text_to_video import find_text_sec
from clip_creator.utils.video_tools import convert_webm_to_mp4
from clip_creator.utils.scan_text import most_common_ngrams, find_timestamps, convert_timestamp_to_seconds, find_timestamp_clips
import argparse


def main():
    '''This is a full service to collect information from youtube, find good videos, and then find sections in the videos to edit.
        It then finds the sections in the original transcript and returns the timestamps for the sections.
        After that it edits the video and returns the edited video.
    '''
    parser = argparse.ArgumentParser(description="AI Clip Creator")
    parser.add_argument("--noretrieve", action="store_true", help="Retrieve new videos from YouTube if not set")
    parser.add_argument("--numvid", type=int, help="Path to the input video")
    parser.add_argument("--noai", action="store_true", help="Retrieve new videos from YouTube if set")
    parser.add_argument("--inputvideoid", type=str, help="Path to the input video")
    args = parser.parse_args()
    LOGGER.info("Arguments: %s", args)
    #####################################
    # Set up paths
    #####################################
    check_and_create_dirs()
    #####################################
    # Create database
    #####################################
    create_database()
    #####################################
    # Get videos and transcripts
    #####################################
    videos = []
    if not args.noretrieve:
        # get hot videos
        #videos.extend(search_videos("gaming", time_range=1))
        videos.extend(get_subscriptions_videos())
        LOGGER.info("Videos: %s", videos)
        if args.numvid:
            videos = videos[:args.numvid]
        # filter out non trending videos
        #videos = [video for video in videos if is_trending(video['id']['videoId'])]
        raw_transcripts = {}
        formated_transcripts = {}
        for video in videos:
            LOGGER.info("getting transcript for video id: %s", video['id']['videoId'])
            raw_transcripts[video['id']['videoId']] = get_transcript(video['id']['videoId']) # {'text': 'out our other man outs right over here', 'start': 1060.84, 'duration': 3.52}
            formated_transcripts[video['id']['videoId']] = join_transcript(raw_transcripts[video['id']['videoId']])
            LOGGER.info("Transcript: %s", raw_transcripts[video['id']['videoId']])
    else:
        formated_transcripts = {}
        raw_transcripts = {}
        with open('test_files/yt_script_t7crKS9DWaI.txt', 'r') as file:
            formated_transcripts["t7crKS9DWaI"] = file.read()
        with open('test_files/yt_script_t7crKS9DWaI.json', 'r') as file:
            raw_transcripts["t7crKS9DWaI"] = json.load(file)
    
    ######################################
    # Get video info
    ######################################
    
    video_info = {}
    LOGGER.info(formated_transcripts)
    for id, script in formated_transcripts.items():
        video_info[id] = get_video_info(id)
        LOGGER.info("Video Info: %s", video_info[id])
    
    ######################################
    # Reddit Comments
    ######################################
    top_reddit_comment = {}
    posts_url = {}
    reddit_comments = {}
    for id, script in formated_transcripts.items():
        top_posts = search_reddit(videoid=id)
        top_reddit_comment[id], reddit_comments[id], posts_url[id] = check_top_comment(top_posts, 10)
        LOGGER.info("Top Reddit Comment: %s", top_reddit_comment[id])
    ######################################
    # Youtube Comments
    ######################################
    yt_comments = {}
    top_yt_comment = {}
    for id, script in formated_transcripts.items():
        yt_comments[id] = get_comments(id)
        top_yt_comment[id] =  get_top_comment(yt_comments[id], 10, video_info[id]["creator"])
        LOGGER.info("Top YT Comment: %s", top_yt_comment[id])
    #########################################
    # Compile comments into words and counts
    #########################################
    most_common_videos = {}
    for id, script in formated_transcripts.items():
        running_words = ""
        for comment in reddit_comments[id]:
            running_words += comment['text']
            running_words += " "
        for comment in yt_comments[id]:
            running_words += comment['text']
            running_words += " "
            
        all_ngrams = {"1-gram": {}, "2-gram": {}, "3-gram": {}}
        all_ngrams["1-gram"]['word'], all_ngrams["1-gram"]['count'] = most_common_ngrams(running_words, 1)
        all_ngrams["2-gram"]['word'], all_ngrams["2-gram"]['count'] = most_common_ngrams(running_words, 2)
        all_ngrams["3-gram"]['word'], all_ngrams["3-gram"]['count'] = most_common_ngrams(running_words, 3)
        most_common_videos[id]:dict = all_ngrams
    ######################################
    # Add to DB
    ######################################
    for id, script in raw_transcripts.items():
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
            "video_creator": video_info[id]["creator"]
        }
        add_video_entry(data_entry)
        #LOGGER.info("Added data %s", data_entry)
    
    ######################################
    # Find Timestamps #1 Reason to CLIP
    ######################################
    timestamps = {}
    for id, script in formated_transcripts.items():
        timestamps[id] = find_timestamps(top_yt_comment[id])
        if timestamps[id]:
            timestamps[id] = convert_timestamp_to_seconds(timestamps[id])
            LOGGER.info("Timestamp in sec: %s", timestamps[id])
        
    ######################################
    # Get length of timestamps
    ######################################
    clips = {}
    for id, script in raw_transcripts.items():
        if timestamps[id]:
            clips[id] = find_timestamp_clips(script, timestamps[id])
        else:
            clips[id] = None
        LOGGER.info("Clips: %s", clips[id])
    ######################################
    # Find comment section in video #2 Reason to CLIP
    ######################################
    comment_in_transcript = {}
    if not args.noai:
        
        for id, script in formated_transcripts.items():
            comment_in_transcript[id] = ask_if_comment_in_transcript(script, top_yt_comment[id])
            LOGGER.info("Comment in transcript: %s", comment_in_transcript[id])
            
    ######################################
    # Find Videos based on conditions
    ######################################
    
    ######################################
    # Use AI to find sections #Last Reason to CLIP
    ######################################
    if not args.noai:
        found_sections = {}
        starting_timestamps = {}
        for id, script in formated_transcripts.items():
            for type_phases in SECTIONS_TYPES:
                found_sections[id] = find_sections(script, type_phases)
                starting_timestamps[id] = find_text_sec(raw_transcripts[id], found_sections[id])
    ######################################
    # Download videos
    ######################################
    
        
    if not args.inputvideoid:
        for id, script in formated_transcripts.items():
            if clips[id]:
                if not os.path.exists(f"tmp/raw/{id}.mp4"):
                    Download(id, path='tmp/raw', filename=id)
                    # Convert webm to mp4
                    convert_webm_to_mp4(f"tmp/raw/{id}.webm", f"tmp/raw/{id}.mp4")
                    os.remove(f"tmp/raw/{id}.webm")
    else:
        if not os.path.exists(f"tmp/raw/{args.inputvideoid}.mp4"):
            Download(args.inputvideoid, path='tmp/raw', filename=args.inputvideoid)
            # Convert webm to mp4
            convert_webm_to_mp4(f"tmp/raw/{args.inputvideoid}.webm", f"tmp/raw/{args.inputvideoid}.mp4")
    
    ######################################
    # Format Clips into chunks
    ######################################
    clips_chunks = {}
    for id, clip in clips.items():
        if clip:
            clips_chunks[id] = {"start":float(clip[0]['start']), "end":float(clip[-1]['start'])+float(clip[0]['duration'])}
        else:
            clips_chunks[id] = None
    ######################################
    # Edit Videos
    ######################################
    for id, clip in clips.items():
        if clip:
            edit_video(f"tmp/raw/{id}.mp4", f"tmp/clips/{id}.mp4", target_size=(1080, 1920), start_time=clips_chunks[id]['start'], end_time=clips_chunks[id]['end'], text=top_yt_comment[id])
    
if __name__ == '__main__':
    main()