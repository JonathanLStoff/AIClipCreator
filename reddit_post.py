import torch
import argparse
import uuid
import os
import shutil
import json
from datetime import datetime
from random import choice, randint, sample
from clip_creator.conf import LOGGER, CLIPS_FOLDER, REDDIT_TEMPLATE_BG, WK_SCHED
from clip_creator.tts.ai import TTSModelKokoro
from clip_creator.utils.forcealign import force_align
from clip_creator.social.custom_tiktok import upload_video_tt
from clip_creator.social.reddit import reddit_posts_orch
from clip_creator.utils.path_setup import check_and_create_dirs
from clip_creator.utils.scan_text import reddit_remove_bad_words, reddit_acronym, split_audio
from clip_creator.vid_ed.red_vid_edit import get_clip_duration, get_audio_duration, create_reddit_video
from clip_creator.utils.caption_img import render_html_to_png
from clip_creator.utils.schedules import get_timestamps
from clip_creator.db.db import (
    update_reddit_post_clip,
    create_database,
    add_reddit_post_clip,
    get_rows_where_tiktok_null_or_empty,
    get_all_post_ids_red,
)
from clip_creator.utils.schedules import none_old_timestamps
def main_reddit_posts_orch():
    parser = argparse.ArgumentParser(description="AI Clip Creator")
    parser.add_argument(
        "--noretrieve",
        action="store_true",
        help="Retrieve new videos from YouTube if not set",
    )
    parser.add_argument(
        "--dryrun", action="store_true", help="Does everything but post to TikTok, save db and remove files"
    )
    parser.add_argument(
        "--usevids", action="store_true", help="Use created videos if set"
    )
    parser.add_argument("--inputvideoid", type=str, help="Path to the input video")
    parser.add_argument(
        "--skiptimecheck",
        action="store_true",
        help="Retrieve new videos from YouTube if set",
    )
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
    found_posts = get_all_post_ids_red()
    
    if not args.noretrieve and not args.usevids:
        netw_redd_posts = reddit_posts_orch(found_posts, min_post=10, max_post=20)
    
    
        #####################################
        # Add posts to database
        #####################################
        for post in netw_redd_posts:
            if "/" in post['url']:
                do_it = False
                post_id = str(uuid.uuid4())
                for party in post['url'].split("/"):
                    if "comment" in party.lower():
                        do_it=True
                    elif do_it:
                        post_id = party
                        break
                par_post_id = None
                if post.get('parent_href'):
                    do_it = False
                    
                    for party in post.get('parent_href').split("/"):
                        if "comment" in party.lower():
                            do_it=True
                        elif do_it:
                            par_post_id = party
                            break
                if post_id in found_posts:
                    LOGGER.error(f"ITEM ADDED FROM POSTS IS ALREADY IN DB: {post['url']}")
                else:
                    LOGGER.info("Adding Post to DB %s", post['url'])
                    
                    add_reddit_post_clip(
                        post_id=post_id,
                        title=post['title'],
                        posted_at=post['posted_at'],
                        content=post['content'],
                        url=post['url'],
                        upvotes=post['upvotes'],
                        comments=post['comments'],
                        nsfw=post['nsfw'],
                        parent_id=par_post_id,
                        author=post['author']
                        )
                    
            else:
                LOGGER.error(f"Invalid URL: {post['url']}")
    #####################################
    # Remove from list if 160 words not met
    #####################################
    unused_posts = get_rows_where_tiktok_null_or_empty()
    posts_to_use = {}
    for post in unused_posts:
        if len(post.get('content', "").split()) > 160 and len(post.get('content', "").split()) < 2000 and not post['nsfw']: # 160 minium words in a post
            LOGGER.info("Post to use %s", post['post_id'])
            posts_to_use[post['post_id']] = (post)
            
    #####################################
    # Censor bad words
    #####################################
    if not args.usevids:
        for pid, post in posts_to_use.items():
            # run video creator that combines video with audio with transcript
            posts_to_use[pid]['content'] = reddit_acronym(reddit_remove_bad_words(post['title'] + " " + post['content']))
            LOGGER.info("Censored %s", posts_to_use[pid]['content'].split()[0:10])
        for pid, post in posts_to_use.items():
            if posts_to_use[pid]['content'] != post['content']:
                LOGGER.error("Censored didnt take")
                exit()
    #####################################
    # Create Audio using TTS
    #####################################
    if not args.usevids:
        tts_model = TTSModelKokoro()
        for pid, post in posts_to_use.items():
            LOGGER.info("Creating Audio for %s", pid)
            posts_to_use[pid]['filename'] = f"tmp/audios/{pid}_tts.wav"
            if not os.path.exists(f"tmp/audios/{pid}_tts.wav"):
                tts_model.run_it(posts_to_use[pid]['filename'], posts_to_use[pid]['content'])
    #####################################
    # Force align text to audio
    #####################################
    device = "cpu"
    if torch.cuda.is_available():
        device = "cuda:0"
        torch.cuda.empty_cache()
    for pid, post in posts_to_use.items():
        LOGGER.info("Aligning %s", pid)
        if not post.get('transcript', None):
            LOGGER.info("Aligning %s, %s", post['filename'], type(posts_to_use[pid]['content']))
            posts_to_use[pid]['aligned_ts'] = force_align(device=device, file=str(post['filename']), yt_ft_transcript=str(posts_to_use[pid]['content']))
            if posts_to_use[pid]['aligned_ts'] != []:
                LOGGER.info("Aligned %s",posts_to_use[pid]['aligned_ts'][-1])
            update_reddit_post_clip(
                post_id=pid,
                transcript=json.dumps(posts_to_use[pid]['aligned_ts'])
            )
        else:
            posts_to_use[pid]['aligned_ts'] = json.loads(post
            ['transcript'])
    #####################################
    # Split audio into parts
    #####################################
    for pid, post in posts_to_use.items():
        posts_to_use[pid]['audio_length'] = get_audio_duration(post['filename'])
        posts_to_use[pid]['part_start']:list[int] = split_audio(posts_to_use[pid]['audio_length'], post['aligned_ts'])
        posts_to_use[pid]['parts'] = 1 #len(posts_to_use[pid]['part_start'])
        LOGGER.info("Audio length, parts: %s, %s, %s", posts_to_use[pid]['audio_length'], posts_to_use[pid]['parts'], posts_to_use[pid]['part_start'])
    ########################################
    # Calc time to post
    ########################################
    day_sched = none_old_timestamps()
    rand_posts = sample(list(posts_to_use.keys()), len(day_sched))
    for i, pid in enumerate(rand_posts):
        posts_to_use[pid]['sched'] = day_sched[i]
        LOGGER.info("Post sched %s, %s", pid, posts_to_use[pid]['sched'])
    #####################################
    # Create video
    #####################################
    if not args.usevids:
        mpfours = [file for file in os.listdir(REDDIT_TEMPLATE_BG) if file.endswith(".mp4")]
        for pid, post in posts_to_use.items():
            sub_name = post['url'].split("/")[2]
            do_it = False
            for part_url in post['url'].split("/"):
                if "r" in part_url.lower():
                    do_it = True
                elif do_it:
                    sub_name = part_url
                    break
            LOGGER.info("Subreddit: %s", sub_name)
            # Create img for post
            post_png_file = render_html_to_png(
                post_id=pid,
                title=post['title'],
                subreddit=sub_name,
                subreddit_id=sub_name,
                user_id="reddit",
                user_name=post['author'],
                time_ago=datetime.fromisoformat(post['posted_at'][:-2] + ':' + post['posted_at'][-2:]),
                score_int=post['upvotes'],
                comment_int=post['comments']
            )
            
            background = choice(mpfours)
            clip_length = get_clip_duration(os.path.join(REDDIT_TEMPLATE_BG, background))
            LOGGER.info("Clip, length, pid: %s, %s, %s", background, clip_length, pid)
            # Grab random part from mc parkor/subway surfers/temple run
            start = randint(0, int(clip_length - posts_to_use[pid]['audio_length']+1))
            end = start + posts_to_use[pid]['audio_length']
            # run video creator that combines video with audio with transcript
            posts_to_use[pid]['vfile'] = f"tmp/clips/reddit_{pid}.mp4"
            create_reddit_video(
                video_path=os.path.join(REDDIT_TEMPLATE_BG, background),
                audio_path=post['filename'],
                output_path=posts_to_use[pid]['vfile'],
                start_time=start,
                end_time=end,
                pid=pid,
                part_start=post['part_start'],
                parts=posts_to_use[pid]['parts'],
                transcript=post['aligned_ts'],
                th=1080,
                tw=1920,
                paragraph=posts_to_use[pid]['content'],
                post_png_file=post_png_file,
                title=reddit_acronym(reddit_remove_bad_words(post['title']))
            )
    else:
        for pid, post in posts_to_use.items():
            posts_to_use[pid]['vfile'] = f"tmp/clips/reddit_{pid}.mp4"
            posts_to_use[pid]['parts'] = 1
            posts_to_use[pid]['filename'] = f"tmp/audios/{pid}_tts.wav"
    
    ######################################
    # Compile Description
    ######################################
    for pid, post in posts_to_use.items():
        if post.get('parts', 1) > 1:
            posts_to_use[pid]["desc"] = []
            for i in range(post['parts']):
                posts_to_use[pid]["desc"].append(
                    f"#part{i+1} #fyp #reddit #clip #fyppppppppppppp\ncredit"
                    f"{post['title']} on Reddit\n"
                )  
        else:
            posts_to_use[pid]["desc"] = (
                "#fyp #reddit #clip #fyppppppppppppp\ncredit"
                f"{post['title']} on Reddit\n"
            )  
    #####################################
    # Upload tiktok
    #####################################
    for pid, post in posts_to_use.items():
        if not post.get("sched"):
            continue
        if not args.dryrun:
            if post.get('parts', 1) > 1:
                for i in range(post['parts']):
                    upload_video_tt(
                            os.path.abspath(post['vfile'].replace(f"{pid}", f"{pid}_p{i}")),
                            post['sched'],
                            post["desc"][i],
                            submit=True
                        )
            else:
                upload_video_tt(
                                os.path.abspath(post['vfile']), 
                                post['sched'], 
                                post["desc"], 
                                submit=True
                            )
            
            update_reddit_post_clip(
                post_id=pid, 
                tiktok_posted=post['sched'], 
                length=post['audio_length']
            )
        else:
            if post.get('parts', 1) > 1:
                for i in range(post['parts']):
                    upload_video_tt(
                            os.path.abspath(post['vfile'].replace(f"{pid}", f"{pid}_p{i}")),
                            post['sched'],
                            post["desc"][i],
                            submit=False
                        )
            else:
                upload_video_tt(
                                os.path.abspath(post['vfile']), 
                                post['sched'], 
                                post["desc"], 
                                submit=False
                            )
    #####################################
    # Clean up
    #####################################
    if not args.dryrun:
        for pid, post in posts_to_use.items():
            if 'sched' not in post.keys():
                continue
            if post.get('parts', 1) > 1:
                for i in range(post['parts']):
                    shutil.copyfile(post['vfile'].replace(f"{pid}", f"{pid}_p{i}"), f"{CLIPS_FOLDER}/reddit_p_{pid}.mp4")
                    os.remove(post['vfile'].replace(f"{pid}", f"{pid}_p{i}"))
            else:
                shutil.copyfile(post['vfile'], f"{CLIPS_FOLDER}/reddit_p_{pid}.mp4")
                os.remove(post['vfile'])
            os.remove(post['filename'])
    LOGGER.info("Reddit posts done")
    
if __name__ == "__main__":
    main_reddit_posts_orch()
    
    
        