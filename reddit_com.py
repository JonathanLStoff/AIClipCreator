import torch
import os
import argparse
import json
import shutil
import uuid
from random import choice, randint
from num2words import num2words
from clip_creator.conf import LOGGER, CLIPS_FOLDER, REDDIT_TEMPLATE_BG, POSSIBLE_TRANSLATE_LANGS, POSSIBLE_TRANSLATE_LANGS_TTS
from clip_creator.tts.ai import TTSModelKokoro
from clip_creator.lang.translate import translate_en_to
from clip_creator.utils.forcealign import force_align
from clip_creator.social.custom_tiktok import upload_video_tt
from clip_creator.social.reddit import reddit_coms_orch, find_sub_reddit_coms
from clip_creator.utils.path_setup import check_and_create_dirs
from clip_creator.utils.caption_img import render_html_to_png, render_html_to_png_comment
from clip_creator.utils.math_things import get_88_percentile
from clip_creator.utils.scan_text import reddit_remove_bad_words, sort_and_loop_by_max_int_key_coms, get_top_posts_coms, swap_words_numbers, remove_non_letters, reddit_acronym
from clip_creator.vid_ed.red_vid_edit import get_clip_duration, get_audio_duration, create_reddit_video
from clip_creator.utils.schedules import get_timestamps
from clip_creator.utils.schedules import none_old_timestamps
from clip_creator.db.db import (
    update_reddit_post_clip_com,
    create_database,
    add_reddit_post_clip_com,
    get_rows_where_tiktok_null_or_empty_com,
    get_all_post_ids_red_com,
)
def main_reddit_coms_orch():
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
    found_posts = get_all_post_ids_red_com()
    
    href_list = find_sub_reddit_coms(found_posts, min_posts=10)
    netw_redd_posts = reddit_coms_orch(href_list, found_posts, min_post=10, max_post=20)
    
    
    #####################################
    # Add posts to database
    #####################################
    for post in netw_redd_posts:
        if "/" in post['url']:
            if post['url'].split("/")[3] in found_posts:
                LOGGER.error(f"ITEM ADDED FROM POSTS IS ALREADY IN DB: {post['url']}")
            else:
                add_reddit_post_clip_com(
                    post_id=post['post_id'],
                    title=post['title'],
                    posted_at=post['posted_at'],
                    content=post['content'],
                    url=post['url'],
                    upvotes=post['upvotes'],
                    comments=post['comments'],
                    nsfw=post['nsfw'],
                    comments_json=post['comments_list'], # a list[dict] of comments where dict is {author, text, score}
                    )
                
        else:
            LOGGER.error(f"Invalid URL: {post['url']}")
    #####################################
    # Remove from list if 160 words not met
    #####################################
    unused_posts = get_rows_where_tiktok_null_or_empty_com()
    posts_to_use = {}
    for post in unused_posts:
        if not post['nsfw']: # if not nsfw
            posts_to_use[post['post_id']] = post
    #####################################
    # Compile script
    #####################################
    for pid, post in posts_to_use.items():
        posts_to_use[pid]["comments_json"] = json.loads(post['comments_json'])
        ht_text = remove_non_letters(
            swap_words_numbers(
                reddit_acronym(
                    reddit_remove_bad_words(
                        post['title'] + "\n" + post['content']
                        )
                    )
                )
            )
        posts_to_use[pid]["chunks"] = {
            uuid.uuid4(): {
                "idx":0, 
                "text": ht_text
                }
            }
        posts_to_use[pid]["comments_json"] = sort_and_loop_by_max_int_key_coms(posts_to_use[pid]["comments_json"]) # sort by score
        comments_above = get_88_percentile(posts_to_use[pid]["comments_json"])
        posts_to_use[pid]["comments_above"] = comments_above
        for idx, comment in enumerate(posts_to_use[pid]["comments_json"]):
            tt_text = remove_non_letters(
                swap_words_numbers(
                    reddit_acronym(
                        reddit_remove_bad_words(
                            "\n" + num2words(idx + 1) + "\n" + comment['content'] + "\n" + (comment['best_reply'].get('content', "") if comment['best_reply'].get('upvotes', "") > comments_above else "")
                            )
                        )
                    )
                )
            
            posts_to_use[pid]["chunks"][uuid.uuid4()] = {
                    "idx": idx + 1, 
                    "text": tt_text,
                    "reply": True if comment['best_reply'].get('upvotes', "") > comments_above else False,
                    "com_json": comment
                }
            
    ########################################
    # Calc time to post
    ########################################
    day_sched = none_old_timestamps()
    LOGGER.info("Day Sched: %s", day_sched)
    best_posts = get_top_posts_coms(posts_to_use, len(day_sched))
        
    # else:
    #     LOGGER.info("Using created videos")
    #     best_posts = []
    #     for file in os.listdir(TMP_CLIPS_FOLDER):
    #         pid_tmp = get_id_from_vfile(file)
    #         if pid_tmp:
    #             posts_to_use[pid_tmp] = get_reddit_post_clip_by_id(pid_tmp)
    #             best_posts.append(pid_tmp)
    poping = []
    for i, sched in enumerate(day_sched):
        if sched == None:
            LOGGER.info("Poping %s", i)
            poping.append(i)
    for i, ix in enumerate(poping):
        day_sched.pop(ix-i)
    LOGGER.info("Day Sched: %s", day_sched)
    posts_to_keep = {}
    for i, pid in enumerate(best_posts):
        if i >= len(day_sched):
            break
        posts_to_keep[pid] = posts_to_use[pid]
        posts_to_keep[pid]['sched'] = day_sched[i]
        LOGGER.info("Post sched %s, %s", pid, posts_to_keep[pid]['sched'])     
    posts_to_use = posts_to_keep
    #####################################
    # Translate to other languages
    #####################################
    if not args.usevids:
        for pid, post in posts_to_use.items():
            for lang in POSSIBLE_TRANSLATE_LANGS:
                posts_to_use[pid][f'chunks_{lang}'] = posts_to_use[pid]['chunks']
                for uid, chunk in post[f'chunks_{lang}'].items():
                    LOGGER.info("Translating %s to %s", pid, lang)
                    posts_to_use[pid][f'chunks_{lang}'][uid]['text'] = translate_en_to(chunk['text'], lang)
    #####################################
    # Create Audio using TTS
    #####################################
    # FIX THIS:
    if not args.usevids:
        tts_model = TTSModelKokoro()
        for pid, post in posts_to_use.items():
            LOGGER.info("Creating Audio for %s", pid)
            for uid, chunk in post['chunks'].items():
                
                posts_to_use[pid]['chunks'][uid]['auFile'] = f"tmp/audios/{pid}_{uid}.wav"
                if not os.path.exists(f"tmp/audios/{pid}_{uid}.wav"):
                    tts_model.run_it(posts_to_use[pid]['chunks'][uid]['auFile'], chunk['text'])
        
        # Create Audio for other languages
        
        for lang in POSSIBLE_TRANSLATE_LANGS:
            
            tts_model_lang = TTSModelKokoro(
                voice=choice(POSSIBLE_TRANSLATE_LANGS_TTS[lang]["tts"]),
                lang_code=POSSIBLE_TRANSLATE_LANGS_TTS[lang][lang]
                )
            for pid, post in posts_to_use.items():
            
                LOGGER.info("Creating Audio for %s", pid)
                for uid, chunk in post[f'chunks_{lang}'].items():
                    posts_to_use[pid][f'chunks_{lang}'][uid]['auFile'] = f"tmp/audios/{pid}_{lang}_{uid}.wav"
                    if not os.path.exists(posts_to_use[pid][f'chunks_{lang}'][uid]['auFile']):
                        tts_model_lang.run_it(posts_to_use[pid][f'chunks_{lang}'][uid]['auFile'], chunk['text'])
    #####################################
    # Force align text to audio
    #####################################
    device = "cpu"
    if torch.cuda.is_available():
        device = "cuda:0"
        torch.cuda.empty_cache()
    for pid, post in posts_to_use.items():
        for uid, chunk in post['chunks'].items():
            posts_to_use[pid]['chunks'][uid]["ascript"] = force_align(device=device, file=chunk['auFile'], yt_ft_transcript=chunk['text'])
    for lang in POSSIBLE_TRANSLATE_LANGS:
        for pid, post in posts_to_use.items():
            for uid, chunk in post[f'chunks_{lang}'].items():
                posts_to_use[pid][f'chunks_{lang}'][uid]['ascript'] = force_align(device=device, file=chunk['auFile'], yt_ft_transcript=chunk['text'])
    
    #####################################
    # Create video
    #####################################
    if not args.usevids:
        mpfours = [file for file in os.listdir(REDDIT_TEMPLATE_BG) if file.endswith(".mp4")]
        for pid, post in posts_to_use.items():
            
            LOGGER.info("Post: %s", pid)
            if not post.get('sched'):
                continue
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
            for uid, chunk in post['chunks'].items():
                if chunk.get('idx') == 0:
                    post_png_file = render_html_to_png(
                        post_id=pid,
                        title=chunk['text'],
                        subreddit=sub_name,
                        subreddit_id=sub_name,
                        user_id="reddit",
                        user_name=dirty_remove_cuss(post['author']),
                        time_ago=datetime.fromisoformat(post['posted_at'][:-2] + ':' + post['posted_at'][-2:]),
                        score_int=post['upvotes'],
                        comment_int=post['comments']
                    )
                else:
                    post_png_file = render_html_to_png_comment(
                        post_id=pid,
                        chunk_id=uid,
                        comment_json=chunk['com_json'],
                        reply=chunk.get("reply", False),
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
                audio_path=posts_to_use[pid]['filename'],
                output_path=posts_to_use[pid]['vfile'],
                start_time=start,
                end_time=end,
                pid=pid,
                part_start=posts_to_use[pid]['part_start'],
                parts=posts_to_use[pid]['parts'],
                transcript=posts_to_use[pid]['aligned_ts'],
                tw=1080,
                th=1920,
                paragraph=posts_to_use[pid]['content'],
                post_png_file=post_png_file,
                title=swap_words_numbers(reddit_acronym(reddit_remove_bad_words(posts_to_use[pid]['title'])))
            )
            for lang in POSSIBLE_TRANSLATE_LANGS:
                post_png_file = render_html_to_png(
                    post_id=pid,
                    title=translate_en_to(post['title'], lang),
                    subreddit=translate_en_to(sub_name, lang),
                    subreddit_id=translate_en_to(sub_name, lang),
                    user_id="reddit",
                    user_name=translate_en_to(dirty_remove_cuss(post['author']), lang),
                    time_ago=datetime.fromisoformat(post['posted_at'][:-2] + ':' + post['posted_at'][-2:]),
                    score_int=post['upvotes'],
                    comment_int=post['comments']
                )
                posts_to_use[pid][f'vfile_{lang}'] = f"tmp/clips/reddit{lang}_{pid}.mp4"
                end = start + posts_to_use[pid][f'audio_length_{lang}']
                create_reddit_video(
                    video_path=os.path.join(REDDIT_TEMPLATE_BG, background),
                    audio_path=posts_to_use[pid][f'filename_{lang}'],
                    output_path=posts_to_use[pid][f'vfile_{lang}'],
                    start_time=start,
                    end_time=end,
                    pid=pid,
                    part_start=posts_to_use[pid][f'part_start_{lang}'],
                    parts=posts_to_use[pid][f'parts_{lang}'],
                    transcript=posts_to_use[pid][f'aligned_ts_{lang}'],
                    tw=1080,
                    th=1920,
                    paragraph=posts_to_use[pid][f'content_{lang}'],
                    post_png_file=post_png_file,
                    title=translate_en_to(swap_words_numbers(reddit_acronym(reddit_remove_bad_words(posts_to_use[pid]['title']))), lang)
                )
    else:
        for pid, post in posts_to_use.items():
            posts_to_use[pid]['vfile'] = f"tmp/clips/reddit_{pid}.mp4"
            posts_to_use[pid]['parts'] = 1
            posts_to_use[pid]['filename'] = f"tmp/audios/{pid}_tts.wav"
            for lang in POSSIBLE_TRANSLATE_LANGS:
                posts_to_use[pid][f'vfile_{lang}'] = f"tmp/clips/reddit{lang}_{pid}.mp4"
                posts_to_use[pid][f'parts_{lang}'] = 1
                posts_to_use[pid][f'filename_{lang}'] = f"tmp/audios/{pid}_{lang}_tts.wav"
    
    ########################################
    # Calc time to post
    ########################################
    number_posts = 0
    for pid, post in posts_to_use.items():
        number_posts += 1
    if number_posts == 0:
        LOGGER.info("No clips to post")
        allsched = []
    else:
        allsched = get_timestamps(number_posts)
    allsched_idx = 0
    for pid, post in posts_to_use.items():
        # if ERRORS_TYPES[2] in errors_lot[id].keys():
        #     continue
        if allsched_idx < len(allsched):
            posts_to_use[pid]['sched'] = allsched[allsched_idx]
            allsched_idx += 1
        else:
            LOGGER.error("Not enough timestamps for %s", pid)
            posts_to_use[pid]['sched'] = None
    
    ######################################
    # Compile Description
    ######################################
    for pid, post in posts_to_use.items():
        posts_to_use[pid]["desc"] = (
            "#fyp #gaming #clip #fyppppppppppppp\ncredit"
            f"{post['title']} on Reddit\n"
        )    
    #####################################
    # Upload tiktok
    #####################################
    for pid, post in posts_to_use.items():
        upload_video_tt(
                        post['vfile'], 
                        post['sched'], 
                        post["desc"], 
                        submit=True
                    )
        update_reddit_post_clip(
            post_id=pid, 
            tiktok_posted=post['sched'], 
            transcript=post['aligned_ts'], 
            length=post['audio_length']
        )
    #####################################
    # Clean up
    #####################################
    for pid, post in posts_to_use.items():
        shutil.copyfile(post['vfile'], f"{CLIPS_FOLDER}/reddit_p_{pid}.mp4")
        os.remove(post['vfile'])
        os.remove(post['filename'])
    LOGGER.info("Reddit posts done")
    
if __name__ == "__main__":
    main_reddit_coms_orch()
    
    
        