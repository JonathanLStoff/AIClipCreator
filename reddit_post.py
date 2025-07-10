import argparse
import json
import os
import shutil
import threading
import time
import traceback
import uuid
from datetime import UTC, datetime, timedelta
from random import choice, randint

import torch
from urlextract import URLExtract
from clip_creator.adb.not_bort import ADBScroll
from clip_creator.conf import (
    CLIPS_FOLDER,
    LOGGER,
    POSSIBLE_TRANSLATE_LANGS,
    POSSIBLE_TRANSLATE_LANGS_TTS,
    REDDIT_TEMPLATE_BG,
    TMP_CLIPS_FOLDER,
)
from clip_creator.db.db import (
    add_reddit_post_clip,
    create_database,
    get_all_post_ids_red,
    get_reddit_post_clip_by_id,
    get_rows_where_tiktok_null_or_empty,
    update_reddit_post_clip_at,
    update_reddit_post_clip_old,
    update_reddit_post_clip_tt,
)
from clip_creator.lang.translate import translate_en_to
from clip_creator.social.custom_tiktok import upload_video_tt
from clip_creator.social.reddit import (
    find_sub_reddit_posts,
    find_top_sub_reddit_posts,
    reddit_posts_orch,
    straight_update_reddit,
)
from clip_creator.tts.ai import TTSModelKokoro
from clip_creator.utils.caption_img import render_html_to_png
from clip_creator.utils.forcealign import force_align
from clip_creator.utils.path_setup import check_and_create_dirs
from clip_creator.utils.scan_text import (
    dirty_remove_cuss,
    get_id_from_vfile,
    get_top_posts,
    reddit_acronym,
    reddit_remove_bad_words,
    remove_non_letters,
    split_audio,
    str_to_datetime,
    swap_words_numbers,
    remove_markdown_links_images,
    fix_update_order
)
from clip_creator.utils.schedules import none_old_timestamps
from clip_creator.vid_ed.red_vid_edit import (
    create_reddit_video,
    get_audio_duration,
    get_clip_duration,
)


