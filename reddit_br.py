from clip_creator.conf import LOGGER
from clip_creator.tts.ai import TTSModel
from clip_creator.utils.forcealign import force_align
from clip_creator.social.reddit import reddit_posts_orch
from clip_creator.utils.path_setup import check_and_create_dirs
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
        pass
    #####################################
    # Create Audio using TTS
    #####################################
    
    tts_model = TTSModel()
    
    #####################################
    # Force align text to audio
    #####################################
    force_align
    #####################################
    # Create video
    #####################################
    
    # Grab random part from mc parkor/subway surfers/temple run
    
    # run video creator that combines video with audio with transcript