import argparse
import json
import logging
import os
import shutil
import uuid
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from random import choice, randint

from urlextract import URLExtract
import torch
from num2words import num2words
from tqdm import tqdm

from clip_creator.conf import (
    CLIPS_FOLDER,
    LOGGER,
    POSSIBLE_TRANSLATE_LANGS,
    POSSIBLE_TRANSLATE_LANGS_TTS,
    RED_COM_DELAY,
    REDDIT_TEMPLATE_BG,
    TMP_CLIPS_FOLDER,
)
from clip_creator.db.db import (
    add_reddit_post_clip_com,
    create_database,
    get_all_post_ids_red_com,
    get_reddit_post_clip_by_id_com,
    get_rows_where_tiktok_null_or_empty_com,
    update_reddit_post_clip_at_com,
    update_reddit_post_clip_tt_com,
    updatey_reddit_post_clip_com,
)
from clip_creator.lang.translate import translate_en_to
from clip_creator.social.reddit import (
    find_sub_reddit_coms,
    find_top_sub_reddit_coms,
    reddit_coms_orch,
    straight_update_reddit_coms,
)
from clip_creator.tts.ai import TTSModelKokoro
from clip_creator.utils.caption_img import (
    render_html_to_png,
    render_html_to_png_comment,
)
from clip_creator.utils.forcealign import force_align
from clip_creator.utils.math_things import get_88_percentile, start_times_per_chunk
from clip_creator.utils.path_setup import check_and_create_dirs
from clip_creator.utils.scan_text import (
    dirty_remove_cuss,
    get_id_from_vfile,
    get_top_posts_coms,
    reddit_acronym,
    reddit_remove_bad_words,
    remove_non_letters,
    sort_and_loop_by_max_int_key_coms,
    str_to_datetime,
    swap_words_numbers,
    get_correct_chunk_end,
    remove_markdown_links_images
)
from clip_creator.utils.schedules import none_old_timestamps_com
from clip_creator.vid_ed.red_vid_edit import (
    create_reddit_video_com,
    get_audio_duration,
    get_clip_duration,
)


