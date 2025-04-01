from clip_creator.adb.api.uploader import ADBUploader
from clip_creator.conf import LOGGER


def upload_phsyphone(
    video_path: str,
    description: str,
    draft: bool = False,
    photo_mode: bool = False,
    only_me: bool = False,
    lang: str = "en",
):
    
    uploader_class = ADBUploader()
    
    
    
    # upload video
    succed = uploader_class.add_video(video_path)
    if not succed:
        LOGGER.error("Error uploading video")
        return False
    
    # Upload to TikTok
    succed = uploader_class.upload_tiktok(
        description=description,
        draft=draft,
        photo_mode=photo_mode,
        only_me=only_me,
        sound=False,
        lang=lang,
    )
    if not succed:
        LOGGER.error("Error uploading video")
        return False
    if lang != "en":
        return True
    # run insta
    try:
        uploader_class.upload_instagram(
            description=description, draft=draft, photo_mode=photo_mode, only_me=only_me
        )
    except Exception as e:
        LOGGER.error("Error uploading video to Instagram")
        LOGGER.error(e)
    try:
        #upload yt
        uploader_class.upload_yt(description=description, draft=draft, photo_mode=photo_mode, only_me=only_me)
    except Exception as e:
        
        LOGGER.error("Error uploading video to YouTube")
        LOGGER.error(e)

    return True


if __name__ == "__main__":
    # subprocess.run(['/opt/homebrew/bin/adb', '-s', 'ZY22H5JP3S', 'shell', 'mkdir', '/storage/self/primary/DCIM/TTUploader'])
    # exit()
    upload_phsyphone(
        "D:/tmp/clips/reddites_1j4xwhl.mp4",
        "This is a test description",
        draft=False,
        photo_mode=False,
        only_me=True,
        lang="es",
    )
