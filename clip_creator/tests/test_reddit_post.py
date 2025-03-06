from unittest import TestCase
from reddit_post import main_reddit_posts_orch
import sys
import os
from clip_creator.social.custom_tiktok import upload_video_tt
from clip_creator.conf import CLIPS_FOLDER
from datetime import datetime, timedelta

class TestDryRun(TestCase):
    
    def test_dry_run(self):
        original_argv = sys.argv[:]
        sys.argv = [sys.argv[0], '--dryrun']
        try:
            main_reddit_posts_orch()
        except SystemExit as e:
            self.assertEqual(e.code, 0)
        finally:
            sys.argv = original_argv
    def test_tt_upload(self):
        self.assertEqual(upload_video_tt(
                os.path.abspath(CLIPS_FOLDER+"/reddit_1j2s83l.mp4"),
                None,
                "Test Title",
                submit=False
            )["status"], "success")
