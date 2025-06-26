cd C:\Users\legoc\Desktop\AI\AIClipCreator
set PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
poetry run python reddit_ai.py
poetry run python scheduled_post.py --skipscroll
poetry run python reddit_com.py
poetry run python scheduled_post.py --skipscroll