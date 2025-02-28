import os
import shutil
import time

from clip_creator.conf import LOGGER


def clean_up_files():
    """
    Remove the files needed
    """
    for file in os.listdir("tmp"):
        if file.endswith(".mp4") or file.endswith(".mp3") or file.endswith(".wav"):
            try:
                os.remove(f"tmp/{file}")
            except Exception as e:
                LOGGER.error(f"Error removing file: {e}")


def copy_to_tmp(dl_fl: str, tmp_dl_fl: str):
    """
    Remove the files needed
    """
    shutil.copy(dl_fl, tmp_dl_fl)


def save_space(dl_fl: str, tmp_dl_fl: str, clips_fl: str, tmp_clips_fl: str):
    """
    Remove the files needed
    """
    try:
        time.sleep(1)
        os.remove(tmp_dl_fl)

    except Exception as e:
        LOGGER.error(f"Error removing file: {e}")

    time.sleep(1)
    shutil.copy(tmp_clips_fl, clips_fl)

    try:
        time.sleep(1)
        os.remove(tmp_clips_fl)
    except Exception as e:
        LOGGER.error(f"Error removing file: {e}")
