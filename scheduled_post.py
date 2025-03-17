from clip_creator.conf import (
    POSSIBLE_TRANSLATE_LANGS,
    LOGGER,
    CLIPS_FOLDER,
    
)
import logging
import os
import random
import argparse
from datetime import datetime, timedelta
from clip_creator.adb.not_bort import ADBScroll
from clip_creator.utils.scan_text import reddit_remove_bad_words, reddit_acronym, split_audio, get_top_posts, swap_words_numbers, remove_non_letters, dirty_remove_cuss, get_id_from_vfile, str_to_datetime
from clip_creator.lang.translate import translate_en_to
from clip_creator.adb.tiktok_auto import upload_phsyphone
from clip_creator.db.db import get_rows_where_tiktok_not_null_or_empty, update_reddit_post_clip_sc

def sched_run(skipscroll=False):
    """
    This function is used to run the scheduled task.
    It will run the scheduled task every few hours-4x a day.
    """
    parser = argparse.ArgumentParser(description="AI Clip Creator")
    parser.add_argument("--scrolltime", type=int, help="Number of minutes to scroll")
    parser.add_argument("--skipscroll", action="store_true", help="Skip scrolling")
    args = parser.parse_args()
    #####################################
    # Scroll more
    #####################################
    if not args.skipscroll and not skipscroll:
        ############## Scroll ##############
        try:
            adb = ADBScroll()
            if args.scrolltime:
                max_time_min = args.scrolltime
            else:
                max_time_min = random.randint(10, 35)
            adb.scroll_tiktok(max_time_min=max_time_min)
            LOGGER.info("Stopping...")
            adb.running = False
            adb.kill_apps()
            LOGGER.info("Stopped.")
        except Exception as e:
            LOGGER.error("Error scrolling: %s", e)
            
    #####################################
    # Setup logging
    #####################################
    file_handler = logging.FileHandler("logs/schedule_runner.log")
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    )
    LOGGER.addHandler(file_handler)
    LOGGER.info("Running scheduled task...")
    all_posts_to_post = get_rows_where_tiktok_not_null_or_empty()
    posts_to_use = {}
    for post in all_posts_to_post:
        if post.get('tiktok_posted') and post.get('tiktok_posted') != "None" and not post.get('tiktok_uploaded'):
            
            try:
                dt_t = datetime.strptime(post.get('tiktok_posted').split(".")[0], "%Y-%m-%d %H:%M:%S")
            except Exception as e:
                LOGGER.error("Error parsing date: %s", e)
                continue
            if dt_t > datetime.now(): # 160 minium words in a post
                LOGGER.info("Post to use %s", post['post_id'])
                posts_to_use[post['post_id']] = (post)
                posts_to_use[post['post_id']]["vfile"] = f"{CLIPS_FOLDER}/reddit_{post['post_id']}.mp4"
                if post.get('parts', 1) > 1:
                    posts_to_use[post['post_id']]["desc"] = []
                    for i in range(post['parts']):
                        posts_to_use[post['post_id']]["desc"].append(
                            f"Part {i+1} | {reddit_remove_bad_words(post['title'])}\n\n"
                            f"#part{i+1} #reddit #reddittreadings #reddit_tiktok \n #redditstorytime #askreddit #fyp"
                            
                        )  
                else:
                    posts_to_use[post['post_id']]["desc"] = (
                        f"{reddit_remove_bad_words(post['title'])}\n\n"
                        "#reddit #reddittreadings #reddit_tiktok \n #redditstorytime #askreddit #fyp"
                    )
                for lang in POSSIBLE_TRANSLATE_LANGS:
                    posts_to_use[post['post_id']][f"vfile_{lang}"] = f"{CLIPS_FOLDER}/reddit{lang}_{post['post_id']}.mp4"
                    if post.get('parts', 1) > 1:
                        posts_to_use[post['post_id']][f"desc_{lang}"] = []
                        for i in range(post['parts']):
                            posts_to_use[post['post_id']][f"desc_{lang}"].append(translate_en_to(posts_to_use[post['post_id']]["desc"][i], lang))
                    else:
                        posts_to_use[post['post_id']][f"desc_{lang}"] = translate_en_to(posts_to_use[post['post_id']]["desc"], lang)
    
    for pid, post in posts_to_use.items():
        LOGGER.info(f"Running scheduled task for {post}...")
        suvvedd = upload_phsyphone(
            os.path.abspath(posts_to_use[post['post_id']]["vfile"]),
            posts_to_use[post['post_id']]["desc"],
            )
        if not suvvedd:
            LOGGER.error("Error uploading video")
            continue
        update_reddit_post_clip_sc(post['post_id'], True)
        for lang in POSSIBLE_TRANSLATE_LANGS:
            LOGGER.info(f"Running scheduled task for {lang}...")
            upload_phsyphone(
            os.path.abspath(posts_to_use[post['post_id']][f"vfile_{lang}"]),
            posts_to_use[post['post_id']][f"desc_{lang}"],
            lang=lang
            )
        LOGGER.info("Scheduled task completed.")
        break
    #####################################
    # Scroll more
    #####################################
    if not args.skipscroll and not skipscroll:
        try:
            adb = ADBScroll()
            if args.scrolltime:
                max_time_min = args.scrolltime
            else:
                max_time_min = random.randint(10, 35)
            adb.scroll_tiktok(max_time_min=max_time_min)
            LOGGER.info("Stopping...")
            adb.running = False
            adb.kill_apps()
            LOGGER.info("Stopped.")
        except Exception as e:
            LOGGER.error("Error scrolling: %s", e)    
    
    
if __name__ == "__main__":
    sched_run()
