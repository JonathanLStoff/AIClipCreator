import torch
import os
from random import choice, randint
from clip_creator.conf import LOGGER, REDDIT_TEMPLATE_FOLDER
from clip_creator.tts.ai import TTSModel
from clip_creator.utils.forcealign import force_align
from clip_creator.social.reddit import reddit_posts_orch
from clip_creator.utils.path_setup import check_and_create_dirs
from clip_creator.utils.scan_text import reddit_remove_bad_words
from clip_creator.vid_ed.red_vid_edit import get_clip_duration, get_audio_duration, create_reddit_video
from clip_creator.db.db import (
    update_reddit_post_clip,
    create_database,
    add_reddit_post_clip,
    get_rows_where_tiktok_null_or_empty,
    get_all_post_ids_red,
)
def main_reddit_posts_orch():
    #####################################
    # Set up paths
    #####################################
    
    check_and_create_dirs()
    #####################################
    # Create database
    #####################################
    create_database()
    found_posts = get_all_post_ids_red()
    
    # 160 minium words in a post
    netw_redd_posts = reddit_posts_orch(found_posts, min_post=10, max_post=20)
    
    
    #####################################
    # Add posts to database
    #####################################
    for post in netw_redd_posts:
        if "/" in post['url']:
            if post['url'].split("/")[3] in found_posts:
                LOGGER.error(f"ITEM ADDED FROM POSTS IS WRONG: {post['url']}")
            else:
                add_reddit_post_clip(
                    post_id=post['url'].split("/")[3], 
                    title=post['title'], 
                    posted_at=post['posted_at'],
                    content=post['content'], 
                    url=post['url'], 
                    upvotes=post['upvotes'],
                    comments=post['comments'],
                    nsfw=post['nsfw'],
                    )
        else:
            LOGGER.error(f"Invalid URL: {post['url']}")
    #####################################
    # Remove from list if 160 words not met
    #####################################
    unused_posts = get_rows_where_tiktok_null_or_empty()
    posts_to_use = {}
    for post in unused_posts:
        if post.get('content', "").split() > 160:
            posts_to_use[post['post_id']] = (post)
            
    #####################################
    # Censor bad words
    #####################################
    for pid, post in posts_to_use.items():
        # run video creator that combines video with audio with transcript
        posts_to_use[pid]['content'] = reddit_remove_bad_words(post['content'])
    #####################################
    # Create Audio using TTS
    #####################################
    
    tts_model = TTSModel()
    for pid, post in posts_to_use.items():
        posts_to_use[pid]['filename'] = f"tmp/audios/{pid}_tts.wav"
        tts_model.run_it(posts_to_use[pid]['filename'], post['content'])
    #####################################
    # Force align text to audio
    #####################################
    device = "cpu"
    if torch.cuda.is_available():
        device = "cuda:0"
        torch.cuda.empty_cache()
    for pid, post in posts_to_use.items():
        posts_to_use[pid]['aligned_ts'] = force_align(device=device, file=post['filename'], yt_ft_transcript=post['content'])
    #####################################
    # Create video
    #####################################
    mpfours = [file for file in os.listdir(REDDIT_TEMPLATE_FOLDER) if file.endswith(".mp4")]
    for pid, post in posts_to_use.items():
        background = choice(mpfours)
        clip_length = get_clip_duration(background)
        # Grab random part from mc parkor/subway surfers/temple run
        posts_to_use[pid]['audio_length'] = get_audio_duration(post['filename'])
        start = randint(0, int(clip_length - posts_to_use[pid]['audio_length']))
        end = start + posts_to_use[pid]['audio_length']
        # run video creator that combines video with audio with transcript
        create_reddit_video(
            video_path=os.path.join(REDDIT_TEMPLATE_FOLDER, background),
            audio_path=post['filename'],
            output_path=f"tmp/clips/{pid}.mp4",
            start_time=start,
            end_time=end,
            pid=pid,
            transcript=post['aligned_ts'],
            th=1080,
            tw=1920,
        )
    
    
        