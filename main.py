import json
import os
from clip_creator.db.db import create_database
from clip_creator.utils.path_setup import check_and_create_dirs
from clip_creator.video_edit import edit_video
from clip_creator.conf import SECTIONS_TYPES, LOGGER
from clip_creator.youtube import search_videos, get_transcript, join_transcript, Download, is_trending, get_comments
from clip_creator.ai import find_sections
from clip_creator.utils.text_to_video import find_text_sec
from clip_creator.utils.video_tools import convert_webm_to_mp4
import argparse


def main():
    '''This is a full service to collect information from youtube, find good videos, and then find sections in the videos to edit.
        It then finds the sections in the original transcript and returns the timestamps for the sections.
        After that it edits the video and returns the edited video.
    '''
    parser = argparse.ArgumentParser(description="AI Clip Creator")
    parser.add_argument("--noretrieve", action="store_true", help="Retrieve new videos from YouTube if not set")
    parser.add_argument("--noai", action="store_true", help="Retrieve new videos from YouTube if set")
    parser.add_argument("--inputvideoid", type=str, help="Path to the input video")
    args = parser.parse_args()
    
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
        videos.extend(search_videos("gaming", time_range=1))
        # filter out non trending videos
        videos = [video for video in videos if is_trending(video['id']['videoId'])]
        raw_transcripts = {}
        formated_transcripts = {}
        for video in videos:
            LOGGER.info("getting transcript for video id: %s", video['id']['videoId'])
            raw_transcripts[video['id']['videoId']] = get_transcript(video['id']['videoId'])
            formated_transcripts[video['id']['videoId']] = join_transcript(raw_transcripts[video['id']['videoId']])
        get_comments(videos)
    else:
        formated_transcripts = {}
        raw_transcripts = {}
        with open('test_files/yt_script_t7crKS9DWaI.txt', 'r') as file:
            formated_transcripts["t7crKS9DWaI"] = file.read()
        with open('test_files/yt_script_t7crKS9DWaI.json', 'r') as file:
            raw_transcripts["t7crKS9DWaI"] = json.load(file)
    
    ######################################
    # Use AI to find sections
    ######################################
    
    if not args.noai:
        found_sections = {}
        starting_timestamps = {}
        for id, script in formated_transcripts:
            for type_phases in SECTIONS_TYPES:
                found_sections[id] = find_sections(script, type_phases)
                starting_timestamps[id] = find_text_sec(raw_transcripts[id], found_sections[id])
                
    ######################################
    # Find Videos based on conditions
    ######################################
    
    
    ######################################
    # Download videos
    ######################################
    if not args.inputvideoid:
        for id, script in formated_transcripts:
            Download(id, path='tmp/raw', filename=id)
            # Convert webm to mp4
            convert_webm_to_mp4(f"tmp/raw/{id}.webm", f"tmp/raw/{id}.mp4")
    else:
        if not os.path.exists(f"tmp/raw/{args.inputvideoid}.mp4"):
            Download(args.inputvideoid, path='tmp/raw', filename=args.inputvideoid)
            # Convert webm to mp4
            convert_webm_to_mp4(f"tmp/raw/{args.inputvideoid}.webm", f"tmp/raw/{args.inputvideoid}.mp4")
    
    ######################################
    edit_video(input_video_path, output_video_path, zoom=1.2, target_size=(720, 1280))
    
if __name__ == '__main__':
    main()