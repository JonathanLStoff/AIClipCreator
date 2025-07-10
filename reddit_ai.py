import argparse
import json
import logging
import os
import shutil
import math
import time
import uuid
import traceback
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from random import choice, randint

import torch
from num2words import num2words
from tqdm import tqdm
from clip_creator.youtube import (
    get_transcript,
    get_video_info,
)
from clip_creator.conf import (
    CLIPS_FOLDER,
    LOGGER,
    POSSIBLE_TRANSLATE_LANGS,
    POSSIBLE_TRANSLATE_LANGS_TTS,
    RED_COM_DELAY,
    REDDIT_TEMPLATE_BG,
    TMP_CLIPS_FOLDER,
    CHANNELS_AI_REDDIT
)
from clip_creator.db.db import (
    add_reddit_post_clip_com,
    create_database,
    get_reddit_post_clip_by_id_com,
    update_reddit_post_clip_tt_com,
    updatey_reddit_post_clip_com,
    get_all_aiyt_clips,
    get_no_uploaded_aiyt_clips,
    add_reddit_post_clip_ai,
    update_reddit_post_clip_aiyt,
    update_reddit_post_clip_tt_aiyt
)
from clip_creator.youtube import (
    get_latest_videos_v2
)
from clip_creator.lang.translate import translate_en_to

