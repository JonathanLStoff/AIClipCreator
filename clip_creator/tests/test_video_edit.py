import os
import shutil
import unittest
from unittest.mock import MagicMock, patch
from clip_creator.conf import CURSE_WORDS
from moviepy import VideoFileClip

from clip_creator.video_edit import (
    edit_vid_orchestrator,
    timestamps
)


class TestVideoEditor(unittest.TestCase):
    
    def test_censoring(self):
        id_v = "SXoQ5gJLJdY"
        start_time = 170.0
        end_time = 200.0
        out_put_file, transcript = edit_vid_orchestrator(
            id_v,
            f"test_files/{id_v}.mp4",
            f"test_files/clip_{id_v}.mp4",
            target_size=(1080, 1920),
            start_time=start_time,
            end_time=end_time,
            text="TEST FUCK SHIT",
        )
        curse_words = 0
        for part in transcript:
            if part['text'].lower() in CURSE_WORDS:
                curse_words += 1
        VideoFileClip(out_put_file).audio.write_audiofile(
            f"test_files/clip_{id_v}.mp3"
        )        
        # Check for Curse words in transcript output
        self.assertEqual(curse_words, 0)
        timestamps_obj = timestamps()
        transcript_segment = timestamps_obj.get_word_timestamps_openai(
            f"test_files/clip_{id_v}.mp3",
            audio_clip_length=end_time-start_time,
            time_add=0,
        )
        curse_words = 0
        for part in transcript_segment:
            if part['text'].lower() in CURSE_WORDS:
                curse_words += 1
        # Check for Curse words in video speech
        self.assertEqual(curse_words, 0)

if __name__ == "__main__":
    unittest.main()
