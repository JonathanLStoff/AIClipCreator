from clip_creator.conf import LOGGER, ADB_DEVICE, ADB_PATH, ADB_PATH_EXE, ADB_SHELL, POSSIBLE_TRANSLATE_LANGS_TTS
from clip_creator.adb.api.uploader import ADBUploader
import random
import uiautomator2 as u2
import threading
import time as tm
from datetime import datetime, timedelta, time
from tqdm import tqdm
import subprocess

SD_CARD_INDEX = False
POSSIBLE_APPS = ['com.zhiliaoapp.musically', 'com.ss.android.ugc.trill']
INSTA_APP = 'com.instagram.android'
YT_APP = 'com.google.android.youtube'
FB_APP = 'com.facebook.appmanager'

class ADBScroll:
    def __init__(self):
        try:
            self.adb_raw(["connect", ADB_DEVICE])
            
        except Exception as e:
            LOGGER.error(e)
        
        self.device_size = (0,0)  
        self.d = u2.connect(ADB_DEVICE)
        self.d.shell('input keyevent 82')
        self.d.shell('input keyevent 3')
        self.device_size = (self.d.info['displayWidth'], self.d.info['displayHeight'])
        self.running = True
        self.app_name = 'com.zhiliaoapp.musically'
        
    def scroll_tiktok(self, lang="en", max_time_hour=4, max_time_min=0):
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
            APP_NAME = 'com.zhiliaoapp.musically'
        self.d.app_stop(APP_NAME)
        self.app_name = APP_NAME
        if not APP_NAME:
            LOGGER.info('TikTok not found')
            return

        # Start tiktok app
        self.d.app_start(APP_NAME)
        self.d.app_wait(APP_NAME, front=True)
        tm.sleep(5)
        LOGGER.info('Started TikTok')
        self.d(text='Profile').wait()
        LOGGER.info('Found profile')
        self.d(text='Profile').click()
        self.d(text="Following").wait()
        if lang == "en":
            if not self.d(text="reddit_city_ai").exists(timeout=5):
                self.d(resourceId="com.zhiliaoapp.musically:id/kn4").click()
                self.d(text="reddit_city_ai").wait()
                self.d(text="reddit_city_ai").click()
        else:
            LOGGER.info('Changing language to %s', POSSIBLE_TRANSLATE_LANGS_TTS[lang])
            profile_name = POSSIBLE_TRANSLATE_LANGS_TTS[lang]['profile']
            profile_user = POSSIBLE_TRANSLATE_LANGS_TTS[lang]['username']
            if not self.d(text=profile_name).exists(timeout=5):
                self.d(resourceId="com.zhiliaoapp.musically:id/kn4").click()
                self.d(text=profile_user).wait()
                self.d(text=profile_user).click()
        
        self.d(text='Profile').wait()
        self.d(text='Home').click()
        th, tw = self.d.info['displayHeight'], self.d.info['displayWidth']
        swipe = {
            'x1': int(tw * 0.5),
            'y1': int(th * 0.8),
            'x2': int(tw * 0.5),
            'y2': int(th * 0.2),
        }
        while datetime.now() < end_time:
            LOGGER.info("Scrolling...")
            if datetime.now() > end_time or not self.running:
                LOGGER.info("time_stop: %s", end_time)
                break
            # Skip ads
            if self.d(text="Sponsored").exists(timeout=2):
                random_time = int(random.randint(1, 5))
                tm.sleep(random_time)
                self.d.swipe(
                            swipe['x1']+random.randint(1, 20),
                            swipe['y1']+random.randint(1, 20),
                            swipe['x2']+random.randint(1, 20),
                            swipe['y2']+random.randint(1, 20),
                            duration = 0.2
                        )
            random_time = int(random.randint(3, 142))
            random_sh = random.randint(1, 100)
            random_lk = random.randint(1, 100)
            tm.sleep(random_time)
            if random_sh < 80:
                LOGGER.info("Sharing video...")
                # Click share button
                self.d(resourceId="com.zhiliaoapp.musically:id/dw4", descriptionContains="Share video").wait()
                self.d(resourceId="com.zhiliaoapp.musically:id/dw4", descriptionContains="Share video").click()
                tm.sleep(random.randint(0, 3)+(random.randint(1, 100)/100))
                # Click copy link
                self.d(description="Copy link").wait()
                self.d(description="Copy link").click()
                tm.sleep(random.randint(0, 3)+(random.randint(1, 100)/100))
            if random_lk < 90:
                LOGGER.info("Liking video...")
                self.d(descriptionContains="Like video.").wait()
                self.d(descriptionContains="Like video.").click()
                tm.sleep(random.randint(0, 3)+(random.randint(1, 100)/100))
            # add comment?
            
            # Next Video
            self.d.swipe(
                            swipe['x1']+random.randint(1, 20),
                            swipe['y1']+random.randint(1, 20),
                            swipe['x2']+random.randint(1, 20),
                            swipe['y2']+random.randint(1, 20),
                            duration = 0.2
                        )
    def adb(self, command:list):
        command_list = [ADB_PATH_EXE, "-s", ADB_DEVICE]+command
        LOGGER.info(f'Running command: {command_list}')
        proc = subprocess.Popen(command_list, stdout=subprocess.PIPE, shell=ADB_SHELL)
        (out, err) = proc.communicate()
        return out.decode('utf-8')
    
    def adb_raw(self, command:list):
        command_list = [ADB_PATH_EXE] + command
        LOGGER.info(f'Running command: {command_list}')
        proc = subprocess.Popen(command_list, stdout=subprocess.PIPE, shell=ADB_SHELL)
        (out, err) = proc.communicate()
        return out.decode('utf-8')
    
    def adb_wait(self, command:list):
        command_list = [ADB_PATH_EXE]+command
        LOGGER.info(f'Running command: {command_list}')
        return subprocess.run(command_list, shell=ADB_SHELL, stdout=subprocess.PIPE).stdout.decode('utf-8')
    def adb_stri_command(self, command:list):
        command_list = [ADB_PATH_EXE]+command
        command_string = ' '.join(command_list)
        LOGGER.info(f'Running command: {command_string}')
        return subprocess.run(command_string, shell=True, stdout=subprocess.PIPE).stdout.decode('utf-8')
    
    def touch(self, x, y, relative=True):
        self.device_size
        # coords are in percentage
        if self.device_size[0] == 0:
            self.device_size = (self.d.info['displayWidth'], self.d.info['displayHeight'])
        LOGGER.info(f'Touching at {x}, {y}')
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
        
if __name__ == "__main__":
    adb = ADBScroll()
    adb_thread = threading.Thread(target=adb.scroll_tiktok)
    adb_thread.start()
    tm.sleep(100)
    LOGGER.info("Stopping...")
    adb_thread.join()  # Wait for the thread to finish
    adb.running = False
    LOGGER.info("Stopped.")
    