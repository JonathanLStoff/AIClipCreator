from clip_creator.adb.api.uploader import ADBUploader
import time
import subprocess
from clip_creator.conf import LOGGER, ADB_DEVICE, BLUESTACKS_PATH, BLUESTACKS_INSTANCE

def upload_phsyphone(video_path:str, description:str, draft:bool=False, photo_mode:bool=False, only_me:bool=False):
    uploader_class=ADBUploader()
    #upload video
    uploader_class.add_video(video_path)
    # run insta
    uploader_class.upload_instagram(description=description, draft=draft, photo_mode=photo_mode, only_me=only_me)
    exit()
    # Upload to TikTok
    uploader_class.upload_tiktok(description=description, draft=draft, photo_mode=photo_mode, only_me=only_me, sound=False)
    
    
if __name__ == "__main__":
    # subprocess.run(['/opt/homebrew/bin/adb', '-s', 'ZY22H5JP3S', 'shell', 'mkdir', '/storage/self/primary/DCIM/TTUploader'])
    # exit()
    upload_phsyphone("/Users/jonathanstoff/Desktop/Scripts/AIClipCreator/test_files/clip_SXoQ5gJLJdY.mp4", "This is a test description", draft=False, photo_mode=False, only_me=True)