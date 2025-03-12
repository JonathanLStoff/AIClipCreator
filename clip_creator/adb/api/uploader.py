import uiautomator2 as u2
from time import sleep
import os,datetime,subprocess,json
from clip_creator.conf import LOGGER, ADB_DEVICE

# "Static" config
SD_CARD_INDEX = False
POSSIBLE_APPS = ['com.zhiliaoapp.musically', 'com.ss.android.ugc.trill']
RELATIVE_PATH = 'Pictures/TTUploader' # has to be it's own folder
class ADBUploader:
    def __init__(self):
        try:
            self.adb_raw("connect %s" % ADB_DEVICE)
            while True:
                LOGGER.debug('Waiting for device')
                out = self.adb_raw('devices')
                found_device = False
                for device in out.split('\n'):
                    LOGGER.debug(device)
                    LOGGER.debug( str(ADB_DEVICE.split(":")[0]) in str(device) )
                    LOGGER.debug( "device" in device )
                    if str(ADB_DEVICE.split(":")[0]) in str(device) and "device" in device:
                        LOGGER.debug('Device connected')
                        found_device = True
                        break
                LOGGER.debug(out)
                if found_device:
                    break
                sleep(5)
        except Exception as e:
            LOGGER.error(e)
        self.device_size = (0,0)    
        self.d = u2.connect(ADB_DEVICE)
        #self.adb(f'shell "rm {RELATIVE_PATH}/*"')

    def adb(self, command):
        LOGGER.info(f'Running command: {command}')
        proc = subprocess.Popen('adb -s %s %s' % (ADB_DEVICE, command), stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate()
        return out.decode('utf-8')
    def adb_raw(self, command):
        LOGGER.info(f'Running command: {command}')
        proc = subprocess.Popen(f'adb {command}', stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate()
        return out.decode('utf-8')
    
    def touch(self, x, y, relative=True):
        self.device_size
        # coords are in percentage
        if self.device_size[0] == 0:
            self.device_size = (self.d.info['displayWidth'], self.d.info['displayHeight'])
        LOGGER.info(f'Touching at {x}, {y}')
        x = int(x * self.device_size[0]) if relative else x
        y = int(y * self.device_size[1]) if relative else y
        self.d.click(x, y)

        
    def upload_tiktok(self, video_path:str="", tiktok_audio=None, original_audio=1, added_audio=1, draft=False, description=None, photo_mode=False, only_me=False):
        # Find app
        self.d.app_stop_all()
        packages = self.d.app_list()
        for package in POSSIBLE_APPS:
            if package in packages:
                APP_NAME = package
                break

        if not APP_NAME:
            LOGGER.info('TikTok not found')
            return


        # Delete old files on device
        self.d.shell('rm -rf /sdcard/%s' % RELATIVE_PATH)
        self.d.shell('mkdir /sdcard/%s' % RELATIVE_PATH)
        ITEM_COUNT = 1
        # Copy files to device
        base_file_name = os.path.basename(video_path)
        self.d.push(os.path.abspath(video_path), f"/sdcard/{RELATIVE_PATH}/{base_file_name}")
        # Call the media scanner to add the video to the media content provider
        # I don't know why it's like this, but for some reason the first one only works on my emulator
        if SD_CARD_INDEX:
            self.d.shell(f'am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d file:///sdcard/{RELATIVE_PATH}/{base_file_name}')
        else:
            self.d.shell(f'am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d file:///storage/emulated/0/{RELATIVE_PATH}/{base_file_name}')
        
        # Start tiktok app
        self.d.app_start(APP_NAME)
        self.d.app_wait(APP_NAME, front=True)
        LOGGER.info('Started TikTok')
        # Click on the upload button
        self.d(text='Profile').wait()
        LOGGER.info('Found profile')
        self.touch(0.5, 0.99)
        LOGGER.info('Waited on profile')
        # Click on the gallery button
        self.d(description='Flash').wait()
        self.touch(0.784, 0.916)
        LOGGER.info('Clicked on upload')
        select_multiple = self.d(text='Select multiple')
        if select_multiple and not self.d(className='android.widget.CheckBox').info['checked']:
            select_multiple.click()
        sleep(1)
        self.touch(0.169, 0.185)

        # Click on the first video
        # for i in range(ITEM_COUNT):
        #     element = self.d(className="androidx.recyclerview.widget.RecyclerView").child(className="android.widget.FrameLayout").child(className="android.widget.TextView")
            

        #     if i == ITEM_COUNT - 1:
        #         element.wait()
        #         element.click()
        #     else:
        #         element.click()

        # Press Next
        next_button = self.d(text='Next').wait()
        if not next_button:
            next_button = self.d(text='Next (%s)' % ITEM_COUNT)
        if not next_button:
            for text_view in self.d(className='android.widget.TextView'):
                if 'Next' in text_view.text:
                    text_view.wait()
                    text_view.click()
                    break
        else:
            self.d(text='Next').click()

        if photo_mode:
            if not self.d(text='Switch to video mode'):
                # Press "Switch to photo mode" button
                self.d(text='Switch to photo mode').click.wait()

        if tiktok_audio:
            # Click audio button
            for layout in self.d(className="android.widget.LinearLayout"):
                if layout.info['clickable']:
                    layout.click.wait()
                    break
            # Click magnifying glass
            self.d(className='android.widget.ImageView')[0].wait()
            self.d(className='android.widget.ImageView')[0].click()
            self.d(text='Search').set_text(tiktok_audio)
            self.d(text='Search').wait()
            self.d(text='Search').click()

            # Click first result
            first_result = self.d(className="androidx.recyclerview.widget.RecyclerView") \
                .child(className="android.widget.LinearLayout")
            first_result.child(index=0).click()

            sleep(0.2)

            # Press check button
            first_result.child(className="android.widget.LinearLayout") \
                .child(className="android.widget.LinearLayout").click.wait()

            if original_audio != 1 or added_audio != 1:
                # Press 'Volume' button
                self.d(text='Volume').wait()
                self.d(text='Volume').click()
                
                # "android.widget.SeekBar"
                # 0 = original audio
                # 1 = added audio

                def set_seekbar(seekbar, value):
                    target = seekbar.info['bounds']['left'] + ((seekbar.info['bounds']['right']-seekbar.info['bounds']['left']*0.985) * value)
                    height = seekbar.info['bounds']['bottom'] - seekbar.info['bounds']['top']
                    y = seekbar.info['bounds']['top'] + height / 2

                    self.d.click(target, y)

                # Set original audio volume
                set_seekbar(self.d(className='android.widget.SeekBar', instance=0), original_audio / 2)

                # Set added audio volume
                set_seekbar(self.d(className='android.widget.SeekBar', instance=1), added_audio / 2)

                #  Press 'Done' button
                self.d(text='Done').click.wait()
            else:
                # Press the back button
                self.d.press("back")
        sleep(2)
        # Press 'Next' button
        self.d(text='Next').wait()
        self.d(text='Next').click()
        LOGGER.info('Clicked on next')
        if description:
            # Description
            self.d(className='android.widget.EditText').set_text(description)
            # Press back button
            self.d.press("back")
            self.d(text=description).wait()
        if only_me:
            try:
                self.d(text='Everyone can view this post').wait()
                self.d(text='Everyone can view this post').click()
                self.d(text='Only you').wait()
                self.d(text='Only you').click()
                sleep(1)
                self.d.press("back")
                sleep(2)
            except Exception as e:
                LOGGER.error(e)

        if draft:
            # Press 'Save' button
            self.touch(0.28, 0.97)
        else:
            # Press 'Post' button
            self.touch(0.74, 0.97)

        # Check if we got a prompt
        try:
            self.d(text='Post Now').wait()
            self.d(text='Post Now').click()
        except:
            pass

        # Wait until the upload is done
        while self.d(resourceId='%s:id/hs0' % APP_NAME):
            sleep(1)
        #                  ^^^^^ THIS (maybe) NEEDS TO BE UPDATED
        # I can't find a quick and reliable way to check if the upload is done, feel free to make a PR