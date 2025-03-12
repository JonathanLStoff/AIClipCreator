from clip_creator.adb.api.uploader import ADBUploader
import time
import subprocess
from clip_creator.conf import LOGGER, ADB_DEVICE, BLUESTACKS_PATH, BLUESTACKS_INSTANCE

def upload_bluestacks(video_path:str, description:str, draft:bool=False, photo_mode:bool=False, only_me:bool=False, hidden:bool=True):
    # Open Bluestacks
    if hidden:
        subprocess.Popen(executable=BLUESTACKS_PATH, args=["--hidden", "--instance", BLUESTACKS_INSTANCE], shell=False)
    else:
        LOGGER.info([f'"{BLUESTACKS_PATH}"', "--instance", BLUESTACKS_INSTANCE])
        subprocess.Popen(executable=BLUESTACKS_PATH, args=["--instance", BLUESTACKS_INSTANCE], shell=False)
    # Upload to TikTok
    ADBUploader().upload_tiktok(video_path=video_path, description=description, draft=draft, photo_mode=photo_mode, only_me=only_me)
    
    
if __name__ == "__main__":
    upload_bluestacks("D:/tmp/clips/reddit1j7jlb1.mp4", "This is a test description", draft=False, photo_mode=False, only_me=True, hidden=False)