from clip_creator.tts.ai import TTSModelKokoro
from clip_creator.utils.caption_img import (
    render_html_to_png,
)
from clip_creator.utils.forcealign import force_align_aiyt
from clip_creator.utils.math_things import get_88_percentile, start_times_per_chunk
from clip_creator.utils.path_setup import check_and_create_dirs
from clip_creator.utils.scan_text import (
    dirty_remove_cuss,
    get_id_from_vfile,
    get_top_posts_aiyt,
    reddit_acronym,
    reddit_remove_bad_words,
    remove_non_letters,
    sort_and_loop_by_max_int_key_coms,
    str_to_datetime,
    swap_words_numbers,
    get_correct_chunk_end,
    remove_markdown_links_images
)
from clip_creator.utils.schedules import none_old_timestamps_aiyt
from clip_creator.vid_ed.red_vid_edit import (
    create_reddit_video_aiyt,
    get_audio_duration,
    get_clip_duration,
)
from clip_creator.tts.audio_edit import (
    find_splits_each_trans,
    combine_audio_files
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
        found_videos = get_all_aiyt_clips()
        
        LOGGER.info("Found posts: %s", len(found_videos.keys()))
        for _, id_c in CHANNELS_AI_REDDIT.items():
            
            found_videos = get_latest_videos_v2(id_c, found_videos)
        
        transcripts_and_data = {}
        for vid, v_data in found_videos.items():
            
            if v_data.get("not_in_db"):
                vid_info_tmp = get_video_info(vid)
                transcripts_and_data[vid] = {
                    "yttranscript": get_transcript(vid),
                    "likes": vid_info_tmp.get("likes", 0),
                    "views": vid_info_tmp.get("views", 0),
                    }
        for vid, tran_data in transcripts_and_data.items():
            if not tran_data["yttranscript"]:
                LOGGER.error("No transcript for %s", vid)
                continue
            if not tran_data["likes"] or not tran_data["views"]:
                LOGGER.error("No likes or views for %s", vid)
                continue
            found_videos[vid]["yttranscript"] = tran_data["yttranscript"]
            found_videos[vid]["likes"] = tran_data["likes"]
            found_videos[vid]["views"] = tran_data["views"]
                
    #####################################
    # Add posts to database
    #####################################
    if not args.noretrieve:
        for vid, v_data in found_videos.items():
                
            if v_data.get("not_in_db"):
                
                LOGGER.info(f"Adding post to DB: {vid}")
                add_reddit_post_clip_ai(
                    vid_id=vid,
                    title=v_data["title"].replace("FULL STORY", "").strip(),
                    posted_at=v_data["posted_at"],
                    descr=v_data["description"],
                    likes=v_data["likes"],
                    views=v_data["views"],
                    nsfw=v_data.get("nsfw"),
                    author=v_data["author"],
                    yttranscript=v_data["yttranscript"],
                    updated_at=datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f+0000"),
                )
            else:
                LOGGER.error(f"Invalid URL: {vid}")
    #####################################
    # get the current list of vids that dont have created clips
    #####################################
    unused_posts = get_no_uploaded_aiyt_clips()
    posts_to_use = {}
    with open("clip_creator/utils/banned.txt") as f:
        banned_words = f.read().split(",")
        for pid, post in unused_posts.items():
            post['content'] = ""
            for section in post['yttranscript']:
                post['content'] += section.get("text", "").strip() + " "
            banned_q = False
            if not post["nsfw"]:  # if not nsfw
                for word in banned_words:
                    if word.strip() == "" or word.strip() == " ":
                        continue
                    if word in post["title"] or word in post["content"]:
                        LOGGER.info("Post %s has banned word %s", pid, word)
                        banned_q = True
                        break
                if (post['yttranscript'][-1].get("start", 0)) < 300: #5 min minium
                    LOGGER.info("Post %s has less than 5 minutes of content, removing", pid)
                    banned_q = True
                if not banned_q:
                    # TODO: Create a function that has more robust checks for the title
                    post['title'] = post['title'].replace("FULL STORY", "").strip()
                    posts_to_use[pid] = post
    
    #####################################
    # Exit if fetch only
    #####################################
    if args.fetchonly:
        LOGGER.info("Fetch only, exiting")
        return
    

    ########################################
    # Calc time to post
    ########################################

    day_sched = none_old_timestamps_aiyt()
    LOGGER.info("Day Sched: %s", day_sched)

    # rand_posts = sample(list(posts_to_use.keys()), len(day_sched))
    if not args.usevids:
        best_posts = get_top_posts_aiyt(posts_to_use, len(day_sched))
        LOGGER.info("Best posts: %s", len(best_posts))

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
    # Compile script
    #####################################
    new_content = {}
    for pid, post in posts_to_use.items():
        # Get Number of words
        
        posts_to_use[pid]['yttranscript_chunks'] = find_splits_each_trans(post['yttranscript'], length=2)
        
        post['content'] = [remove_non_letters(
                swap_words_numbers(
                    reddit_acronym(
                        reddit_remove_bad_words(post["title"])
                        )
                    )
            )]
        for chunk in posts_to_use[pid]['yttranscript_chunks']:
            tmp_chunk_data = ""
            for section in chunk:
                tmp_chunk_data += section.get("text", "").strip() + " "
            

            ht_text = remove_non_letters(
                swap_words_numbers(
                    reddit_acronym(
                        reddit_remove_bad_words(tmp_chunk_data)
                        )
                    )
            )
            post['content'].append(ht_text)
        new_content[pid] = post['content']
    for pid, content in new_content.items():
        posts_to_use[pid]["content"] = content
        LOGGER.info("Post %s content chunk num: %s", pid, len(posts_to_use[pid]["content"]))
    #####################################
    # Translate to other languages
    #####################################
    if not args.usevids:
        for pid, post in posts_to_use.items():
            for lang in POSSIBLE_TRANSLATE_LANGS:
                posts_to_use[pid][f"content_{lang}"] = []
                LOGGER.info("Translating %s to %s", content, lang)
                for content in post["content"]:
                    
                    try:
                        posts_to_use[pid][f"content_{lang}"].append(translate_en_to(deepcopy(
                            content
                        ),lang))
                    except Exception as e:
                        LOGGER.error("Error translating %s to %s: %s", content, lang, e)
                        time.sleep(20)
                    time.sleep(1)

    #####################################
    # Create Audio using TTS
    #####################################

    if not args.usevids:
        
        LOGGER.info("Creating audio using TTS")
        LOGGER.info("There are %s posts to use", len(posts_to_use.keys()))
        for pid, post in posts_to_use.items():
            posts_to_use[pid]["auFile"] = [] #f"tmp/audios/{pid}.wav"
            posts_to_use[pid]["audio_length"] = 0
            LOGGER.info("Creating audio for script starting with %s ....", posts_to_use[pid]["content"][0])
            tts_model = TTSModelKokoro()
            for i, content in enumerate(posts_to_use[pid]["content"]):
                
                posts_to_use[pid]["auFile"].append(f"tmp/audios/{pid}_{i}.wav")
                if not os.path.exists(posts_to_use[pid]["auFile"][-1]):
                    LOGGER.info("Creating audio file %s", posts_to_use[pid]["auFile"][-1])
                    tts_model.run_it(
                        posts_to_use[pid]["auFile"][-1], content
                    )
                else:
                    LOGGER.info("Audio file %s already exists, skipping TTS", posts_to_use[pid]["auFile"][-1])
                posts_to_use[pid]["audio_length"] += get_audio_duration(
                    posts_to_use[pid]["auFile"][-1]
                )
                if i == 0:
                    posts_to_use[pid]["audio_length_title"] = get_audio_duration(
                        posts_to_use[pid]["auFile"][-1]
                    )
            tts_model.stop()
            del tts_model
        # Create Audio for other languages

        for lang in POSSIBLE_TRANSLATE_LANGS:
            for pid, post in posts_to_use.items():
                posts_to_use[pid][f"auFile_{lang}"] = [] #f"tmp/audios/{pid}.wav"
                posts_to_use[pid][f"audio_length_{lang}"] = 0
                LOGGER.info("Creating audio for script starting with %s ....", posts_to_use[pid][f"content_{lang}"][0])
                for i, content in enumerate(posts_to_use[pid][f"content_{lang}"]):
                    tts_model_lang = TTSModelKokoro(
                        voice=choice(POSSIBLE_TRANSLATE_LANGS_TTS[lang]["tts"]),
                        lang_code=POSSIBLE_TRANSLATE_LANGS_TTS[lang][lang],
                    )
                    posts_to_use[pid][f"auFile_{lang}"].append(f"tmp/audios/{pid}_{i}_{lang}.wav")
                    if not os.path.exists(posts_to_use[pid][f"auFile_{lang}"][-1]):

                        tts_model_lang.run_it(
                            posts_to_use[pid][f"auFile_{lang}"][-1], content
                        )
                    else:
                        LOGGER.info("Audio file %s already exists, skipping TTS", posts_to_use[pid][f"auFile_{lang}"][-1])
                    if i == 0:
                        posts_to_use[pid][f"audio_length_title_{lang}"] = get_audio_duration(
                                                posts_to_use[pid][f"auFile_{lang}"][-1]
                                            )
                    posts_to_use[pid][f"audio_length_{lang}"] += get_audio_duration(
                        posts_to_use[pid][f"auFile_{lang}"][-1]
                    )
                    tts_model_lang.stop()
                    del tts_model_lang
            

    #####################################
    # Force align text to audio
    #####################################
    
    
    for pid, post in posts_to_use.items():
        device = "cpu"
        if torch.cuda.is_available():
            device = "cuda"
            torch.cuda.empty_cache()
            time.sleep(2)
        LOGGER.info("Using device: %s", device)
        try:
            posts_to_use[pid]["mytranscript"] = force_align_aiyt(
                device=device, file=post["auFile"], yt_ft_transcript=post["content"]
            )
        except Exception as e:
            LOGGER.error("Error in force_align for %s: %s", pid, traceback.format_exc())
            if "CUDA out of memory" in str(e):
                LOGGER.error("Out of memory error, trying to free up memory")
                torch.cuda.empty_cache()
                time.sleep(2)
                device = "cpu"
                posts_to_use[pid]["mytranscript"] = force_align_aiyt(
                    device=device, file=post["auFile"], yt_ft_transcript=post["content"]
                )
        if isinstance(posts_to_use[pid]["mytranscript"], str):
            posts_to_use[pid]["mytranscript"] = json.loads(posts_to_use[pid]["mytranscript"])
        if posts_to_use[pid]["audio_length"]/60 > 9: # check if audio is longer than 9 minutes
            posts_to_use[pid]["parts"] = math.ceil((posts_to_use[pid]["audio_length"]/60)/9) # 9 minutes per part max but will split the time into equal parts
        else:
            posts_to_use[pid]["parts"] = 1
        update_reddit_post_clip_aiyt(
            post_id=pid,
            transcript=json.dumps(posts_to_use[pid]["mytranscript"]), 
            length=posts_to_use[pid]["audio_length"],
            parts=posts_to_use[pid]["parts"]
            )
    for lang in POSSIBLE_TRANSLATE_LANGS:
        for pid, post in posts_to_use.items():
            if torch.cuda.is_available():
                device = "cuda"
                torch.cuda.empty_cache()
                time.sleep(2)
            LOGGER.info("Using device: %s", device)
            try:
                posts_to_use[pid][f"mytranscript_{lang}"] = force_align_aiyt(
                    device=device, file=post[f"auFile_{lang}"], yt_ft_transcript=post[f"content_{lang}"]
                )
            except Exception as e:
                LOGGER.error("Error in force_align for %s: %s", pid, traceback.format_exc())
                if "CUDA out of memory" in str(e):
                    LOGGER.error("Out of memory error, trying to free up memory")
                    torch.cuda.empty_cache()
                    time.sleep(2)
                    device = "cpu"
                    posts_to_use[pid][f"mytranscript_{lang}"] = force_align_aiyt(
                        device=device, file=post[f"auFile_{lang}"], yt_ft_transcript=post[f"content_{lang}"]
                    )
            if isinstance(posts_to_use[pid].get(f"mytranscript_{lang}"), str):
                posts_to_use[pid][f"mytranscript_{lang}"] = json.loads(posts_to_use[pid][f"mytranscript_{lang}"])
    #####################################
    # Combine Audio files
    #####################################
    for pid, post in posts_to_use.items():
        combine_audio_files(
            audio_files=post["auFile"],
            output_file=f"tmp/audios/combined_{pid}.wav"
        )
        posts_to_use[pid]["auFile"] = f"tmp/audios/combined_{pid}.wav"
        posts_to_use[pid]["audio_length"] = get_audio_duration(posts_to_use[pid]["auFile"])
        for lang in POSSIBLE_TRANSLATE_LANGS:
            combine_audio_files(
                audio_files=post[f"auFile_{lang}"],
                output_file=f"tmp/audios/combined_{pid}_{lang}.wav"
            )
            posts_to_use[pid][f"auFile_{lang}"] = f"tmp/audios/combined_{pid}_{lang}.wav"
            posts_to_use[pid][f"audio_length_{lang}"] = get_audio_duration(posts_to_use[pid][f"auFile_{lang}"])


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
            
                
            sub_name = "r/RedditCity"
            LOGGER.info("Subreddit: %s", sub_name)
            for part_num in range(int(post["parts"])):
                # Create img for post
                LOGGER.info("Creating image for post %s, part %s", pid, part_num)
                image_file = render_html_to_png(
                        post_id=pid,
                        title=posts_to_use[pid]["title"] + ("Part " + str(part_num) if part_num >= 1 else ""),
                        subreddit=sub_name,
                        subreddit_id=sub_name,
                        user_id="reddit",
                        user_name=dirty_remove_cuss(post.get("author", "Unknown")),
                        time_ago=datetime.fromisoformat(
                            post["posted_at"].replace('Z', '+00:00')
                        ),
                        score_int=post["views"],
                        comment_int=post["likes"],
                    )
                part_start_tmp = (posts_to_use[pid]["audio_length"]/post["parts"]) * part_num
                part_end_tmp = (((posts_to_use[pid]["audio_length"]/post["parts"]) * (part_num + 1)) if i != len(posts_to_use[pid]["mytranscript"]) - 1 else posts_to_use[pid]["audio_length"])
                starting_section = None
                ending_section = 0
                part_start = None
                part_end = None
                LOGGER.info("Part start tmp: %s, part end tmp: %s", part_start_tmp, part_end_tmp)
                for i, section in enumerate(posts_to_use[pid]["mytranscript"]):
                    if part_start_tmp == 0 and i == 0:
                        LOGGER.info("Part start is 0, using first section %s", section)
                        part_start = section["start"]
                        starting_section = i

                    if section["start"] >= part_start_tmp and part_start is None and starting_section is None:
                        LOGGER.info("Part start found at section %s, current part start: %s, starting section: %s", section, part_start, starting_section)
                        part_start = posts_to_use[pid]["mytranscript"][i-1]["start"]
                        starting_section = i
                    if section["end"] >= part_end_tmp or i == len(posts_to_use[pid]["mytranscript"]) - 1:
                        LOGGER.info("Part end found at section %s", section)
                        part_end = section["end"]
                        ending_section = i
                        break
                LOGGER.info("="* 90)
                LOGGER.info("pst %s, pet %s, ps %s, pe %s, start_sec %s, end_sec %s, len of trans %s", part_start_tmp, part_end_tmp, part_start, part_end, starting_section, ending_section, len(posts_to_use[pid]["mytranscript"][starting_section:ending_section]))
                LOGGER.info("first section: %s, last section: %s", posts_to_use[pid]["mytranscript"][starting_section], posts_to_use[pid]["mytranscript"][ending_section-1])
                LOGGER.info("ID: %s, part_num: %s", pid, part_num)
                
                if part_start is None or part_end is None:
                    LOGGER.error("Part start or end not found for %s", pid)
                    LOGGER.error(
                        "Part start: %s, part_end: %s, part_start_tmp: %s, part_end_tmp: %s",
                        part_start,
                        part_end,
                        part_start_tmp,
                        part_end_tmp,
                    )
                    raise ValueError(
                        f"Part start or end not found for {pid}, part_start: {part_start}, part_end: {part_end}"
                    )
                LOGGER.info("Finished creating images")
                background = choice(mpfours)
                clip_length = get_clip_duration(
                    os.path.join(REDDIT_TEMPLATE_BG, background)
                )
                LOGGER.info("Clip bg, length_bg_total, pid: %s, %s, %s", background, clip_length, pid)
                # Grab random part from mc parkor/subway surfers/temple run
                start = randint(0, int(clip_length - part_end + 1))
                end = start + part_end
                # run video creator that combines video with audio with transcript
                posts_to_use[pid][f"vfile_{part_num}"] = f"tmp/clips/reddit_{pid}_{part_num}.mp4"
                LOGGER.info("Creating video for %s", pid)
                create_reddit_video_aiyt(
                        video_path=os.path.join(REDDIT_TEMPLATE_BG, background),
                        audio_path=posts_to_use[pid]["auFile"],
                        output_path=posts_to_use[pid][f"vfile_{part_num}"],
                        start_time=start,
                        end_time=end,
                        pid=pid,
                        part_start=part_start,
                        part_end=part_end,
                        adjust=posts_to_use[pid]["mytranscript"][starting_section]["start"],
                        first_part=part_num == 0,
                        transcript=posts_to_use[pid]["mytranscript"][starting_section:ending_section],
                        tw=1080,
                        th=1920,
                        post_png_file=image_file,
                        title=swap_words_numbers(
                            reddit_acronym(
                                reddit_remove_bad_words(posts_to_use[pid]["title"])
                            )
                        ),
                        title_len=posts_to_use[pid]["audio_length_title"]
                    )
                if not os.path.exists(posts_to_use[pid][f"vfile_{part_num}"]):
                    LOGGER.error("Video not created %s", posts_to_use[pid][f"vfile_{part_num}"])
                    exit(1)
                    continue
            update_reddit_post_clip_tt_aiyt(
                post_id=pid,
                tiktok_posted=post["sched"],
            )
            for lang in POSSIBLE_TRANSLATE_LANGS:
                for part_num in range(post["parts"]):
                    # Create img for post
                    image_file = render_html_to_png(
                            post_id=pid,
                            title=translate_en_to((posts_to_use[pid]["title"]) + ("Part " + str(part_num) if part_num >= 1 else ""),lang=lang),
                            subreddit=sub_name,
                            subreddit_id=sub_name,
                            user_id="reddit",
                            user_name=dirty_remove_cuss(post.get("author", "Unknown")),
                            time_ago=datetime.fromisoformat(
                                post["posted_at"].replace('Z', '+00:00')
                            ),
                            score_int=post["views"],
                            comment_int=post["likes"],
                        )
                    part_start_tmp = (posts_to_use[pid][f"audio_length_{lang}"]/post["parts"]) * part_num
                    part_end_tmp = (((posts_to_use[pid][f"audio_length_{lang}"]/post["parts"]) * (part_num + 1)) if i != len(posts_to_use[pid][f"mytranscript_{lang}"]) - 1 else posts_to_use[pid][f"audio_length_{lang}"])
                    starting_section = None
                    ending_section = 0
                    part_start = None
                    part_end = None
                    for i, section in enumerate(posts_to_use[pid][f"mytranscript_{lang}"]):
                        if part_start_tmp == 0 and i == 0:
                            LOGGER.info("Part start is 0, using first section %s", section)
                            part_start = section["start"]
                            starting_section = i

                        if section["start"] >= part_start_tmp and part_start is None and starting_section is None:
                            LOGGER.info("Part start found at section %s, current part start: %s, starting section: %s", section, part_start, starting_section)
                            part_start = posts_to_use[pid]["mytranscript"][i-1]["start"]
                            starting_section = i
                        if section["end"] >= part_end_tmp or i == len(posts_to_use[pid]["mytranscript"]) - 1:
                            LOGGER.info("Part end found at section %s", section)
                            part_end = section["end"]
                            ending_section = i
                            break
                    if not part_start or not part_end:
                        LOGGER.error("Part start or end not found for %s", pid)
                        LOGGER.error(
                            "Part start: %s, part_end: %s, part_start_tmp: %s, part_end_tmp: %s",
                            part_start,
                            part_end,
                            part_start_tmp,
                            part_end_tmp,
                        )
                        LOGGER.error("Transcript: %s", posts_to_use[pid][f"mytranscript_{lang}"])
                        raise ValueError(
                            f"Part start or end not found for {pid}, part_start: {part_start}, part_end: {part_end}"
                        )
                    LOGGER.info("Finished creating images")
                    background = choice(mpfours)
                    clip_length = get_clip_duration(
                        os.path.join(REDDIT_TEMPLATE_BG, background)
                    )
                    LOGGER.info("Clip, length, pid: %s, %s, %s", background, clip_length, pid)
                    # Grab random part from mc parkor/subway surfers/temple run
                    start = randint(0, int(clip_length - part_end + 1))
                    end = start + part_end
                    # run video creator that combines video with audio with transcript
                    posts_to_use[pid][f"vfile_{part_num}_{lang}"] = f"tmp/clips/reddit_{pid}_{part_num}_{lang}.mp4"
                    LOGGER.info("Creating video for %s", pid)
                    create_reddit_video_aiyt(
                            video_path=os.path.join(REDDIT_TEMPLATE_BG, background),
                            audio_path=posts_to_use[pid][f"auFile_{lang}"],
                            output_path=posts_to_use[pid][f"vfile_{part_num}_{lang}"],
                            start_time=start,
                            end_time=end,
                            pid=pid,
                            part_start=part_start,
                            part_end=part_end,
                            adjust=posts_to_use[pid][f"mytranscript_{lang}"][starting_section]["start"],
                            first_part=part_num == 0,
                            transcript=posts_to_use[pid][f"mytranscript_{lang}"][starting_section:ending_section],
                            tw=1080,
                            th=1920,
                            post_png_file=image_file,
                            title=translate_en_to(swap_words_numbers(
                                reddit_acronym(
                                    reddit_remove_bad_words(posts_to_use[pid]["title"])
                                )
                            )),
                            title_len=posts_to_use[pid][f"audio_length_title_{lang}"]
                        )
                    if not os.path.exists(posts_to_use[pid][f"vfile_{part_num}_{lang}"]):
                        LOGGER.error("Video not created %s", posts_to_use[pid][f"vfile_{part_num}_{lang}"])
                        continue
                update_reddit_post_clip_tt_aiyt(
                    post_id=pid,
                    tiktok_posted=post["sched"],
                )
    else:
        for pid, post in posts_to_use.items():
            for part_num in range(post["parts"]):
                posts_to_use[pid][f"vfile_{part_num}"] = f"tmp/clips/reddit_{pid}_{part_num}.mp4"
                posts_to_use[pid]["auFile"] = f"tmp/audios/{pid}_tts.wav"
                for lang in POSSIBLE_TRANSLATE_LANGS:
                    posts_to_use[pid][f"vfile_{part_num}_{lang}"] = f"tmp/clips/reddit_{pid}_{part_num}_{lang}.mp4"
                    posts_to_use[pid][
                        f"auFile_{lang}"
                    ] = f"tmp/audios/{pid}_{lang}_tts.wav"

    
    #####################################
    # Clean up
    #####################################
    for pid, post in posts_to_use.items():
        for part_num in range(post["parts"]):
            shutil.copyfile(post[f"vfile_{part_num}"], f"{CLIPS_FOLDER}/reddit_{pid}_{part_num}.mp4")
            os.remove(post[f"vfile_{part_num}"])
            os.remove(post["auFile"])
            

            for lang in POSSIBLE_TRANSLATE_LANGS:
                shutil.copyfile(
                    post[f"vfile_{part_num}_{lang}"], f"{CLIPS_FOLDER}/reddit{lang}_{pid}.mp4"
                )
                os.remove(post[f"vfile_{part_num}_{lang}"])
                os.remove(post[f"auFile_{lang}"])
                
        


    LOGGER.info("Reddit posts done")


if __name__ == "__main__":
    main_reddit_coms_orch()
