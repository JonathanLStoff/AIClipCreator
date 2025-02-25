import argparse
import json
import os

from datetime import datetime

from clip_creator.conf import (
    CLIPS_FOLDER,
    DOWNLOAD_FOLDER,
    LOGGER,

)
from clip_creator.db.db import (

    create_or_update_clip,
    update_post_status,
    add_clip_info,
    get_all_video_ids,

    get_all_clips_df
)
from clip_creator.social.custom_tiktok import upload_video_tt
from clip_creator.social.insta import InstaGramUp
from clip_creator.utils.path_setup import check_and_create_dirs, get_unused_videos
from clip_creator.utils.schedules import get_timestamps



def main():
    """This is a full service to collect information from youtube, find good videos, and then find sections in the videos to edit.
    It then finds the sections in the original transcript and returns the timestamps for the sections.
    After that it edits the video and returns the edited video.
    """
    used_videos = get_all_video_ids()
    un_used_videos, un_used_videos_li = get_unused_videos(used_videos, raw_dir=DOWNLOAD_FOLDER)
    #####################################
    # Get videos and transcripts
    #####################################
    videos = []
    LOGGER.info("Used Videos: %s", un_used_videos)
    videos.extend(un_used_videos)
    

    #####################################
    # Check for unused clips
    #####################################
    clip_paths = {}
    descriptions = {}
    clips = {}
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
        if clipy:
            upload_video_tt(clip_paths[id], schedules[id], descriptions[id], submit=True)
            update_post_status(id, "tiktok", schedules[id].strftime("%Y-%m-%d %H:%M:%S"))

            #insta.upload_to_insta(clip_paths[id], descriptions[id])
            #update_post_status(id, "instagram", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            
    

if __name__ == "__main__":
    main()
