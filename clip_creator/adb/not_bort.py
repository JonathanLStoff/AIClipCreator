import logging
import random
import subprocess
import threading
import time as tm
from time import sleep
from datetime import datetime, timedelta
from uiautomator2.exceptions import SessionBrokenError

import uiautomator2 as u2

from clip_creator.conf import (
    ADB_DEVICE,
    ADB_PATH_EXE,
    ADB_SHELL,
    LOGGER,
    POSSIBLE_TRANSLATE_LANGS_TTS,
)

SD_CARD_INDEX = False
POSSIBLE_APPS = ["com.zhiliaoapp.musically", "com.ss.android.ugc.trill"]
INSTA_APP = "com.instagram.android"
YT_APP = "com.google.android.youtube"
FB_APP = "com.facebook.appmanager"


class ADBScroll:
    def __init__(self):
        try:
            self.adb_raw_non_blocking(["connect", ADB_DEVICE])

        except Exception as e:
            LOGGER.error(e)

        self.device_size = (0, 0)
        LOGGER.info("Connecting to device...")
        self.d = u2.connect(ADB_DEVICE)
        self.d.shell("input keyevent 82")
        try:
            self.d.shell(["settings", "put", "system", "screen_brightness", "1"])
        except Exception as e:
            LOGGER.error(e)

        self.d.shell("input keyevent 3")
        self.device_size = (self.d.info["displayWidth"], self.d.info["displayHeight"])
        self.running = True
        self.app_name = "com.zhiliaoapp.musically"
        file_handler = logging.FileHandler("logs/scroll_runner.log")
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )
        LOGGER.addHandler(file_handler)
        LOGGER.info("Running Scrolling task...")

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
        if self.d(textContains="Not").exists(timeout=5):
            self.d(textContains="Not").click()
            sleep(2)
        while curr_tries < max_tries:
            try:
                if self.d(textContains="Sign up").exists(timeout=5):
                    self.d.press("back")
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
                    if self.d(textContains="Sign up").exists(timeout=5):
                        self.d.press("back")
                    if self.d(textStartsWith="Reddit").exists(timeout=5):
                        self.click_with_random_offset(self.d(textStartsWith="Reddit"))
                    elif self.d(textContains="@").exists(timeout=5):
                        _, aty = self.d(textContains="@").center()
                        adat_y = (aty / self.d.info.get("displayHeight", 1)) -0.025
                        self.touch(0.5, adat_y)
                    elif self.d(resourceId="com.zhiliaoapp.musically:id/kn4").exists(timeout=5):
                        self.click_with_random_offset(
                            self.d(resourceId="com.zhiliaoapp.musically:id/kn4")
                        )
                    else:
                        self.touch(0.5, 0.075)
                    if self.d(textContains="Sign up").exists(timeout=5):
                        self.d.press("back")
                    self.d(textContains=username).wait()
                    if self.d(textContains=username).exists(timeout=5):
                        self.click_with_random_offset(self.d(textContains=username))
                    elif self.d(descriptionContains=username).exists(timeout=5):
                        self.click_with_random_offset(self.d(descriptionContains=username))
                    if self.d(textContains="Sign up").exists(timeout=5):
                        self.d.press("back")
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

    def scroll_tiktok(self, lang="en", max_time_hour=2, max_time_min=0):
        if max_time_min > 0:
            end_time = datetime.now() + timedelta(minutes=max_time_min)
        else:
            end_time = datetime.now() + timedelta(hours=max_time_hour)
        # This is a failsafe, not a timer
        packages = self.d.app_list()
        for package in POSSIBLE_APPS:
            if package in packages:
                APP_NAME = package
                break
        if not APP_NAME:
            APP_NAME = "com.zhiliaoapp.musically"
        self.d.app_stop(APP_NAME)
        self.app_name = APP_NAME
        if not APP_NAME:
            LOGGER.info("TikTok not found")
            return

        # Start tiktok app
        self.d.app_start(APP_NAME)
        self.d.app_wait(APP_NAME, front=True)
        tm.sleep(5)
        LOGGER.info("Started TikTok")
        if not self.d(text="Profile").exists(timeout=5):
            LOGGER.info("Profile not found")
            if self.d(text="Skip").exists(timeout=5):
                self.click_with_random_offset(self.d(text="Skip"))
                if self.d(text="Skip").exists(timeout=5):
                    self.click_with_random_offset(self.d(text="Skip"))
            if self.d(text="Skip").exists(timeout=5):
                self.click_with_random_offset(self.d(text="Skip"))
            if self.d(text="Done").exists(timeout=5):
                self.click_with_random_offset(self.d(text="Done"))
        self.d(text="Profile").wait()
        LOGGER.info("Found profile")
        self.d(text="Profile").click()
        self.d(text="Following").wait()
        self.switch_profile(lang=lang)

        self.d(text="Profile").wait()
        self.d(text="Home").click()
        th, tw = self.d.info["displayHeight"], self.d.info["displayWidth"]
        swipe = {
            "x1": int(tw * 0.5),
            "y1": int(th * 0.8),
            "x2": int(tw * 0.5),
            "y2": int(th * 0.2),
        }
        error_count = 0
        while datetime.now() < end_time:
            try:
                LOGGER.info("Scrolling...")
                if datetime.now() > end_time or not self.running:
                    LOGGER.info("time_stop: %s", end_time)
                    break
                # Skip ads and live streams
                if self.d(text="Sponsored").exists(timeout=2) or not self.d(
                    text="Like video."
                ).exists(timeout=2):
                    random_time = int(random.randint(1, 5))
                    tm.sleep(random_time)
                    self.d.swipe(
                        swipe["x1"] + random.randint(1, 20),
                        swipe["y1"] + random.randint(1, 20),
                        swipe["x2"] + random.randint(1, 20),
                        swipe["y2"] + random.randint(1, 20),
                        duration=0.2,
                    )
                random_time = int(random.randint(3, 142))
                random_sh = random.randint(1, 100)
                random_lk = random.randint(1, 100)
                tm.sleep(random_time)
                if random_sh < 80:
                    LOGGER.info("Sharing video...")
                    # Click share button
                    if self.d(
                            descriptionContains="Share video",
                        ).exists(timeout=5):
                        self.d(
                            descriptionContains="Share video",
                        ).wait()
                        self.d(
                            descriptionContains="Share video",
                        ).click()
                    elif self.d(text="Share").exists(timeout=5):
                        self.d(text="Share").wait()
                        self.d(text="Share").click()
                    tm.sleep(random.randint(0, 3) + (random.randint(1, 100) / 100))
                    # Click copy link
                    self.d(description="Copy link").wait()
                    self.d(description="Copy link").click()
                    tm.sleep(random.randint(0, 3) + (random.randint(1, 100) / 100))
                if random_lk < 90:
                    LOGGER.info("Liking video...")
                    self.d(descriptionContains="Like video.").wait()
                    self.d(descriptionContains="Like video.").click()
                    tm.sleep(random.randint(0, 3) + (random.randint(1, 100) / 100))
                # add comment?

                # Next Video
                self.d.swipe(
                    swipe["x1"] + random.randint(1, 20),
                    swipe["y1"] + random.randint(1, 20),
                    swipe["x2"] + random.randint(1, 20),
                    swipe["y2"] + random.randint(1, 20),
                    duration=0.01 + (random.randint(1, 100) / 1000),
                )
            except Exception as e:
                LOGGER.error(e)
                error_count += 1
                if error_count > 10:
                    break
                try:
                    self.d(text="Home").click()
                except Exception as x:
                    LOGGER.error(x)
                    self.d.app_stop(APP_NAME)
                    self.d.app_start(APP_NAME)
                    self.d.app_wait(APP_NAME, front=True)
                    tm.sleep(5)
                continue
        self.d.app_stop(APP_NAME)

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
    def adb_raw_non_blocking(self, command: list):
        """
        Runs an ADB command without waiting for its completion and ignores the output.
        """
        command_list = [ADB_PATH_EXE, *command]
        LOGGER.info(f"Running command (non-blocking): {command_list}")
        subprocess.Popen(command_list, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=ADB_SHELL)
        # We don't call communicate() or wait(), so the function returns immediately.
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

    def stop(self):
        self.running = False

    def kill_apps(self):
        self.d.app_stop(self.app_name)
        self.d.app_stop(INSTA_APP)
        self.d.app_stop(YT_APP)
        self.d.app_stop(FB_APP)
        self.close_all()

    def close_all(self):
        self.d.stop_uiautomator()


if __name__ == "__main__":
    adb = ADBScroll()
    adb_thread = threading.Thread(target=adb.scroll_tiktok)
    adb_thread.start()
    tm.sleep(100)
    LOGGER.info("Stopping...")
    adb_thread.join()  # Wait for the thread to finish
    adb.running = False
    LOGGER.info("Stopped.")
