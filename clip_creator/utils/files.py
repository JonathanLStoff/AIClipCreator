import shutil
import os
from clip_creator.conf import LOGGER
def copy_to_tmp(dl_fl:str, tmp_dl_fl:str):
    """
    Remove the files needed
    """
    shutil.copy(dl_fl, tmp_dl_fl)

def save_space(dl_fl:str, tmp_dl_fl:str, clips_fl:str, tmp_clips_fl:str):
    """
    Remove the files needed
    """
    try:
        os.remove(tmp_dl_fl)
    except Exception as e:
        LOGGER.error(f"Error removing file: {e}")
        
    shutil.copy(tmp_clips_fl, clips_fl)