import os


def check_and_create_dirs(base_dir="tmp"):
    """
    Checks for the existence of directories: tmp, tmp/clips, and tmp/raw.
    Creates them if they do not exist.

    Parameters:
        base_dir (str): The base directory to use. Defaults to 'tmp'.
    """
    required_paths = [
        base_dir,
        os.path.join(base_dir, "clips"),
        os.path.join(base_dir, "raw"),
        os.path.join(base_dir, "caps_img"),
        os.path.join(base_dir, "caps_vids"),
        os.path.join(base_dir, "audios"),
    ]

    for path in required_paths:
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
            print(f"Created directory: {path}")
        else:
            
            print(f"Directory already exists: {path}")
    # for file in os.listdir(os.path.join(base_dir, "audios")):
    #     os.remove(os.path.join(os.path.join(base_dir, "audios"), file))

def get_unused_videos(used_videos: list[str], raw_dir: str):
    """
    Get a list of unused videos in the raw directory.

    Parameters:
        used_videos (list[str]): A list of used video filenames.
        raw_dir (str): The path to the raw directory.

    Returns:
        list[str]: A list of unused video filenames.
    """
    all_files = os.listdir(raw_dir)
    all_videos = [
        file.replace(".mp4", "") for file in all_files if file.endswith(".mp4") and not file.startswith("._")
    ]
    unused_videos = [video for video in all_videos if video not in used_videos]
    dict_unused_videos = []
    for vid in unused_videos:
        dict_unused_videos.append({"id": {"videoId": vid}})
    return dict_unused_videos, unused_videos