def main_reddit_posts_orch():
    parser = argparse.ArgumentParser(description="AI Clip Creator")
    parser.add_argument(
        "--noretrieve",
        action="store_true",
        help="Retrieve new videos from YouTube if not set",
    )
    parser.add_argument(
        "--doupdate",
        action="store_true",
        help="Retrieve updates if noretrieve is set",
    )
    parser.add_argument(
        "--dryrun",
        action="store_true",
        help="Does everything but post to TikTok, save db and remove files",
    )
    parser.add_argument(
        "--skipup",
        action="store_true",
        help="Does everything but post to TikTok, save db and remove files",
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
    parser.add_argument(
        "--skipscroll",
        action="store_true",
        help="skip scrolling",
    )
    args = parser.parse_args()
    LOGGER.info("Arguments: %s", args)
    try:
        #####################################
        # Set up paths
        #####################################
        bad_pids = []
        check_and_create_dirs()
        #####################################
        # Start Scrolling
        #####################################
        if not args.skipscroll and not args.dryrun:
            ############## Scroll ##############
            try:
                adb = ADBScroll()
                adb_thread = threading.Thread(target=adb.scroll_tiktok)
                adb_thread.start()
            except Exception:
                pass
        #####################################
        # Create database
        #####################################
        create_database()
        found_posts = get_all_post_ids_red()

        if not args.noretrieve and not args.usevids:
            href_list = find_sub_reddit_posts(found_posts, min_posts=10, max_posts=20)
            href_list.extend(find_top_sub_reddit_posts(found_posts, min_posts=1))
            netw_redd_posts = reddit_posts_orch(
                href_list, found_posts, min_post=10, max_post=20
            )

            #####################################
            # Add posts to database
            #####################################
            for post in netw_redd_posts:
                if "/" in post["url"]:
                    do_it = False
                    post_id = str(uuid.uuid4())
                    for party in post["url"].split("/"):
                        if "comment" in party.lower():
                            do_it = True
                        elif do_it:
                            post_id = party
                            break
                    par_post_id = None
                    if post.get("parent_href"):
                        do_it = False

                        for party in post.get("parent_href").split("/"):
                            if "comment" in party.lower():
                                do_it = True
                            elif do_it:
                                par_post_id = party
                                break
                    if post_id in found_posts:
                        LOGGER.error(
                            f"ITEM ADDED FROM POSTS IS ALREADY IN DB: {post['url']}"
                        )
                    else:
                        LOGGER.info("Adding Post to DB %s", post["url"])

                        add_reddit_post_clip(
                            post_id=post_id,
                            title=post["title"],
                            posted_at=post["posted_at"],
                            content=post["content"],
                            url=post["url"],
                            upvotes=post["upvotes"],
                            comments=post["comments"],
                            nsfw=post["nsfw"],
                            parent_id=par_post_id,
                            author=post["author"],
                            updated_at=datetime.now().strftime(
                                "%Y-%m-%dT%H:%M:%S.%f+0000"
                            ),
                        )

                else:
                    LOGGER.error(f"Invalid URL: {post['url']}")
        #####################################
        # Remove from list if 160 words not met
        #####################################
        unused_posts = get_rows_where_tiktok_null_or_empty()
        posts_to_use = {}
        for post in unused_posts:
            if (
                len(post.get("content", "").split()) > 160
                and len(post.get("content", "").split()) < 3000
                and not post["nsfw"]
            ):  # 160 minium words in a post
                LOGGER.info("Post to use %s", post["post_id"])
                posts_to_use[post["post_id"]] = post
        #####################################
        # Check if Updates are needed
        #####################################
        href_list = []
        num_updates = 0
        if (
            (args.noretrieve and args.doupdate)
            or (not args.noretrieve and not args.doupdate and False)
        ) and not args.usevids:
            for pid, post in posts_to_use.items():
                if num_updates > 15:
                    break
                if post.get("updated_at") is not None and post.get("updated_at") != "":
                    post_dt = str_to_datetime(post.get("updated_at", ""))
                else:
                    post_dt = str_to_datetime(post.get("posted_at", ""))
                LOGGER.debug("Post dt: %s", post_dt)
                if (datetime.now(UTC) - post_dt) > timedelta(days=7) and str_to_datetime(post.get("posted_at", "")) > datetime.now(UTC) - timedelta(days=14):
                    posty = straight_update_reddit(post.get("url", ""))
                    num_updates += 1
                    LOGGER.info("Posty: %s",  posty.get("title"))
                    if posty.get("title"):
                        LOGGER.debug("Updating Post on time %s", posty["url"])
                        LOGGER.info("number of updates: %s", num_updates)
                        update_reddit_post_clip_old(
                            post_id=pid,
                            title=posty["title"],
                            posted_at=posty["posted_at"],
                            content=posty["content"],
                            url=posty["url"],
                            upvotes=posty["upvotes"],
                            comments=posty["comments"],
                            nsfw=posty["nsfw"],
                            author=posty["author"],
                            updated_at=datetime.now().strftime(
                                "%Y-%m-%dT%H:%M:%S.%f+0000"
                            ),
                        )
        #####################################
        # Remove urls/Fetch updates
        #####################################
        url_finder = URLExtract()
        if not args.usevids:
            for pid, post in posts_to_use.items():
                if url_finder.has_urls(post.get("content", "")):
                    found_urls:list[str] = url_finder.find_urls(post["content"])
                    for url in found_urls:
                        post["content"] = remove_markdown_links_images(post.get("content", "")).replace(url, "")
                        # if "reddit" in str(url):
                        #     found_pid = False
                        #     for pid in posts_to_use.keys():
                        #         if pid in url:
                        #             found_pid = True
                        #             break
                            # if not found_pid:
                            #     posty = straight_update_reddit(url)
                            #     if posty.get("title"):
                            #         LOGGER.info("Updating Post %s", posty["url"])
                            #         add_reddit_post_clip(
                            #             post_id=post_id,
                            #             title=post["title"],
                            #             posted_at=post["posted_at"],
                            #             content=post["content"],
                            #             url=post["url"],
                            #             upvotes=post["upvotes"],
                            #             comments=post["comments"],
                            #             nsfw=post["nsfw"],
                            #             parent_id=pid,
                            #             author=post["author"],
                            #             updated_at=datetime.now().strftime(
                            #                 "%Y-%m-%dT%H:%M:%S.%f+0000"
                            #             ),
                            #         )
                    if "update" in post.get("title", "").lower() and (found_urls == [] or not found_urls):
                        #TODO: Do something to collect the updates from user account
                        pass
        ########################################
        # Calc time to post
        ########################################
        day_sched = none_old_timestamps()
        LOGGER.info("Day Sched: %s", day_sched)
        # rand_posts = sample(list(posts_to_use.keys()), len(day_sched))
        if not args.usevids:
            best_posts = get_top_posts(posts_to_use, len(day_sched))

        else:
            LOGGER.info("Using created videos")
            best_posts = []
            for file in os.listdir(TMP_CLIPS_FOLDER):
                pid_tmp = get_id_from_vfile(file)
                if pid_tmp:
                    posts_to_use[pid_tmp] = get_reddit_post_clip_by_id(pid_tmp)
                    best_posts.append(pid_tmp)
        poping = []
        for i, sched in enumerate(day_sched):
            if sched is None:
                LOGGER.info("Poping %s", i)
                poping.append(i)
        for i, ix in enumerate(poping):
            day_sched.pop(ix - i)
        LOGGER.info("Day Sched: %s", day_sched)
        posts_to_keep = {}
        for i, pid in enumerate(best_posts):
            if i >= len(day_sched):
                break
            posts_to_keep[pid] = posts_to_use[pid]
            posts_to_keep[pid]["sched"] = day_sched[i]
            LOGGER.info("Post sched %s, %s", pid, posts_to_keep[pid]["sched"])
        posts_to_use = posts_to_keep
        #####################################
        # Censor bad words
        #####################################
        if not args.usevids:
            for pid, post in posts_to_use.items():
                # run video creator that combines video with audio with transcript
                try:
                    post["content"] = fix_update_order(post["content"])
                except Exception as e:
                    LOGGER.error("Error: %s", traceback.format_exc()) 
                posts_to_use[pid]["content"] = remove_non_letters(
                    swap_words_numbers(
                        reddit_acronym(
                            reddit_remove_bad_words(
                                post["title"] + " " + post["content"]
                            )
                        )
                    )
                )
                LOGGER.info("Censored %s", posts_to_use[pid]["content"].split()[0:10])
            for pid, post in posts_to_use.items():
                if posts_to_use[pid]["content"] != post["content"]:
                    LOGGER.error("Censored didnt take")
                    exit()
        #####################################
        # Translate to other languages
        #####################################
        if not args.usevids:
            for pid, post in posts_to_use.items():
                for lang in POSSIBLE_TRANSLATE_LANGS:
                    LOGGER.info("Translating %s to %s", pid, lang)
                    posts_to_use[pid][f"content_{lang}"] = translate_en_to(
                        posts_to_use[pid]["content"], lang
                    )
        #####################################
        # Create Audio using TTS
        #####################################
        if not args.usevids:
            tts_model = TTSModelKokoro()
            for pid, post in posts_to_use.items():
                LOGGER.info("Creating Audio for %s", pid)
                posts_to_use[pid]["filename"] = f"tmp/audios/{pid}_tts.wav"
                if not os.path.exists(f"tmp/audios/{pid}_tts.wav"):
                    tts_model.run_it(
                        posts_to_use[pid]["filename"], posts_to_use[pid]["content"]
                    )

            # Create Audio for other languages

            for lang in POSSIBLE_TRANSLATE_LANGS:
                tts_model_lang = TTSModelKokoro(
                    voice=choice(POSSIBLE_TRANSLATE_LANGS_TTS[lang]["tts"]),
                    lang_code=POSSIBLE_TRANSLATE_LANGS_TTS[lang][lang],
                )
                for pid, post in posts_to_use.items():
                    LOGGER.info("Creating Audio for %s", pid)
                    posts_to_use[pid][
                        f"filename_{lang}"
                    ] = f"tmp/audios/{pid}_{lang}_tts.wav"
                    if not os.path.exists(f"tmp/audios/{pid}_{lang}_tts.wav"):
                        tts_model_lang.run_it(
                            posts_to_use[pid][f"filename_{lang}"],
                            posts_to_use[pid][f"content_{lang}"],
                        )
        #####################################
        # Force align text to audio
        #####################################
        device = "cpu"
        if torch.cuda.is_available():
            device = "cuda:0"
            torch.cuda.empty_cache()
        if not args.usevids:
            for pid, post in posts_to_use.items():
                LOGGER.info(
                    "Aligning %s, %s, %s",
                    pid,
                    post["filename"],
                    posts_to_use[pid]["content"][0:10],
                )

                if not os.path.exists(post["filename"]):
                    LOGGER.error("Audio file not found %s", post["filename"])
                    bad_pids.append(pid)
                    continue
                posts_to_use[pid]["aligned_ts"] = force_align(
                    device=device,
                    file=str(post["filename"]),
                    yt_ft_transcript=str(posts_to_use[pid]["content"]),
                )
                if posts_to_use[pid]["aligned_ts"] != []:
                    LOGGER.debug("Aligned %s", posts_to_use[pid]["aligned_ts"][-1])
                update_reddit_post_clip_at(
                    post_id=pid, transcript=json.dumps(posts_to_use[pid]["aligned_ts"])
                )
                for lang in POSSIBLE_TRANSLATE_LANGS:
                    LOGGER.info(
                        "Aligning %s, %s, %s",
                        pid,
                        post[f"filename_{lang}"],
                        posts_to_use[pid][f"content_{lang}"][0:10],
                    )
                    if not os.path.exists(post[f"filename_{lang}"]):
                        LOGGER.error(
                            "Audio file not found %s", post[f"filename_{lang}"]
                        )
                        bad_pids.append(pid)
                        continue
                    posts_to_use[pid][f"aligned_ts_{lang}"] = force_align(
                        device=device,
                        file=str(post[f"filename_{lang}"]),
                        yt_ft_transcript=str(posts_to_use[pid][f"content_{lang}"]),
                    )
            for pid in bad_pids:
                posts_to_use.pop(pid)
            bad_pids = []
        #####################################
        # Split audio into parts
        #####################################
        if not args.usevids:
            new_posts_to_use = {}
            for pid, post in posts_to_use.items():
                posts_to_use[pid]["audio_length"] = get_audio_duration(
                    post.get("filename", None)
                )
                if not posts_to_use[pid]["audio_length"]:
                    posts_to_use[pid]["audio_length"] = (
                        post["aligned_ts"][-1]["start"]
                        + post["aligned_ts"][-1]["duration"]
                    )
                posts_to_use[pid]["part_start"]: list[int] = split_audio(
                    posts_to_use[pid]["audio_length"], post["aligned_ts"]
                )
                posts_to_use[pid]["parts"] = 1  # len(posts_to_use[pid]['part_start'])
                LOGGER.info(
                    "Audio length, parts: %s, %s, %s",
                    posts_to_use[pid]["audio_length"],
                    posts_to_use[pid]["parts"],
                    posts_to_use[pid]["part_start"],
                )
                # if posts_to_use[pid]['audio_length'] < 60:
                #     LOGGER.error("Audio too short")
                # else:
                new_posts_to_use[pid] = posts_to_use[pid]
                for lang in POSSIBLE_TRANSLATE_LANGS:
                    posts_to_use[pid][f"audio_length_{lang}"] = get_audio_duration(
                        post.get(f"filename_{lang}", None)
                    )
                    if not posts_to_use[pid][f"audio_length_{lang}"]:
                        posts_to_use[pid][f"audio_length_{lang}"] = (
                            post[f"aligned_ts_{lang}"][-1]["start"]
                            + post[f"aligned_ts_{lang}"][-1]["duration"]
                        )
                    posts_to_use[pid][f"part_start_{lang}"]: list[int] = split_audio(
                        posts_to_use[pid][f"audio_length_{lang}"],
                        post[f"aligned_ts_{lang}"],
                    )
                    posts_to_use[pid][
                        f"parts_{lang}"
                    ] = 1  # len(posts_to_use[pid][f'part_start_{lang}'])
                    LOGGER.info(
                        "Audio length, parts: %s, %s, %s",
                        posts_to_use[pid][f"audio_length_{lang}"],
                        posts_to_use[pid][f"parts_{lang}"],
                        posts_to_use[pid][f"part_start_{lang}"],
                    )
                    # if posts_to_use[pid][f'audio_length_{lang}'] < 60:
                    #     LOGGER.error("Audio too short")
                    # else:
                    new_posts_to_use[pid] = posts_to_use[pid]
            posts_to_use = new_posts_to_use

        #####################################
        # Create video
        #####################################
        if not args.usevids:
            mpfours = [
                file for file in os.listdir(REDDIT_TEMPLATE_BG) if file.endswith(".mp4")
            ]
            for pid, post in posts_to_use.items():
                LOGGER.info("Post: %s", pid)
                if not post.get(
                    "sched"
                ):  # or posts_to_use[pid].get("audio_length") < 60:
                    continue
                sub_name = post["url"].split("/")[2]
                do_it = False
                for part_url in post["url"].split("/"):
                    if "r" in part_url.lower():
                        do_it = True
                    elif do_it:
                        sub_name = part_url
                        break
                LOGGER.info("Subreddit: %s", sub_name)
                # Create img for post
                post_png_file = render_html_to_png(
                    post_id=pid,
                    title=post["title"],
                    subreddit=sub_name,
                    subreddit_id=sub_name,
                    user_id="reddit",
                    user_name=dirty_remove_cuss(post["author"]),
                    time_ago=datetime.fromisoformat(
                        post["posted_at"][:-2] + ":" + post["posted_at"][-2:]
                    ),
                    score_int=post["upvotes"],
                    comment_int=post["comments"],
                )

                background = choice(mpfours)
                clip_length = get_clip_duration(
                    os.path.join(REDDIT_TEMPLATE_BG, background)
                )
                LOGGER.info(
                    "Clip, length, pid: %s, %s, %s", background, clip_length, pid
                )
                # Grab random part from mc parkor/subway surfers/temple run
                start = randint(
                    0, int(clip_length - posts_to_use[pid]["audio_length"] + 1)
                )
                end = start + posts_to_use[pid]["audio_length"]
                # run video creator that combines video with audio with transcript
                posts_to_use[pid]["vfile"] = f"tmp/clips/reddit_{pid}.mp4"
                create_reddit_video(
                    video_path=os.path.join(REDDIT_TEMPLATE_BG, background),
                    audio_path=posts_to_use[pid]["filename"],
                    output_path=posts_to_use[pid]["vfile"],
                    start_time=start,
                    end_time=end,
                    pid=pid,
                    part_start=posts_to_use[pid]["part_start"],
                    parts=posts_to_use[pid]["parts"],
                    transcript=posts_to_use[pid]["aligned_ts"],
                    tw=1080,
                    th=1920,
                    paragraph=posts_to_use[pid]["content"],
                    post_png_file=post_png_file,
                    title=swap_words_numbers(
                        reddit_acronym(
                            reddit_remove_bad_words(posts_to_use[pid]["title"])
                        )
                    ),
                )
                for lang in POSSIBLE_TRANSLATE_LANGS:
                    post_png_file = render_html_to_png(
                        post_id=pid,
                        title=translate_en_to(post["title"], lang),
                        subreddit=translate_en_to(sub_name, lang),
                        subreddit_id=translate_en_to(sub_name, lang),
                        user_id="reddit",
                        user_name=translate_en_to(
                            dirty_remove_cuss(post["author"]), lang
                        ),
                        time_ago=datetime.fromisoformat(
                            post["posted_at"][:-2] + ":" + post["posted_at"][-2:]
                        ),
                        score_int=post["upvotes"],
                        comment_int=post["comments"],
                    )
                    posts_to_use[pid][
                        f"vfile_{lang}"
                    ] = f"tmp/clips/reddit{lang}_{pid}.mp4"
                    end = start + posts_to_use[pid][f"audio_length_{lang}"]
                    create_reddit_video(
                        video_path=os.path.join(REDDIT_TEMPLATE_BG, background),
                        audio_path=posts_to_use[pid][f"filename_{lang}"],
                        output_path=posts_to_use[pid][f"vfile_{lang}"],
                        start_time=start,
                        end_time=end,
                        pid=pid,
                        part_start=posts_to_use[pid][f"part_start_{lang}"],
                        parts=posts_to_use[pid][f"parts_{lang}"],
                        transcript=posts_to_use[pid][f"aligned_ts_{lang}"],
                        tw=1080,
                        th=1920,
                        paragraph=posts_to_use[pid][f"content_{lang}"],
                        post_png_file=post_png_file,
                        title=translate_en_to(
                            swap_words_numbers(
                                reddit_acronym(
                                    reddit_remove_bad_words(posts_to_use[pid]["title"])
                                )
                            ),
                            lang,
                        ),
                    )
        else:
            for pid, post in posts_to_use.items():
                posts_to_use[pid]["vfile"] = f"tmp/clips/reddit_{pid}.mp4"
                posts_to_use[pid]["parts"] = 1
                posts_to_use[pid]["filename"] = f"tmp/audios/{pid}_tts.wav"
                for lang in POSSIBLE_TRANSLATE_LANGS:
                    posts_to_use[pid][
                        f"vfile_{lang}"
                    ] = f"tmp/clips/reddit{lang}_{pid}.mp4"
                    posts_to_use[pid][f"parts_{lang}"] = 1
                    posts_to_use[pid][
                        f"filename_{lang}"
                    ] = f"tmp/audios/{pid}_{lang}_tts.wav"

        ######################################
        # Compile Description
        ######################################
        for pid, post in posts_to_use.items():
            if post.get("parts", 1) > 1:
                posts_to_use[pid]["desc"] = []
                for i in range(post["parts"]):
                    posts_to_use[pid]["desc"].append(
                        f"Part {i+1} |"
                        f" {reddit_remove_bad_words(post['title'])}\n\n#part{i+1} #reddit"
                        " #reddittreadings #reddit_tiktok \n #redditstorytime"
                        " #askreddit #fyp"
                    )
            else:
                posts_to_use[pid]["desc"] = (
                    f"{reddit_remove_bad_words(post['title'])}\n\n#reddit"
                    " #reddittreadings #reddit_tiktok \n #redditstorytime #askreddit"
                    " #fyp"
                )
            for lang in POSSIBLE_TRANSLATE_LANGS:
                if post.get("parts", 1) > 1:
                    posts_to_use[pid][f"desc_{lang}"] = []
                    for i in range(post["parts"]):
                        posts_to_use[pid][f"desc_{lang}"].append(
                            translate_en_to(posts_to_use[pid]["desc"][i], lang)
                        )
                else:
                    posts_to_use[pid][f"desc_{lang}"] = translate_en_to(
                        posts_to_use[pid]["desc"], lang
                    )

        #####################################
        # Upload tiktok
        #####################################
        if not args.skipup:
            for pid, post in posts_to_use.items():
                if not post.get(
                    "sched"
                ):  # or posts_to_use[pid].get("audio_length", 61) < 60:
                    continue
                if not post["sched"] == "now":
                    time_str = post["sched"]
                    today = datetime.today().date()
                    time_obj = datetime.strptime(time_str, "%H:%M").time()
                    scheduled_datetime = datetime.combine(today, time_obj)
                    LOGGER.info(scheduled_datetime)
                    scheduled_datetime = None
                else:
                    scheduled_datetime = "now"
                if post.get("parts", 1) > 1:
                    for i in range(post["parts"]):
                        upload_video_tt(
                            os.path.abspath(
                                post["vfile"].replace(f"{pid}", f"{pid}_p{i}")
                            ),
                            scheduled_datetime,  # +timedelta(minutes=i*5),
                            post["desc"][i],
                            save_draft=False,
                            submit=True,
                            only_me=True,
                        )
                else:
                    upload_video_tt(
                        os.path.abspath(post["vfile"]),
                        scheduled_datetime,
                        post["desc"],
                        save_draft=False,
                        submit=True,
                        only_me=True,
                    )

                update_reddit_post_clip_tt(
                    post_id=pid,
                    tiktok_posted=scheduled_datetime,
                    length=post["audio_length"],
                )
                for lang in POSSIBLE_TRANSLATE_LANGS:
                    if post.get("parts", 1) > 1:
                        for i in range(post["parts"]):
                            upload_video_tt(
                                os.path.abspath(
                                    post[f"vfile_{lang}"].replace(
                                        f"{pid}", f"{pid}_p{i}"
                                    )
                                ),
                                None,  # scheduled_datetime+timedelta(minutes=i*5),
                                post[f"desc_{lang}"][i],
                                save_draft=False,
                                submit=True,
                                only_me=True,
                                lang=lang,
                            )
                    else:
                        upload_video_tt(
                            os.path.abspath(post[f"vfile_{lang}"]),
                            None,  # scheduled_datetime,
                            post[f"desc_{lang}"],
                            save_draft=False,
                            submit=True,
                            only_me=True,
                            lang=lang,
                        )
        else:
            for pid, post in posts_to_use.items():
                if not post.get(
                    "sched"
                ):  # or posts_to_use[pid].get("audio_length", 61) < 60:
                    continue
                if not post["sched"] == "now":
                    time_str = post["sched"]
                    today = datetime.today().date()
                    time_obj = datetime.strptime(time_str, "%H:%M").time()
                    scheduled_datetime = datetime.combine(today, time_obj)
                    LOGGER.info(scheduled_datetime)
                    # scheduled_datetime = None
                else:
                    scheduled_datetime = "now"
                update_reddit_post_clip_tt(
                    post_id=pid,
                    tiktok_posted=scheduled_datetime,
                    length=post["audio_length"],
                )
        #####################################
        # Clean up
        #####################################
        if not args.dryrun:
            for pid, post in posts_to_use.items():
                try:
                    if not post.get(
                        "sched"
                    ):  # or posts_to_use[pid].get("audio_length", 0) < 60:
                        continue
                    if post.get("parts", 1) > 1:
                        for i in range(post["parts"]):
                            shutil.copyfile(
                                post["vfile"].replace(f"{pid}", f"{pid}_p{i}"),
                                f"{CLIPS_FOLDER}/reddit_p_{pid}.mp4",
                            )
                            os.remove(post["vfile"].replace(f"{pid}", f"{pid}_p{i}"))
                            LOGGER.info(
                                "Deleting %s",
                                post["vfile"].replace(f"{pid}", f"{pid}_p{i}"),
                            )
                    else:
                        shutil.copyfile(
                            posts_to_use[pid]["vfile"],
                            f"{CLIPS_FOLDER}/reddit_{pid}.mp4",
                        )
                        os.remove(post["vfile"])
                        LOGGER.info("Deleting %s", post["vfile"])
                    os.remove(post["filename"])
                    LOGGER.info("Deleting %s", post["filename"])
                except Exception as e:
                    LOGGER.error("Error: %s", e)
                for lang in POSSIBLE_TRANSLATE_LANGS:
                    try:
                        if post.get(f"parts_{lang}", 1) > 1:
                            for i in range(post[f"parts_{lang}"]):
                                shutil.copyfile(
                                    post[f"vfile_{lang}"].replace(
                                        f"{pid}", f"{pid}_p{i}"
                                    ),
                                    f"{CLIPS_FOLDER}/reddit{lang}_p{i}_{pid}.mp4",
                                )
                                os.remove(
                                    post[f"vfile_{lang}"].replace(
                                        f"{pid}", f"{pid}_p{i}"
                                    )
                                )
                                LOGGER.info(
                                    "Deleting %s",
                                    post[f"vfile_{lang}"].replace(
                                        f"{pid}", f"{pid}_p{i}"
                                    ),
                                )
                        else:
                            shutil.copyfile(
                                posts_to_use[pid][f"vfile_{lang}"],
                                f"{CLIPS_FOLDER}/reddit{lang}_{pid}.mp4",
                            )
                            os.remove(post[f"vfile_{lang}"])
                            LOGGER.info("Deleting %s", post[f"vfile_{lang}"])
                        os.remove(post[f"filename_{lang}"])
                        LOGGER.info("Deleting %s", post[f"filename_{lang}"])
                    except Exception as e:
                        LOGGER.error("Error: %s", e)
            for file in os.listdir("tmp/audios"):
                os.remove(os.path.join("tmp/audios", file))
            for file in os.listdir("tmp/caps_img"):
                os.remove(os.path.join("tmp/caps_img", file))
        LOGGER.info("Reddit posts done")

        #####################################
        # Stop Scrolling
        #####################################
        if not args.skipscroll and not args.dryrun:
            try:
                LOGGER.info("Stopping Scroll...")

                adb.running = False
                adb.kill_apps()
                adb_thread.join()  # Wait for the thread to finish
            except Exception as e:
                LOGGER.error("Error stopping scroll: %s", e)
            time.sleep(5)

    except Exception as e:
        LOGGER.error("Fail in main: %s", e)
        adb_thread.join()
        adb.running = False
        adb.kill_apps()


if __name__ == "__main__":
    main_reddit_posts_orch()
