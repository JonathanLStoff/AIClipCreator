from instabot import Bot

from clip_creator.conf import TIKTOK_PASSWORD, TIKTOK_USERNAME


class InstaGramUp:
    def __init__(self):
        self.bot = Bot()
        self.bot.login(
            username=TIKTOK_USERNAME, password=TIKTOK_PASSWORD, use_cookie=False
        )

    def upload_to_insta(self, v_path, caption):
        self.bot.upload_video(v_path, caption=caption)

    def logout(self):
        self.bot.logout()
