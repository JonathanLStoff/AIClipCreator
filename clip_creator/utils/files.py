import shutil
import os
def copy_to_tmp(dl_fl:str, tmp_dl_fl:str):
    """
    Remove the files needed
    """
    shutil.copy(dl_fl, tmp_dl_fl)

def save_space(dl_fl:str, tmp_dl_fl:str, clips_fl:str, tmp_clips_fl:str):
    """
    Remove the files needed
    """
    os.remove(tmp_dl_fl)
    shutil.move(tmp_clips_fl, clips_fl)