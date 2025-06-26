import datetime
import os
import random
import subprocess
from time import sleep
from tqdm import tqdm
import uiautomator2 as u2
from uiautomator2.exceptions import SessionBrokenError
from clip_creator.utils.scan_text import remove_non_letterstwo
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
            self.adb_raw_non_blocking(["connect", ADB_DEVICE])

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
    def adb_raw_non_blocking(self, command: list):
        """
        Runs an ADB command without waiting for its completion and ignores the output.
        """
        command_list = [ADB_PATH_EXE, *command]
        LOGGER.info(f"Running command (non-blocking): {command_list}")
        subprocess.Popen(command_list, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=ADB_SHELL)
        # We don't call communicate() or wait(), so the function returns immediately.
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
        LOGGER.info("Started Youtube")
        self.d(text="Subscriptions").wait()
        (xi, yi) = self.d(text="Subscriptions").center()
        ad_yi = yi / self.d.info.get("displayHeight", 1)
        # Just touch the upload
        self.touch(0.5, ad_yi)
        LOGGER.info("Clicked on upload")
        sleep(2)  # Give it a moment to load the upload screen
        # Check if start over
        if self.d(textContains="Start").exists(timeout=5):
            
            self.click_with_random_offset(
                self.d(textContains="Start")
            )
            LOGGER.info("Clicked on Start to start over")
        
        self.d(text="Add").wait()
        addx, addy = self.d(text="Add").center()  # Find the add button, this is where we will start the upload from
        self.d(text="Add").click()
        LOGGER.info("Clicked on add")
        # Touch the video
        if self.d(text="Create").exists(timeout=5):
            self.d(text="Create").wait()
            ad_x = (self.d.info.get("displayWidth", 1) / 3) / 2
            (xi, yi) = self.d(descriptionContains="Create").center()
            ad_y = yi * 2
            self.touch(
                ad_x / self.d.info.get("displayWidth", 1),
                ad_y / self.d.info.get("displayHeight", 1),
            )
            LOGGER.info("Clicked on vid and adjusted for create")
        elif self.d(text="Gallery").exists(timeout=5):
            self.d(text="Gallery").wait()
            ad_x = (self.d.info.get("displayWidth", 1) / 3) / 2
            (xi, yi) = self.d(description="Gallery").center()
            ad_y = yi * 4
            self.touch(
                ad_x / self.d.info.get("displayWidth", 1),
                ad_y / self.d.info.get("displayHeight", 1),
            )
            LOGGER.info("Clicked on vid and adjusted for no create")
        
        sleep(2)  # Give it a moment to load the video
        
        if self.d(text="Select").exists(timeout=5):
        
        if self.d(text="Next").exists(timeout=5):
            self.click_with_random_offset(self.d(text="Next"))
        LOGGER.info("Clicked on next")
        sleep(4)  # Give it a moment to load the video
        if self.d(text="Done").exists(timeout=5):
            self.click_with_random_offset(self.d(text="Done"))
        sleep(2)  # Give it a moment to load the video
        if self.d(text="Done").exists(timeout=5):
            self.click_with_random_offset(self.d(text="Done"))
        for i in tqdm(range(8), desc="Waiting for upload to process", unit="s"):
            sleep(10)  # wait for the upload to process, this can take a while on slow connections
        
        if self.d(text="Add").exists(timeout=60):
            (xi, yi) = self.d(text="Add").center()
            ad_x = self.d.info.get("displayWidth", 1) - xi
            self.touch(
                ad_x / self.d.info.get("displayWidth", 1),
                yi / self.d.info.get("displayHeight", 1),
            )
            LOGGER.info("Found add")
        elif self.d(descriptionContains="Add Sound").exists(timeout=60):
            #self.click_with_random_offset(self.d(descriptionContains="Add Sound"))
            self.touch((self.d.info.get("displayWidth", 1)-(addx/2))/self.d.info.get("displayWidth", 1), addy/ self.d.info.get("displayHeight", 1))  # Click in the middle of the screen to avoid issues with the keyboard
        else:
            LOGGER.info("SOMETHING IS WRONG WE ARE NOT IN THE ADD SCREEN")
        

        
        if self.d(text="Next").exists(timeout=10):
            
            self.click_with_random_offset(self.d(text="Next"))
        else:
            LOGGER.error("Next button not found")
            xml = self.d.dump_hierarchy()
            with open("logs/error_dump_yt.xml", "w", encoding="utf-8") as f:
                f.write(xml)
        sleep(2)  # Give it a moment to process the upload before we set the title/description
        dsc_parx, dsc_pary = self.d(text="Caption your Short").center()  # Find the parent of the caption text box, will need this later
        if self.d(descriptionContains="#").exists(timeout=5):
             correct_vis_y = (dsc_pary * 3.8) / self.d.info.get("displayHeight", 1)  # Get the y coordinate of the caption box, this is where we will click to enter the description
        else:
            correct_vis_y = (dsc_pary * 3) / self.d.info.get("displayHeight", 1)  # Get the y coordinate of the caption box, this is where we will click to enter the description
        pub_vis_y  = (dsc_pary * 1.6) / self.d.info.get("displayHeight", 1)
        if description:
            
            self.d(text="Caption your Short").set_text(self.format_yt_desc(description))
            self.d.press("back")
        
        
        if only_me:
            
            if self.d(text="Private").exists(timeout=3):
                self.d.press("back")
            else:
                LOGGER.info("Setting privacy to Private")
                self.touch(dsc_parx/self.d.info.get("displayWidth") ,correct_vis_y)
                sleep(2)
                self.touch(dsc_parx/self.d.info.get("displayWidth") ,correct_vis_y)
                self.d.press("back")
            sleep(2)
        elif self.d(text="Private").exists(timeout=3):
            self.d(text="Private").wait()
            self.d(text="Private").click()
            self.d(text="Public").wait()
            self.d(text="Public").click()
            self.d.press("back")
            sleep(2)
        else:
            self.touch(dsc_parx/self.d.info.get("displayWidth") , correct_vis_y)
            sleep(2)
            self.touch(dsc_parx/self.d.info.get("displayWidth") , pub_vis_y)
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
        for i in tqdm(range(30), desc="Waiting for upload to finish, takes about 4 mins", unit="s"):
            sleep(8)
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
        sleep(2)
        if self.d(text="Start new video").exists(timeout=3):
            self.d(text="Start new video").click()
        
        self.d(text="POST").wait()
        if self.d(text="POST").info["selected"]:
            self.click_with_random_offset(self.d(text="REEL"))
            
        if self.d(textContains="STORY").exists(timeout=5):
            self.click_with_random_offset(self.d(text="REEL"))
        if self.d(text="REEL").exists(timeout=5):
            if not self.d(text="REEL").info["selected"]:
                xml = self.d.dump_hierarchy()
                with open("logs/error_dump_insta_noreel.xml", "w", encoding="utf-8") as f:
                    f.write(xml)
                LOGGER.info("COULD NOT SELECT REEL")
                self.click_with_random_offset(self.d(text="REEL"))
                
        sleep(2)
        if self.d(text="Start new video").exists(timeout=3):
            self.d(text="Start new video").click()
        if self.d(text="Recents").exists(timeout=5):
            
            # Click on recents to select the video from the gallery
            LOGGER.info("Selecting from recents")
            rex, rey = self.d(text="Recents").center()
            rey_n = rey * 1.2
            self.touch(rex/self.d.info.get("displayWidth",1), rey_n/self.d.info.get("displayHeight", 1)) 
            
        
        elif self.d(textContains="Recents").exists(timeout=5): # May have a different name so we check for the text
            # Click on recents to select the video from the gallery
            LOGGER.info("Selecting from contains recents")
            rex, rey = self.d(textContains="Recents").center()
            rey_n = rey * 1.3
            self.touch(rex/self.d.info.get("displayWidth",1), rey_n/self.d.info.get("displayHeight", 1))
        elif self.d(text="Templates").exists(timeout=5):
            LOGGER.info("Found templates")
            _, templatey = self.d(text="Templates").center()
            self.touch(0.5, (templatey * 2) / self.d.info.get("displayHeight", 1))
        # self.d(resourceId='com.instagram.android:id/gallery_grid_item_bottom_container', instance=0).wait()
        # self.d(resourceId='com.instagram.android:id/gallery_grid_item_bottom_container', instance=0).click()
        sleep(5)  # Give it a moment to load the video
        # if self.d(textContains='no').exists(timeout=5):
        #     self.click_with_random_offset(self.d(textContains='no'))
        if self.d(text="Next").exists(timeout=5):
            self.click_with_random_offset(self.d(text="Next"))
            LOGGER.info("Clicked on next")
        if self.d(text="Next").exists(timeout=5):
            try:
                self.click_with_random_offset(self.d(text="Next"))
            except Exception as e:
                LOGGER.error("Error clicking on next %s", e)
            LOGGER.info("Clicked on next")
        if self.d(description="Next").exists(timeout=5):
            try:
                self.click_with_random_offset(self.d(description="Next"))
            except Exception as e:
                LOGGER.error("Error clicking on next %s", e)
        if description:
            sleep(2)  # Give it a moment to process the upload before we set the title/description
            if self.d(
                resourceId="com.instagram.android:id/caption_input_text_view"
            ).exists(timeout=5):
                # Click on the caption box to enter the description
                
                self.d(
                    resourceId="com.instagram.android:id/caption_input_text_view"
                ).set_text(description)
            elif self.d(className="android.widget.AutoCompleteTextView").exists(timeout=5):
                # Click on the caption box to enter the description
                
                self.d(className="android.widget.AutoCompleteTextView").set_text(description)
            self.d.press("back")
        # not working on current account
        if only_me and photo_mode:
            self.d(text="Audience").wait()
            self.click_with_random_offset(self.d(text="Audience"))
            self.d(text="Close Friends").wait()
            self.click_with_random_offset(self.d(text="Close Friends"))
            self.d.press("back")
        sleep(2)
        if draft:
            self.d(text="Save draft").wait()
            self.click_with_random_offset(self.d(text="Save draft"))
        else:
            if self.d(description="GIF Keyboard").exists(timeout=5):
                self.d.press("back")
            if self.d(text="Next").exists(timeout=5):
                self.click_with_random_offset(self.d(text="Next"))
            elif self.d(text="Share").exists(timeout=5):
                try:
                    self.click_with_random_offset(self.d(text="Share"))
                except Exception as e:
                    
                    LOGGER.error("Error clicking on share %s", e)
            else:
                xml = self.d.dump_hierarchy()
                with open("logs/error_dump_insta.xml", "w", encoding="utf-8") as f:
                    f.write(xml)
                LOGGER.info("Error finding share")
                
                self.d.press("back")
                self.click_with_random_offset(self.d(text="Share"))
            
        timeout_time = datetime.datetime.now() + datetime.timedelta(minutes=5)
        
        LOGGER.info("Waiting for upload to finish")
        if self.d(text="Sharing to Reels…").exists(timeout=3):
            while self.d(text="Sharing to Reels…").exists(timeout=3):
                sleep(1)
                if datetime.datetime.now() > timeout_time:
                    LOGGER.info("Breaking, timeout")
                    break
        elif self.d(resourceId="com.instagram.android:id/row_pending_container").exists(timeout=3):
            # For pending uploads, wait until it disappears
            LOGGER.info("Waiting for pending upload to finish")
            while self.d(resourceId="com.instagram.android:id/row_pending_container").exists(timeout=3):
                
                sleep(1)
                if datetime.datetime.now() > timeout_time:
                    LOGGER.info("Breaking, timeout")
                    break
        else:
            LOGGER.info("Cannot find upload status, assuming upload will take 4 mins")
            sleep(60*7)  # Sleep for 7 minutes to allow the upload to finish, this is a fallback in case the status is not found

        LOGGER.info("Done uploading, stopping app")
        sleep(2)
        self.d.app_stop(INSTA_APP)

    def add_location_insta(self):
        try:
            if self.d(text="Location").exists(timeout=5):
                self.d(text="Location").click()
                sleep(2)
                
            if self.d(textContains="Search").exists(timeout=5):
                self.d(textContains="Search").set_text(
                                    "united states"
                                )
            if self.d(text="United States").exists(timeout=5):
                self.click_with_random_offset(self.d(text="United States"))
                sleep(2)
            if self.d(description="GIF Keyboard").exists(timeout=5):
                if self.d(text="USA").exists(timeout=5):
                    self.click_with_random_offset(self.d(text="USA"))
                elif self.d(text="Orlando").exists(timeout=5):
                    self.click_with_random_offset(self.d(text="Orlando"))
        except Exception as e:
            LOGGER.error("Error adding location: %s", e)
            xml = self.d.dump_hierarchy()
            with open("logs/error_dump_tikloc.xml", "w", encoding="utf-8") as f:
                f.write(xml)
        if self.d(text="Retry").exists(timeout=5):
            LOGGER.info("Found retry prompt, bad location")
            self.d.press("back")

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
    def format_yt_desc(self, text:str)->str:
        """
        Youtube's max description length is 100 characters, this will format the description to fit within that limit
        """
        fixed_text = ""
        idxs = 0
        split_text = text.split()
        for i, word in enumerate(split_text):
            if "#" in word:
                idxs = i
                break
        split_text = split_text[idxs:]
        
        for i, word in enumerate(split_text):
            if len(fixed_text) + len(word) + 1 <= 100:
                if i == 0:
                    fixed_text += word
                else:
                    fixed_text += " " + word
            else:
                # If adding the next word would exceed the limit, stop adding
                break
        return fixed_text
        
        
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
                elif self.d(text="More insights").exists(timeout=5):
                    # Click on more insights to get the description
                    
                    self.click_with_random_offset(
                        self.d(descriptionContains="Read or add comments.")
                    )
                sleep(2)
                if dumpdo:
                    dump()
                    sleep(2)
                # Get text from description and check if it matches
                num_words = 5 if len(description.replace("\n", "").split()) > 5 else -1
                LOGGER.info("Checking description with %s words", num_words)
                part_desc = remove_non_letterstwo((
                    " ".join(description.replace("\n", "").split()[:num_words])
                    .encode("ascii", "ignore")
                    .decode("ascii")
                ))
                LOGGER.info("Part desc: %s", part_desc)
                if self.d(
                    resourceId="com.zhiliaoapp.musically:id/desc", instance=0
                ).exists(timeout=5):
                    text_decs = remove_non_letterstwo(
                        self.d(
                            resourceId="com.zhiliaoapp.musically:id/desc", instance=0
                        )
                        .info["text"]
                        .encode("ascii", "ignore")
                        .decode("ascii")
                    ).replace("\n", "")
                    LOGGER.info('resourceId="com.zhiliaoapp.musically:id/desc"')
                elif self.d(textStartsWith=part_desc).exists(timeout=5):
                    return True
                else:
                    try:
                        text_decs = remove_non_letterstwo(
                            self.d(resourceId="com.zhiliaoapp.musically:id/dsy", index=0)
                            .child(index=0)
                            .info["text"]
                            .encode("ascii", "ignore")
                            .decode("ascii")
                        ).replace("\n", "")
                        LOGGER.info('resourceId="com.zhiliaoapp.musically:id/dsy"')
                    except Exception as e:
                        LOGGER.error(e)
                        return True
                LOGGER.info("Description: %s", text_decs)
                returnsz = False
                if part_desc.lower().replace(" ", "") not in text_decs.lower().replace(" ", ""):
                    LOGGER.info("%s not in %s", part_desc.lower().replace(" ", ""), text_decs.lower().replace(" ", ""))
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
                        if sess(text="Skip").exists(timeout=5):
                            self.click_with_random_offset(sess(text="Skip"))
                            if sess(text="Skip").exists(timeout=5):
                                self.click_with_random_offset(sess(text="Skip"))
                        if sess(text="Skip").exists(timeout=5):
                            self.click_with_random_offset(sess(text="Skip"))
                        if sess(text="Done").exists(timeout=5):
                            self.click_with_random_offset(sess(text="Done"))    
                            
                        if sess(text="Profile").exists(timeout=5):
                        
                            LOGGER.info("Found profile")
                            self.click_with_random_offset(sess(text="Profile"))
                        elif sess(text="Next").exists(timeout=5):
                            self.d.press("back")
                            sleep(2)
                            self.d.press("back")
                            sleep(2)
                            self.d.press("back")
                            sleep(2)
                            LOGGER.info("Found profile")
                            self.click_with_random_offset(sess(text="Profile"))
                        sess(text="Following").wait()
                        if sess(text="Cancel").exists(timeout=5):
                            sess(text="Cancel").click()
                            sleep(2)
                            
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
                        
                        # Make sure we are on 60s mode so no sound is added
                        if sess(text="60s").exists(timeout=5):
                            if not sess(text="60s").info["selected"]:
                                LOGGER.info("Selecting 60s mode")
                                sess(text="60s").click()
                                
                        # Remove sound if it exists
                        if not sess(text="Add sound").exists(timeout=5):
                            sess(descriptionContains="Remove sound").click()
                            
                        # Click on the gallery button
                        sess(description="Flash").wait()
                        if sess(text="TEXT").exists(timeout=5):
                            _, texty = sess(text="TEXT").center()
                            tempx, tempy = sess(text="TEMPLATES").center()
                            ty = texty + ((tempy - texty)/3 )
                            livex, _ = sess(text="LIVE").center()
                            tx = ((livex - tempx) / 2) + tempx
                            typerc = ty / self.d.info.get("displayHeight", 1)
                            txperc = tx / self.d.info.get("displayWidth", 1)
                            self.touch(txperc, typerc)
                        else:
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
                        sleep(10)
                        if sess(textContains="Next").exists(timeout=5) and not sess(
                            text="Next"
                        ):
                            LOGGER.info("Clicking on next")
                            self.click_with_random_offset(sess(textContains="Next"))
                    
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
                        if sess(text="Next").exists(timeout=5):
                            LOGGER.info("Clicking on next")
                            self.click_with_random_offset(sess(text="Next"))
                
                        LOGGER.info("Clicked on next")
                        if description:
                            # Description
                            sess(className="android.widget.EditText").set_text(
                                description
                            )
                            LOGGER.info("Set description")
                            sleep(2)
                            # Press back button
                            if sess(description="GIF Keyboard").exists(timeout=5):
                                self.d.press("back")
                                LOGGER.info("Pressed back")
                                sleep(2)
                                if sess(text="Next").exists(timeout=5):
                                    sess(text="Next").click()
                                    
                            #sess(text=description).wait()
                        self.add_location_insta()
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
                            if sess(text="Post Now").exists(timeout=5):
                                LOGGER.info("Found post now prompt")
                                sess(text="Post Now").click()
                            elif sess(text="Retry").exists(timeout=5):
                                LOGGER.info("Found retry prompt")
                                sess(text="Retry").click()
                        except:
                            LOGGER.info("No post now prompt")
                            xml = self.d.dump_hierarchy()
                            with open("logs/error_dump_tik.xml", "w", encoding="utf-8") as f:
                                f.write(xml)
                        LOGGER.info("Clicked on post now")
                        
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
            xml = self.d.dump_hierarchy()
            with open("logs/error_dump_tikful.xml", "w", encoding="utf-8") as f:
                f.write(xml)
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
