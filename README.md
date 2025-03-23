# AIClipCreator

## Useful Links:
Voices for TTS: https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md#spanish

## DB Format

Database Name: `aiclipcreator`
Tables:

- `videos`
- `clips`

### `videos` Table

`used_clips` (One to many relationship with `clips`)

columns:

- `id` (str, primary key)
- `name` (str)
- `created_at` (DateTimeField)
- `updated_at` (DateTimeField)
- `uploaded_at` (DateTimeField)
- `transcript` (TextField)
- `one_word_most_used` (str)
- `one_word_count` (int)
- `two_word_most_used` (str)
- `two_word_count` (int)
- `three_word_most_used` (str)
- `three_word_count` (int)
- `views` (int)
- `likes` (int)
- `top_yt_comment` (TextField)
- `top_reddit_comment` (TextField)
- `reddit_url` (str)
- `video_creator` (str)

### `clips` Table

columns:

- `id` (int, primary key, autoincrement)
- `video_id` (str, foreign key to `videos`)
- `start_time` (int)
- `end_time` (int)
- `clip_transcript` (TextField)
- `post_tiktok` (DateTimeField)
- `tiktok_url` (str)
- `post_instagram` (DateTimeField)
- `instagram_url` (str)
- `post_youtube` (DateTimeField)
- `youtube_url` (str)

### Notes:

- Check for face in x percent of the frame where x is like within 10% of one of the corners