def main_reddit_coms_orch():
    parser = argparse.ArgumentParser(description="AI Clip Creator")
    parser.add_argument(
        "--noretrieve",
        action="store_true",
        help="Retrieve new videos from YouTube if not set",
    )
    parser.add_argument(
        "--dryrun",
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
        "--doupdate",
        action="store_true",
        help="overrides noretrieve for updating if set",
    )
    parser.add_argument(
        "--fetchonly",
        action="store_true",
        help="exits after fetching new data if set",
    )
    args = parser.parse_args()
    LOGGER.info("Arguments: %s", args)
    #####################################
    # Set up paths
    #####################################

    check_and_create_dirs()
    #####################################
    # Setup logging
    #####################################
    dt = datetime.now()
    log_file = f"logs/reddit_coms_orch_{dt.strftime('%Y-%m-%d_%H-%M-%S')}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    )
    LOGGER.addHandler(file_handler)
    #####################################
    # Create database
    #####################################
    create_database()
    LOGGER.info("Database created")
    if not args.noretrieve:
        found_posts = get_all_post_ids_red_com()
        
        LOGGER.info("Found posts: %s", len(found_posts))
        
        top_list = find_top_sub_reddit_coms(found_posts, min_posts=5)
        LOGGER.info("Found top hrefs: %s", len(top_list))
        
        href_list = find_sub_reddit_coms(found_posts, min_posts=10)
        LOGGER.info("Found hrefs: %s", len(href_list))
        
        href_list.extend(top_list)

        netw_redd_posts = reddit_coms_orch(
            href_list, found_posts, min_post=10, max_post=20
        )
        LOGGER.info("Found posts: %s", len(netw_redd_posts))

        #####################################
        # Add posts to database
        #####################################
        for post in netw_redd_posts:
            if post["url"] is None:
                continue
            if "/" in post["url"]:
                if post["url"].split("/")[3] in found_posts:
                    LOGGER.error(
                        f"ITEM ADDED FROM POSTS IS ALREADY IN DB: {post['url']}"
                    )
                else:
                    LOGGER.info(f"Adding post to DB: {post['url']}")
                    add_reddit_post_clip_com(
                        post_id=post["post_id"],
                        title=post["title"],
                        posted_at=post["posted_at"],
                        content=post["content"],
                        url=post["url"],
                        upvotes=post["upvotes"],
                        comments=post["comments"],
                        nsfw=post["nsfw"],
                        author=post["author"],
                        comments_json=post[
                            "comments_list"
                        ],  # a list[dict] of comments where dict is {author, text, score}
                        updated_at=datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f+0000"),
                    )

            else:
                LOGGER.error(f"Invalid URL: {post['url']}")

    #####################################
    # Remove from list if 160 words not met
    #####################################
    unused_posts = get_rows_where_tiktok_null_or_empty_com()
    posts_to_use = {}
    with open("clip_creator/utils/banned.txt") as f:
        banned_words = f.read().split(",")
        for post in unused_posts:
            banned_q = False
            if not post["nsfw"]:  # if not nsfw
                for word in banned_words:
                    if word in post["title"] or word in post["content"]:
                        LOGGER.info("Post %s has banned word %s", post["post_id"], word)
                        banned_q = True
                        break
                if "reddit" in post['title'].lower():
                    banned_q = True
                if not banned_q:
                    posts_to_use[post["post_id"]] = post
    #####################################
    # remove urls from content
    #####################################
    url_finder = URLExtract()
    if not args.usevids:
        for pid, post in posts_to_use.items():
            if url_finder.has_urls(post.get("content", "")):
                found_urls:list[str] = url_finder.find_urls(post["content"])
                for url in found_urls:
                    post["content"] = post.get("content", "").replace(url, "")
                    # detect if its an image
    #####################################
    # possibly update database
    #####################################
    href_list = []
    if (
        (args.noretrieve and args.doupdate)
        or (not args.noretrieve and not args.doupdate and False)
    ) and not args.usevids:
        for pid, post in posts_to_use.items():
            if post.get("updated_at") is not None and post.get("updated_at") != "":
                post_dt = str_to_datetime(post.get("updated_at", ""))
            else:
                post_dt = str_to_datetime(post.get("posted_at", ""))
            LOGGER.debug("Post dt: %s", post_dt)
            if (datetime.now(UTC) - post_dt) > timedelta(days=4):
                posty = straight_update_reddit_coms(post.get("url", ""))
                LOGGER.debug("Posty: %s", posty)
                if posty.get("title"):
                    LOGGER.debug("Updating Post %s", posty["url"])
                    updatey_reddit_post_clip_com(
                        post_id=post["post_id"],
                        title=post["title"],
                        posted_at=post["posted_at"],
                        content=post["content"],
                        url=post["url"],
                        upvotes=post["upvotes"],
                        comments=post["comments"],
                        nsfw=post["nsfw"],
                        author=post["author"],
                        comments_json=post[
                            "comments_list"
                        ],  # a list[dict] of comments where dict is {author, text, score}
                        updated_at=datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f+0000"),
                    )
    #####################################
    # Exit if fetch only
    #####################################
    if args.fetchonly:
        LOGGER.info("Fetch only, exiting")
        return
    #####################################
    # Compile script
    #####################################
    posts_to_rm = []
    for pid, post in posts_to_use.items():
        # Get Number of words
        total_words = len(post["title"].split()) + (len(post["content"].split()) if "?" not in post["title"] else 0)

        posts_to_use[pid]["comments_json"] = json.loads(post["comments_json"])
        if not posts_to_use[pid]["comments_json"]:
            posts_to_rm.append(pid)
            continue
        ht_text = remove_non_letters(
            swap_words_numbers(reddit_acronym(reddit_remove_bad_words(post["title"]+ ("\n" + post["content"] if "?" not in post["title"] else ""))))
        )
        posts_to_use[pid]["chunks"] = {str(uuid.uuid4()): {"idx": 0, "text": ht_text}}
        posts_to_use[pid]["comments_json"] = sort_and_loop_by_max_int_key_coms(
            posts_to_use[pid]["comments_json"]
        )  # sort by score
        comments_above, comments_above_rpl = get_88_percentile(
            posts_to_use[pid]["comments_json"]
        )

        posts_to_use[pid]["comments_above_rpl"] = comments_above_rpl
        posts_to_use[pid]["comments_above"] = comments_above

        posts_to_use[pid]["comments_json"].sort(
            key=lambda comment: comment.get("upvotes", 0), reverse=True
        )
        for idx, comment in enumerate(posts_to_use[pid]["comments_json"]):
            
            with open("clip_creator/utils/banned.txt") as f:
                banned_words = f.read().split(",")
                banned_q = False
                for word in banned_words:
                    if word in comment["content"] or word in comment["best_reply"].get(
                        "content", ""
                    ):
                        LOGGER.info(
                            "Comment %s has banned word %s", str(comment["content"]).encode("ASCII", "ignore").decode("ASCII"), word
                        )
                        banned_q = True
                        break
                if banned_q:
                    continue
            # TODO: Modify to save the og comment to map to the captions like numbers
            tt_text = ("\n"
                            + num2words(idx + 1)
                            + ".\n\n\n"
                            + comment["content"]
                            + ".\n"
                            + (
                                (comment["best_reply"].get("content", "") + ".")
                                if comment["best_reply"].get("upvotes", 0)
                                > comments_above_rpl
                                else ""
                            )
                            )
            if url_finder.has_urls(tt_text):
                found_urls:list[str] = url_finder.find_urls(tt_text)
                for url in found_urls:
                    tt_text = tt_text.replace(url, "")
            tt_text = remove_non_letters(
                swap_words_numbers(
                    reddit_acronym(
                        reddit_remove_bad_words(
                            remove_markdown_links_images(
                            tt_text
                            )
                        )
                    )
                )
            )
            
            total_words += len(tt_text.split())
            posts_to_use[pid]["chunks"][str(uuid.uuid4())] = {
                "idx": idx + 1,
                "text": tt_text,
                "reply": (
                    True
                    if comment["best_reply"].get("upvotes", 0) > comments_above_rpl
                    else False
                ),
                "com_json": comment,
            }
            if total_words > 450:
                LOGGER.debug("Post %s has more than 450 words", pid)
                break
            if idx >= 20:
                break
        if total_words < 160:
            LOGGER.debug("Post %s has less than 160 words", pid)
            posts_to_rm.append(pid)
        else:
            LOGGER.info("Post %s has %s words", pid, total_words)
    for pid in posts_to_rm:
        posts_to_use.pop(pid)

    ########################################
    # Calc time to post
    ########################################

    day_sched = none_old_timestamps_com()
    LOGGER.info("Day Sched: %s", day_sched)

    # rand_posts = sample(list(posts_to_use.keys()), len(day_sched))
    if not args.usevids:
        best_posts = get_top_posts_coms(posts_to_use, len(day_sched))

    else:
        LOGGER.info("Using created videos")
        best_posts = []
        for file in os.listdir(TMP_CLIPS_FOLDER):
            pid_tmp = get_id_from_vfile(file)
            if pid_tmp:
                posts_to_use[pid_tmp] = get_reddit_post_clip_by_id_com(pid_tmp)
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
        posts_to_keep[pid]["sched"] = (
            datetime.today()
            .replace(
                hour=int(day_sched[i].split(":")[0]),
                minute=int(day_sched[i].split(":")[1]),
                second=0,
                microsecond=0,
            )
            .isoformat()
        )
        LOGGER.info("Post sched %s, %s", pid, posts_to_keep[pid]["sched"])

    posts_to_use = posts_to_keep
    #####################################
    # Translate to other languages
    #####################################
    if not args.usevids:
        for pid, post in posts_to_use.items():
            for lang in POSSIBLE_TRANSLATE_LANGS:
                posts_to_use[pid][f"chunks_{lang}"] = deepcopy(
                    posts_to_use[pid]["chunks"]
                )
                for uid, chunk in tqdm(
                    post[f"chunks_{lang}"].items(),
                    desc=f"Translating chunks to {lang} for post {pid}",
                ):
                    LOGGER.debug("Translating %s:%s to %s", pid, uid, lang)
                    posts_to_use[pid][f"chunks_{lang}"][uid]["text"] = translate_en_to(
                        posts_to_use[pid][f"chunks_{lang}"][uid]["text"], lang
                    )
    #####################################
    # Create Audio using TTS
    #####################################

    if not args.usevids:
        tts_model = TTSModelKokoro()
        for pid, post in posts_to_use.items():
            posts_to_use[pid]["audio_length"] = 0

            for uid, chunk in tqdm(
                post["chunks"].items(), "creating audio for post %s" % pid
            ):
                LOGGER.debug("Creating Audio for %s:%s", pid, uid)
                posts_to_use[pid]["chunks"][uid][
                    "auFile"
                ] = f"tmp/audios/{pid}_{uid}.wav"
                if not os.path.exists(f"tmp/audios/{pid}_{uid}.wav"):
                    tts_model.run_it(
                        posts_to_use[pid]["chunks"][uid]["auFile"], chunk["text"]
                    )
                posts_to_use[pid]["chunks"][uid]["audio_length"] = get_audio_duration(
                    posts_to_use[pid]["chunks"][uid]["auFile"]
                )
                posts_to_use[pid]["audio_length"] += (
                    get_audio_duration(posts_to_use[pid]["chunks"][uid]["auFile"])
                    + RED_COM_DELAY
                )
            
        # Create Audio for other languages

        for lang in POSSIBLE_TRANSLATE_LANGS:
            tts_model_lang = TTSModelKokoro(
                voice=choice(POSSIBLE_TRANSLATE_LANGS_TTS[lang]["tts"]),
                lang_code=POSSIBLE_TRANSLATE_LANGS_TTS[lang][lang],
            )
            for pid, post in posts_to_use.items():
                posts_to_use[pid][f"audio_length_{lang}"] = 0
                LOGGER.debug("Creating Audio for %s", pid)
                for uid, chunk in tqdm(
                    post[f"chunks_{lang}"].items(),
                    desc=f"Creating audio for {pid} lang:{lang}",
                ):
                    posts_to_use[pid][f"chunks_{lang}"][uid][
                        "auFile"
                    ] = f"tmp/audios/{pid}_{lang}_{uid}.wav"
                    if not os.path.exists(
                        posts_to_use[pid][f"chunks_{lang}"][uid]["auFile"]
                    ):
                        tts_model_lang.run_it(
                            posts_to_use[pid][f"chunks_{lang}"][uid]["auFile"],
                            chunk["text"],
                        )
                    posts_to_use[pid][f"audio_length_{lang}"] += (
                        get_audio_duration(
                            posts_to_use[pid][f"chunks_{lang}"][uid]["auFile"]
                        )
                        + RED_COM_DELAY
                    )
                    posts_to_use[pid][f"chunks_{lang}"][uid]["audio_length"] = (
                        get_audio_duration(
                            posts_to_use[pid][f"chunks_{lang}"][uid]["auFile"]
                        )
                    )

    #####################################
    # Force align text to audio
    #####################################
    device = "cpu"
    if torch.cuda.is_available():
        device = "cuda:0"
        torch.cuda.empty_cache()

    for pid, post in posts_to_use.items():
        script = []
        for uid, chunk in tqdm(post["chunks"].items(), desc=f"Force aligning {pid}"):
            posts_to_use[pid]["chunks"][uid]["ascript"] = force_align(
                device=device, file=chunk["auFile"], yt_ft_transcript=chunk["text"]
            )
            script.extend(posts_to_use[pid]["chunks"][uid]["ascript"])
        update_reddit_post_clip_at_com(post_id=pid, transcript=json.dumps(script))
    for lang in POSSIBLE_TRANSLATE_LANGS:
        for pid, post in posts_to_use.items():
            for uid, chunk in tqdm(
                post[f"chunks_{lang}"].items(), desc=f"Force aligning {pid} lang-{lang}"
            ):
                posts_to_use[pid][f"chunks_{lang}"][uid]["ascript"] = force_align(
                    device=device, file=chunk["auFile"], yt_ft_transcript=chunk["text"]
                )
    #####################################
    # Math the start
    #####################################
    for pid, post in posts_to_use.items():
        posts_to_use[pid]["chunks"] = start_times_per_chunk(post["chunks"])
        for lang in POSSIBLE_TRANSLATE_LANGS:
            posts_to_use[pid][f"chunks_{lang}"] = start_times_per_chunk(
                post[f"chunks_{lang}"]
            )
    #####################################
    # Create video
    #####################################
    if not args.usevids:
        mpfours = [
            file for file in os.listdir(REDDIT_TEMPLATE_BG) if file.endswith(".mp4")
        ]
        for pid, post in posts_to_use.items():
            LOGGER.info("Post: %s", pid)
            if not post.get("sched"):
                continue
            sub_name = post["url"].split("/")[2]
            do_it = False
            last_part = ""
            for part_url in post["url"].split("/"):
                if "r" == part_url.lower():
                    do_it = True
                elif do_it:
                    sub_name = part_url
                    break
                elif "comment" in part_url:
                    sub_name = last_part
                    break
                last_part = part_url
            LOGGER.info("Subreddit: %s", sub_name)
            # Create img for post
            same_idx = 0
            for uid, chunk in post["chunks"].items():
                if same_idx > 1:
                    LOGGER.error("More than 1 same idx")
                    raise Exception("More than 1 same idx")
                if chunk.get("idx") == 0:
                    same_idx += 1
                    chunk["img"] = render_html_to_png(
                        post_id=pid,
                        title=chunk["text"],
                        subreddit=sub_name,
                        subreddit_id=sub_name,
                        user_id="reddit",
                        user_name=dirty_remove_cuss(post.get("author", "Unknown")),
                        time_ago=datetime.fromisoformat(
                            post["posted_at"][:-2] + ":" + post["posted_at"][-2:]
                        ),
                        score_int=post["upvotes"],
                        comment_int=post["comments"],
                    )
                # else:
                #     chunk["img"]:list = render_html_to_png_comment(
                #         post_id=pid,
                #         comt_above=post["comments_above"],
                #         chunk=chunk,
                #         chunk_id=uid,
                #         comment_json=chunk["com_json"],
                #         reply=chunk.get("reply", False),
                #     )
                posts_to_use[pid]["chunks"][uid] = chunk
            LOGGER.info("Finished creating images")
            background = choice(mpfours)
            clip_length = get_clip_duration(
                os.path.join(REDDIT_TEMPLATE_BG, background)
            )
            LOGGER.info("Clip, length, pid: %s, %s, %s", background, clip_length, pid)
            # Grab random part from mc parkor/subway surfers/temple run
            start = randint(0, int(clip_length - posts_to_use[pid]["audio_length"] + 1))
            end = start + posts_to_use[pid]["audio_length"]
            # run video creator that combines video with audio with transcript
            posts_to_use[pid]["vfile"] = f"tmp/clips/reddit_{pid}.mp4"
            LOGGER.info("Creating video for %s", pid)
            create_reddit_video_com(
                video_path=os.path.join(REDDIT_TEMPLATE_BG, background),
                output_path=posts_to_use[pid]["vfile"],
                start_time=start,
                end_time=end,
                pid=pid,
                tw=1080,
                th=1920,
                chunks=posts_to_use[pid]["chunks"],
            )
            if not os.path.exists(posts_to_use[pid]["vfile"]):
                LOGGER.error("Video not created %s", posts_to_use[pid]["vfile"])
                continue
            update_reddit_post_clip_tt_com(
                post_id=pid,
                tiktok_posted=post["sched"],
                length=posts_to_use[pid]["audio_length"],
            )
            for lang in POSSIBLE_TRANSLATE_LANGS:
                for uid, chunk in post[f"chunks_{lang}"].items():
                    if chunk.get("idx") == 0:
                        posts_to_use[pid][f"chunks_{lang}"][uid]["img"] = (
                            render_html_to_png(
                                post_id=pid,
                                lang=lang,
                                title=chunk["text"],
                                subreddit=sub_name,
                                subreddit_id=sub_name,
                                user_id="reddit",
                                user_name=dirty_remove_cuss(post["author"]),
                                time_ago=datetime.fromisoformat(
                                    post["posted_at"][:-2]
                                    + ":"
                                    + post["posted_at"][-2:]
                                ),
                                score_int=post["upvotes"],
                                comment_int=post["comments"],
                            )
                        )
                    # else:
                    #     posts_to_use[pid][f"chunks_{lang}"][uid]["img"]:list = (
                    #         render_html_to_png_comment(
                    #             post_id=pid,
                    #             comt_above=post["comments_above"],
                    #             chunk=chunk,
                    #             chunk_id=uid,
                    #             comment_json=chunk["com_json"],
                    #             reply=chunk.get("reply", False),
                    #         )
                    #     )
                posts_to_use[pid][f"vfile_{lang}"] = f"tmp/clips/reddit{lang}_{pid}.mp4"
                end = start + posts_to_use[pid][f"audio_length_{lang}"]
                create_reddit_video_com(
                    video_path=os.path.join(REDDIT_TEMPLATE_BG, background),
                    output_path=posts_to_use[pid][f"vfile_{lang}"],
                    start_time=start,
                    end_time=end,
                    pid=pid,
                    tw=1080,
                    th=1920,
                    chunks=posts_to_use[pid][f"chunks_{lang}"],
                )
    else:
        for pid, post in posts_to_use.items():
            posts_to_use[pid]["vfile"] = f"tmp/clips/reddit_{pid}.mp4"
            posts_to_use[pid]["parts"] = 1
            posts_to_use[pid]["filename"] = f"tmp/audios/{pid}_tts.wav"
            for lang in POSSIBLE_TRANSLATE_LANGS:
                posts_to_use[pid][f"vfile_{lang}"] = f"tmp/clips/reddit{lang}_{pid}.mp4"
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
                    " #reddittreadings #reddit_tiktok \n #redditstorytime #askreddit"
                    " #fyp"
                )
        else:
            posts_to_use[pid]["desc"] = (
                f"{reddit_remove_bad_words(post['title'])}\n\n#reddit #reddittreadings"
                " #reddit_tiktok \n #redditstorytime #askreddit #fyp"
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
    # Clean up
    #####################################
    for pid, post in posts_to_use.items():
        shutil.copyfile(post["vfile"], f"{CLIPS_FOLDER}/reddit_{pid}.mp4")
        os.remove(post["vfile"])
        for uid, chunk in post["chunks"].items():
            os.remove(chunk["auFile"])

        for lang in POSSIBLE_TRANSLATE_LANGS:
            shutil.copyfile(
                post[f"vfile_{lang}"], f"{CLIPS_FOLDER}/reddit{lang}_{pid}.mp4"
            )
            os.remove(post[f"vfile_{lang}"])
            for uid, chunk in post[f"chunks_{lang}"].items():
                os.remove(chunk["auFile"])


    LOGGER.info("Reddit posts done")


if __name__ == "__main__":
    main_reddit_coms_orch()
