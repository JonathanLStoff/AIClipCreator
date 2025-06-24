import argparse
import logging
import os
import random

from clip_creator.adb.not_bort import ADBScroll
from clip_creator.adb.tiktok_auto import upload_phsyphone
from clip_creator.conf import (
    CLIPS_FOLDER,
    LOGGER,
    POSSIBLE_TRANSLATE_LANGS,
)
from clip_creator.db.db import (
    update_reddit_post_clip_sc_aiyt,
    update_reddit_post_clip_sc_com,
    get_rows_where_tiktok_not_null_or_empty_com,
    get_rows_where_tiktok_not_null_or_empty_aiyt
)
from clip_creator.lang.translate import translate_en_to
from clip_creator.utils.scan_text import (
    reddit_remove_bad_words,
)


def sched_run(skipscroll=False):
    """
    This function is used to run the scheduled task.
    It will run the scheduled task every few hours-4x a day.
    """
    parser = argparse.ArgumentParser(description="AI Clip Creator")
    parser.add_argument("--scrolltime", type=int, help="Number of minutes to scroll")
    parser.add_argument("--skipscroll", action="store_true", help="Skip scrolling")
    parser.add_argument("--scrollonly", action="store_true", help="scroll")
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
                max_time_min = random.randint(5, 10)
            adb.scroll_tiktok(max_time_min=max_time_min)
            LOGGER.info("Stopping...")
            adb.running = False
            adb.kill_apps()
            LOGGER.info("Stopped.")
        except Exception as e:
            LOGGER.error("Error scrolling: %s", e)
        if args.scrollonly:
            return
    #####################################
    # Setup logging
    #####################################
    file_handler = logging.FileHandler("logs/schedule_runner.log")
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    )
    LOGGER.addHandler(file_handler)
    LOGGER.info("Running scheduled task...")
    all_posts_to_post = [post for post in get_rows_where_tiktok_not_null_or_empty_aiyt() if post.get("tiktok_posted") and post.get("tiktok_uploaded") != "None" and not post.get("tiktok_uploaded")]
    more_posts = [post for post in get_rows_where_tiktok_not_null_or_empty_com() if post.get("tiktok_posted") and post.get("tiktok_uploaded") != "None" and not post.get("tiktok_uploaded")]
    LOGGER.info("more_posts: %s", len(more_posts))
    all_all_reddit = []
    for post in more_posts:
        post["type"] = "coms"
        all_all_reddit.append(post)
    for post in all_posts_to_post:
        post["type"] = "aiyt"
        all_all_reddit.append(post)
        
    posts_to_use = {}

        
    random.shuffle(all_all_reddit)
    for post in all_all_reddit:
        if (
            post.get("tiktok_posted")
            and post.get("tiktok_posted") != "None"
            and not post.get("tiktok_uploaded")
        ):
            # No need to check date, just that it hasn't been posted
            ############## Post ##############

            LOGGER.info("Post to use %s", post["post_id"])
            posts_to_use[post["post_id"]] = post
            posts_to_use[post["post_id"]][
                "vfile"
            ] = f"{CLIPS_FOLDER}/reddit_{post['post_id']}.mp4"
            if post.get("parts", 1) > 1:
                posts_to_use[post["post_id"]]["desc"] = []
                for i in range(post["parts"]):
                    posts_to_use[post["post_id"]]["desc"].append(
                        f"Part {i+1} |"
                        f" {post['title']}\n\n#part{i+1} #reddit"
                        " #reddittreadings #reddit_tiktok \n #redditstorytime"
                        " #askreddit #fyp"
                    )
            else:
                posts_to_use[post["post_id"]]["desc"] = (
                    f"{post['title']}\n\n#reddit"
                    " #reddittreadings #reddit_tiktok \n #redditstorytime #askreddit"
                    " #fyp"
                )
            for lang in POSSIBLE_TRANSLATE_LANGS:
                posts_to_use[post["post_id"]][
                    f"vfile_{lang}"
                ] = f"{CLIPS_FOLDER}/reddit{lang}_{post['post_id']}.mp4"
                if post.get("parts", 1) > 1:
                    posts_to_use[post["post_id"]][f"desc_{lang}"] = []
                    for i in range(post["parts"]):
                        posts_to_use[post["post_id"]][f"desc_{lang}"].append(
                            translate_en_to(
                                posts_to_use[post["post_id"]]["desc"][i], lang
                            )
                        )
                else:
                    posts_to_use[post["post_id"]][f"desc_{lang}"] = translate_en_to(
                        posts_to_use[post["post_id"]]["desc"], lang
                    )

    for pid, post in posts_to_use.items():
        LOGGER.info(f"Running scheduled task for {pid}...")
        if post.get("parts", 1) > 1:
            skip_this_post = False
            for i in range(post["parts"]):
                if not os.path.exists(os.path.abspath(f"tmp/clips/reddit_{pid}_{i}.mp4")):
                    LOGGER.error(
                        "File %s does not exist, skipping post %s",
                        f"tmp/clips/reddit_{pid}_{i}.mp4",
                        pid,
                    )
                    skip_this_post = True
                    break
            if skip_this_post:
                LOGGER.error("Skipping post %s", pid)
                continue
            for i in range(post["parts"]):
                suvvedd = False
                max_retries = 5
                while not suvvedd:
                    suvvedd = upload_phsyphone(
                        os.path.abspath(f"tmp/clips/reddit_{pid}_{i}.mp4"),
                        posts_to_use[pid]["desc"][i],
                    )
                    if not suvvedd:
                        LOGGER.error("Error uploading video")
                        max_retries -= 1
                        if max_retries <= 0:
                            LOGGER.error("Max retries reached, skipping post %s", pid)
                            skip_this_post = True
                            break
                if skip_this_post:
                    LOGGER.error("Skipping post %s", pid)
                    break
            if skip_this_post:
                LOGGER.error("Skipping post %s", pid)
                continue
        else:
            suvvedd = upload_phsyphone(
                os.path.abspath(posts_to_use[post["post_id"]]["vfile"]),
                posts_to_use[post["post_id"]]["desc"],
            )
        if not suvvedd:
            LOGGER.error("Error uploading video")
            continue
        if post["type"] == "coms":
            update_reddit_post_clip_sc_com(post["post_id"], True)
        else:
            
            update_reddit_post_clip_sc_aiyt(post["post_id"], True)
        for lang in POSSIBLE_TRANSLATE_LANGS:
            LOGGER.info(f"Running scheduled task for {lang}...")
            upload_phsyphone(
                os.path.abspath(posts_to_use[post["post_id"]][f"vfile_{lang}"]),
                posts_to_use[post["post_id"]][f"desc_{lang}"],
                lang=lang,
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
