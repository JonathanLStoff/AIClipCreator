import datetime
import os
import random
import subprocess
from time import sleep

import uiautomator2 as u2
from uiautomator2.exceptions import SessionBrokenError

from clip_creator.adb.dump import dump
from clip_creator.conf import (
    ADB_DEVICE,
    ADB_PATH,
    ADB_PATH_EXE,
    ADB_SHELL,
    LOGGER,
    POSSIBLE_TRANSLATE_LANGS_TTS,
)

# "Static" config
SD_CARD_INDEX = False
POSSIBLE_APPS = ["com.zhiliaoapp.musically", "com.ss.android.ugc.trill"]
INSTA_APP = "com.instagram.android"
YT_APP = "com.google.android.youtube"
FB_APP = "com.facebook.appmanager"
RELATIVE_PATH = f"{ADB_PATH}/DCIM"  # has to be it's own folder
RELATIVE_PATH_T = f"{ADB_PATH}/Pictures"  # has to be it's own folder


class ADBUploader:
    def __init__(self):
        try:
            self.adb_raw(["connect", ADB_DEVICE])

        except Exception as e:
            LOGGER.error(e)

        self.device_size = (0, 0)
        self.d = u2.connect(ADB_DEVICE)
        self.d.shell("input keyevent 82")
        self.d.shell("input keyevent 3")

    def adb(self, command: list):
        command_list = [ADB_PATH_EXE, "-s", ADB_DEVICE, *command]
        LOGGER.info(f"Running command: {command_list}")
        proc = subprocess.Popen(command_list, stdout=subprocess.PIPE, shell=ADB_SHELL)
        (out, err) = proc.communicate()
        return out.decode("utf-8")

    def adb_raw(self, command: list):
        command_list = [ADB_PATH_EXE, *command]
        LOGGER.info(f"Running command: {command_list}")
        proc = subprocess.Popen(command_list, stdout=subprocess.PIPE, shell=ADB_SHELL)
        (out, err) = proc.communicate()
        return out.decode("utf-8")

    def adb_wait(self, command: list):
        command_list = [ADB_PATH_EXE, *command]
        LOGGER.info(f"Running command: {command_list}")
        return subprocess.run(
            command_list, shell=ADB_SHELL, stdout=subprocess.PIPE
        ).stdout.decode("utf-8")

    def adb_stri_command(self, command: list):
        command_list = [ADB_PATH_EXE, *command]
        command_string = " ".join(command_list)
        LOGGER.info(f"Running command: {command_string}")
        return subprocess.run(
            command_string, shell=True, stdout=subprocess.PIPE
        ).stdout.decode("utf-8")

    def touch(self, x, y, relative=True):
        self.device_size
        # coords are in percentage
        if self.device_size[0] == 0:
            self.device_size = (
                self.d.info["displayWidth"],
                self.d.info["displayHeight"],
            )
        LOGGER.info(f"Touching at {x}, {y}")
        x = int(x * self.device_size[0]) if relative else x
        y = int(y * self.device_size[1]) if relative else y
        self.d.click(x, y)

    def add_sound_tt(self):
        self.d(text="Add sound").wait()
        self.d(text="Add sound").click()
        sleep(1)
        self.d(text="Volume").wait()
        self.d(text="Volume").click()
        sleep(1)
        self.d(className="android.widget.SeekBar", instance="1").click(
            offset=(0.2, 0.5)
        )
        sleep(1)
        self.d(text="Done").wait()
        self.d(text="Done").click()
        sleep(1)
        self.d.press("back")

    def add_location_tt(self):
        pass

    def add_video(self, video_path: str) -> bool:
        # Make sure the path exists
        try:
            LOGGER.info(
                self.adb_stri_command(["shell", "rm", "-rf", f'"{RELATIVE_PATH}/*"'])
            )
            LOGGER.info("Deleted old files")
            LOGGER.info(
                self.adb_stri_command(["shell", "rm", "-rf", f'"{RELATIVE_PATH_T}/*"'])
            )
        except:
            pass
        # LOGGER.info('Making new folder: %s', RELATIVE_PATH)
        # LOGGER.info(self.adb_wait(["shell", "mkdir", '-m', '777', RELATIVE_PATH]))
        try:
            # Copy files to device
            base_file_name = os.path.basename(video_path)
            LOGGER.info(f"Copying {video_path} to {RELATIVE_PATH}/{base_file_name}")
            self.d.push(
                os.path.abspath(video_path), f"{RELATIVE_PATH}/{base_file_name}"
            )
            LOGGER.info(f"Copying {video_path} to {RELATIVE_PATH_T}/{base_file_name}")
            self.d.push(
                os.path.abspath(video_path), f"{RELATIVE_PATH_T}/{base_file_name}"
            )
            # Call the media scanner to add the video to the media content provider
            # I don't know why it's like this, but for some reason the first one only works on my emulator
            self.d.shell(
                "am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d"
                f" file://{RELATIVE_PATH}/{base_file_name}"
            )
            self.d.shell(
                "am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d"
                f" file://{RELATIVE_PATH_T}/{base_file_name}"
            )
        except Exception as e:
            LOGGER.error(e)
            return False
        return True

    def upload_yt(
        self,
        title=None,
        description=None,
        tags=None,
        location=None,
        draft=False,
        photo_mode=False,
        only_me=False,
    ):
        self.d.app_stop(YT_APP)

        self.d.app_start(YT_APP)
        self.d.app_wait(YT_APP, front=True)

        self.d(text="Subscriptions").wait()
        (xi, yi) = self.d(text="Subscriptions").center()
        ad_yi = yi / self.d.info.get("displayHeight", 1)
        self.touch(0.5, ad_yi)
        self.d(text="Add").wait()
        self.d(text="Add").click()
        self.d(text="Create").wait()
        ad_x = (self.d.info.get("displayWidth", 1) / 3) / 2
        (xi, yi) = self.d(description="Create").center()
        ad_y = yi * 2
        self.touch(
            ad_x / self.d.info.get("displayWidth", 1),
            ad_y / self.d.info.get("displayHeight", 1),
        )
        self.d(text="Next").wait()
        self.d(text="Next").click()
        self.d(text="Done").wait()
        self.d(text="Done").click()

        self.d(text="Add").wait(timeout=60)
        LOGGER.info("Found add")

        (xi, yi) = self.d(text="Add").center()
        ad_x = self.d.info.get("displayWidth", 1) - xi
        self.touch(
            ad_x / self.d.info.get("displayWidth", 1),
            yi / self.d.info.get("displayHeight", 1),
        )
        self.d(text="Next").wait()
        self.d(text="Next").click()
        if description:
            self.d(text="Caption your Short").set_text(description)
            self.d.press("back")
        # THIS DOESN'T WORK ************************************
        if only_me:
            if self.d(text="Private").exists(timeout=3):
                self.d.press("back")
            else:
                self.d(text="Public").wait()
                self.d(text="Public").click()
                self.d(text="Private").wait()
                self.d(text="Private").click()
                self.d.press("back")
            sleep(2)
        elif self.d(text="Private").exists(timeout=3):
            self.d(text="Private").wait()
            self.d(text="Private").click()
            self.d(text="Public").wait()
            self.d(text="Public").click()
            self.d.press("back")
            sleep(2)
        if draft:
            LOGGER.info("Saving draft")
            self.d(text="Save draft").wait()
            self.d(text="Save draft").click()
        else:
            LOGGER.info("Uploading")
            self.d(text="Upload Short").wait()
            self.d(text="Upload Short").click()
        sleep(2)
        self.d(text="Uploaded to Your Videos").wait(timeout=60)
        self.d.app_stop(YT_APP)

    def upload_instagram(
        self,
        description=None,
        tags=None,
        location=None,
        draft=False,
        photo_mode=False,
        only_me=False,
    ):
        self.d.app_stop(INSTA_APP)

        self.d.app_start(INSTA_APP)
        self.d.app_wait(INSTA_APP, front=True)
        LOGGER.info("Started Instagram")
        # Click on the upload button
        self.d(resourceId="com.instagram.android:id/creation_tab").wait()
        self.d(resourceId="com.instagram.android:id/creation_tab").click()

        LOGGER.info("Clicked on upload")
        if self.d(text="Start new video").exists(timeout=3):
            self.d(text="Start new video").click()
        sleep(2)
        self.d(text="Templates").wait()
        LOGGER.info("Found templates")
        _, templatey = self.d(text="Templates").center()
        self.touch(0.5, (templatey * 2) / self.d.info.get("displayHeight", 1))
        # self.d(resourceId='com.instagram.android:id/gallery_grid_item_bottom_container', instance=0).wait()
        # self.d(resourceId='com.instagram.android:id/gallery_grid_item_bottom_container', instance=0).click()

        self.d(text="Next").wait()
        self.d(text="Next").click()
        LOGGER.info("Clicked on next")
        if description:
            self.d(
                resourceId="com.instagram.android:id/caption_input_text_view"
            ).set_text(description)
            self.d.press("back")
        if only_me:
            self.d(text="Audience").wait()
            self.d(text="Audience").click()
            self.d(text="Close Friends").wait()
            self.d(text="Close Friends").click()
            self.d.press("back")
        sleep(2)
        if draft:
            self.d(text="Save draft").wait()
            self.d(text="Save draft").click()
        else:
            self.d(text="Share").wait()
            self.d(text="Share").click()
        timeout_time = datetime.datetime.now() + datetime.timedelta(minutes=5)
        LOGGER.info("Waiting for upload to finish")
        while self.d(text="Sharing to Reels…").exists(timeout=3):
            sleep(1)
            if datetime.datetime.now() > timeout_time:
                LOGGER.info("Breaking, timeout")
                break

        LOGGER.info("Done uploading, stopping app")
        sleep(2)
        self.d.app_stop(INSTA_APP)

    def add_location_insta(self):
        self.d(resourceId="com.instagram.android:id/location").click()

    def click_with_random_offset(self, element):
        x = random.randint(1, 100) / 100
        y = random.randint(1, 100) / 100
        element.click(offset=(x, y))

    def switch_profile(self, lang="en"):
        username = (
            "reddit_city_ai"
            if lang == "en"
            else POSSIBLE_TRANSLATE_LANGS_TTS[lang]["username"]
        )
        profname = (
            "reddit_city_ai"
            if lang == "en"
            else POSSIBLE_TRANSLATE_LANGS_TTS[lang]["profile"]
        )
        max_tries = 5
        curr_tries = 0
        while curr_tries < max_tries:
            try:
                LOGGER.info("Switching profile")
                sleep(5)
                if self.d(resourceId="com.zhiliaoapp.musically:id/knl").exists(
                    timeout=5
                ):
                    self.click_with_random_offset(
                        self.d(resourceId="com.zhiliaoapp.musically:id/knl").child(
                            index=0
                        )
                    )
                sleep(2)
                if not self.d(text=profname).exists(timeout=5):
                    if self.d(resourceId="com.zhiliaoapp.musically:id/kn4").exists(timeout=5):
                        self.click_with_random_offset(
                            self.d(resourceId="com.zhiliaoapp.musically:id/kn4")
                        )
                    elif self.d(textContains="reddit").exists(timeout=5):
                        self.click_with_random_offset(self.d(textContains="reddit"))
                    else:
                        self.touch(0.5, 0.09)
                    self.d(textContains=username).wait()
                    self.click_with_random_offset(self.d(descriptionContains=username))
                sleep(2)
                self.d(text="Profile").wait()
                if self.d(text="Profile").info["selected"] is False:
                    LOGGER.info("profile not selected")
                    self.click_with_random_offset(self.d(text="Profile"))
                LOGGER.info("Does profile exist? %s", self.d(text=profname).exists)
                if self.d(text=profname).exists(timeout=5):
                    break
                curr_tries += 1
                if curr_tries == max_tries:
                    LOGGER.info("Could not switch profile")
                    break
            except Exception as e:
                LOGGER.error(e)
                curr_tries += 1
                if curr_tries == max_tries:
                    LOGGER.info("Could not switch profile")
                    raise SessionBrokenError(e)

    def check_if_posted_tt(self, description="", dumpdo=False, lang="en"):
        """
        Returns True if the post is found
        """
        max_tries = 5
        curr_tries = 0
        while True:
            try:
                # Assuming that we are on the home page
                self.d(text="Profile").wait()
                if not self.d(text="Profile").info["selected"]:
                    self.click_with_random_offset(self.d(text="Profile"))
                self.d(text="Following").wait()

                # Click on the first video
                self.d(
                    resourceId="com.zhiliaoapp.musically:id/cover", instance=0
                ).wait()
                self.click_with_random_offset(
                    self.d(resourceId="com.zhiliaoapp.musically:id/cover", instance=0)
                )
                sleep(2)

                # Try 3 ways to click on comments
                if self.d(descriptionContains="Read or add comments.").exists(
                    timeout=5
                ):
                    self.click_with_random_offset(
                        self.d(descriptionContains="Read or add comments.")
                    )
                elif self.d(resourceId="com.zhiliaoapp.musically:id/ctk").exists(
                    timeout=5
                ):
                    self.click_with_random_offset(
                        self.d(resourceId="com.zhiliaoapp.musically:id/ctk")
                    )
                else:
                    self.touch(0.98, 0.723)
                sleep(2)

                # Check if keyboard is open
                if self.d(description="GIF Keyboard").exists(timeout=5):
                    self.d.press("back")
                sleep(2)
                if dumpdo:
                    dump()
                    sleep(2)
                # Get text from description and check if it matches

                part_desc = (
                    " ".join(description.replace("\n", "").split()[:5])
                    .encode("ascii", "ignore")
                    .decode("ascii")
                )
                LOGGER.info("Part desc: %s", part_desc)
                if self.d(
                    resourceId="com.zhiliaoapp.musically:id/desc", instance=0
                ).exists(timeout=5):
                    text_decs = (
                        self.d(
                            resourceId="com.zhiliaoapp.musically:id/desc", instance=0
                        )
                        .info["text"]
                        .encode("ascii", "ignore")
                        .decode("ascii")
                    )
                    LOGGER.info('resourceId="com.zhiliaoapp.musically:id/desc"')
                elif self.d(textStartsWith=part_desc).exists(timeout=5):
                    return True
                else:
                    text_decs = (
                        self.d(resourceId="com.zhiliaoapp.musically:id/dsy", index=0)
                        .child(index=0)
                        .info["text"]
                        .encode("ascii", "ignore")
                        .decode("ascii")
                    )
                    LOGGER.info('resourceId="com.zhiliaoapp.musically:id/dsy"')
                LOGGER.info("Description: %s", text_decs)
                returnsz = False
                if part_desc.lower() not in text_decs.lower():
                    LOGGER.info("%s not in %s", part_desc, text_decs)
                    LOGGER.info("Description not found")
                    if lang != "en":
                        returnsz = True
                else:
                    returnsz = True
                self.d.press("back")
                sleep(2)
                self.d.press("back")
                sleep(2)
            except Exception as e:
                LOGGER.error(e)
                curr_tries += 1

                if curr_tries > max_tries:
                    LOGGER.info("Could not find post")
                    return False

                continue
            LOGGER.info("Post has description found? %s", returnsz)

            return returnsz

    def upload_tiktok(
        self,
        sound=None,
        original_audio=1,
        added_audio=1,
        draft=False,
        description=None,
        photo_mode=False,
        only_me=False,
        lang="en",
    ):
        # Find app

        packages = self.d.app_list()
        for package in POSSIBLE_APPS:
            if package in packages:
                APP_NAME = package
                break
        if not APP_NAME:
            APP_NAME = "com.zhiliaoapp.musically"
        self.d.app_stop(APP_NAME)
        try:
            if not APP_NAME:
                LOGGER.info("TikTok not found")
                return

            while True:
                # Start tiktok app
                self.d.app_start(APP_NAME)
                self.d.app_wait(APP_NAME, front=True)
                LOGGER.info("Started TikTok")

                try:
                    with self.d.session(APP_NAME) as sess:
                        # Click on the upload button
                        sess(text="Profile").wait()
                        LOGGER.info("Found profile")
                        self.click_with_random_offset(sess(text="Profile"))
                        sess(text="Following").wait()
                        # Switch account
                        self.switch_profile(lang)
                        if self.check_if_posted_tt(description):
                            break
                        self.d.app_wait(APP_NAME, front=True)
                        LOGGER.info("No upload found")
                        if not sess(text="Profile").exists:
                            LOGGER.info("no profile, going back")
                            self.d.press("back")
                            sleep(2)
                        LOGGER.info("waiting for profile")
                        sess(text="Profile").wait()
                        LOGGER.info("Found profile")
                        sleep(2)
                        (xi, yi) = sess(text="Profile").center()
                        LOGGER.info("Location of profile: %s, %s", xi, yi)
                        self.touch(0.5, yi / self.d.info.get("displayHeight", 1))
                        LOGGER.info("Clicked on Upload")
                        post_button_y = yi / self.d.info.get("displayHeight", 1)
                        LOGGER.info("Post button y: %s", post_button_y)
                        # Click on the gallery button
                        sess(description="Flash").wait()
                        self.touch(0.784, 0.76)
                        sleep(4)
                        LOGGER.info("Clicked on gallery")
                        # Fix multiple
                        sess(text="Select multiple").wait()
                        select_multiple = sess(text="Select multiple")
                        if (
                            select_multiple
                            and not self.d(className="android.widget.CheckBox").info[
                                "checked"
                            ]
                        ):
                            self.click_with_random_offset(select_multiple)

                        sleep(1)
                        LOGGER.info("Clicking on video")
                        tx, ty = sess(
                            className="android.widget.FrameLayout",
                            description="All",
                            selected=True,
                        ).center()

                        tx = tx / self.d.info.get("displayWidth", 1)
                        ty = ty * 2 / self.d.info.get("displayHeight", 1)
                        LOGGER.info("Location of video: %s, %s", tx, ty)

                        self.touch(tx, ty)

                        # Press Next
                        next_button = sess(text="Next").wait()
                        LOGGER.info("Next button")
                        if not next_button:
                            next_button = sess(text=f"Next ({1})")
                        if not next_button:
                            for text_view in sess(className="android.widget.TextView"):
                                if "Next" in text_view.text:
                                    text_view.wait()
                                    text_view.click()
                                    break
                        else:
                            sess(text="Next").click()

                        if sound:
                            self.add_sound_tt()

                        sleep(2)
                        # Press 'Next' button
                        sess(text="Next").wait()
                        sess(text="Next").click()
                        LOGGER.info("Clicked on next")
                        if description:
                            # Description
                            sess(className="android.widget.EditText").set_text(
                                description
                            )
                            LOGGER.info("Set description")
                            sleep(2)
                            # Press back button
                            self.d.press("back")
                            LOGGER.info("Pressed back")
                            sess(text=description).wait()
                        if only_me:
                            try:
                                sess(text="Everyone can view this post").wait()
                                sess(text="Everyone can view this post").click()
                                sess(text="Only you").wait()
                                sess(text="Only you").click()
                                sleep(1)
                                self.d.press("back")
                                sleep(2)
                            except Exception as e:
                                LOGGER.error(e)

                        if draft:
                            # Press 'Save' button
                            self.touch(0.28, post_button_y)
                            LOGGER.info("Clicked on draft")
                            sleep(2)
                            if sess(text="Profile").exists(timeout=5):
                                self.touch(0.28, post_button_y)
                        else:
                            # Press 'Post' button
                            self.touch(0.74, post_button_y)
                            LOGGER.info("Clicked on post")
                            sleep(2)
                            if sess(text="Profile").exists(timeout=5):
                                self.touch(0.74, post_button_y)

                        # Check if we got a prompt
                        try:
                            sess(text="Post Now").wait()
                            sess(text="Post Now").click()
                        except:
                            pass

                        # Wait until the upload is done
                        timout_time = 100
                        cur_time = 0
                        sleep(5)
                        if not sess(text="Home").exists(timeout=5):
                            self.touch(0.74, post_button_y)
                            sleep(2)
                        sess(text="Home").wait()
                        if sess(text="Home").info["selected"] is not True:
                            self.click_with_random_offset(sess(text="Home"))
                        while sess(resourceId="%s:id/hs0" % APP_NAME):
                            sleep(1)
                            cur_time += 1
                            if cur_time > timout_time:
                                break
                        sleep(60)
                        if only_me:
                            self.d.app_stop(APP_NAME)
                            break
                        if self.check_if_posted_tt(description):
                            self.d.app_stop(APP_NAME)
                            break
                        self.d.app_stop(APP_NAME)
                except SessionBrokenError as e:
                    LOGGER.error(e)
                    self.d.app_stop(APP_NAME)
                    continue

        except Exception as e:
            self.d.app_stop(APP_NAME)
            LOGGER.error(e)
            return False

        return True


if __name__ == "__main__":
    adb = ADBUploader()
    packages = adb.d.app_list()
    for package in POSSIBLE_APPS:
        if package in packages:
            APP_NAME = package
            break
    if not APP_NAME:
        APP_NAME = "com.zhiliaoapp.musically"
    adb.d.app_stop(APP_NAME)
    LOGGER.info("Stopped TikTok")
    ##############################
    if not APP_NAME:
        LOGGER.info("TikTok not found")

        # Start tiktok app
    adb.d.app_start(APP_NAME)
    adb.d.app_wait(APP_NAME, front=True)
    adb.click_with_random_offset(adb.d(text="Profile"))
    adb.switch_profile()
    adb.check_if_posted_tt(
        "AITAH for telling my girlfriend I told", dumpdo=True
    )  # test
    adb.d.app_stop(APP_NAME)
