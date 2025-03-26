import unittest

from moviepy import VideoFileClip

from clip_creator.conf import CURSE_WORDS
from clip_creator.vid_ed.video_edit import edit_vid_orchestrator, timestamps


class TestVideoEditor(unittest.TestCase):
    def test_censoring(self):
        id_v = "SXoQ5gJLJdY"
        start_time = 157
        end_time = 220
        transcript = [
            {
                "text": "stuck down we got to figure out what",
                "start": 157.959,
                "duration": 3.121,
            },
            {
                "text": "went wrong some animals are loose watch",
                "start": 159.04,
                "duration": 4.479,
            },
            {
                "text": "out for the animals yeah okay wait I",
                "start": 161.08,
                "duration": 5.12,
            },
            {
                "text": "found a healing syringe wait highy guys",
                "start": 163.519,
                "duration": 5.201,
            },
            {
                "text": "you want to see me shoot this up oh [\u00a0__\u00a0]",
                "start": 166.2,
                "duration": 4.52,
            },
            {"text": "oh [\u00a0__\u00a0]", "start": 168.72, "duration": 6.32},
            {
                "text": "oh oh [\u00a0__\u00a0] me when I just learned how to",
                "start": 170.72,
                "duration": 8.159,
            },
            {
                "text": "swear okay fair enough Val anyway drug",
                "start": 175.04,
                "duration": 6.64,
            },
            {"text": "time", "start": 178.879, "duration": 7.041},
            {
                "text": "oh what the [\u00a0__\u00a0] open Silo 3 to retrieve",
                "start": 181.68,
                "duration": 6.919,
            },
            {
                "text": "power cells that's what we need to do",
                "start": 185.92,
                "duration": 4.679,
            },
            {
                "text": "okay okay are we going to survive",
                "start": 188.599,
                "duration": 4.56,
            },
            {
                "text": "getting there I don't know check my give",
                "start": 190.599,
                "duration": 4.161,
            },
            {
                "text": "me a second sorry sorry I was being a",
                "start": 193.159,
                "duration": 3.201,
            },
            {
                "text": "piece of [\u00a0__\u00a0] damn this thing takes",
                "start": 194.76,
                "duration": 3.96,
            },
            {
                "text": "hours to swing oh my God you almost ran",
                "start": 196.36,
                "duration": 3.92,
            },
            {
                "text": "into that because they were watching me",
                "start": 198.72,
                "duration": 2.599,
            },
            {
                "text": "I think we just have to do the level",
                "start": 200.28,
                "duration": 2.959,
            },
            {
                "text": "three thing why is he dying still with",
                "start": 201.319,
                "duration": 5.64,
            },
            {
                "text": "that see we have to go fine everybody on",
                "start": 203.239,
                "duration": 4.72,
            },
            {"text": "the", "start": 206.959, "duration": 3.36},
            {"text": "lift this is", "start": 207.959, "duration": 4.721},
            {
                "text": "on this this thing here it says to take",
                "start": 210.319,
                "duration": 5.2,
            },
            {
                "text": "iodine and I have it so I'm going to try",
                "start": 212.68,
                "duration": 4.6,
            },
            {
                "text": "and taking iodine and entering this",
                "start": 215.519,
                "duration": 2.881,
            },
            {"text": "thing", "start": 217.28, "duration": 3.319},
        ]
        ft_transcript = ""
        for part in transcript:
            ft_transcript += part["text"] + " "
        out_put_file, transcript = edit_vid_orchestrator(
            id_v,
            f"test_files/{id_v}.mp4",
            f"test_files/clip_{id_v}.mp4",
            target_size=(1080, 1920),
            start_time=start_time,
            end_time=end_time,
            text="TEST FUCK SHIT",
            ft_transcript=ft_transcript,
        )
        curse_words = 0
        for part in transcript:
            if part["text"].lower() in CURSE_WORDS:
                curse_words += 1
        VideoFileClip(out_put_file).audio.write_audiofile(f"test_files/clip_{id_v}.mp3")
        # Check for Curse words in transcript output
        self.assertEqual(curse_words, 0)
        timestamps_obj = timestamps()
        transcript_segment = timestamps_obj.get_word_timestamps_openai(
            f"test_files/clip_{id_v}.mp3",
            audio_clip_length=end_time - start_time,
            time_add=0,
        )
        curse_words = 0
        for part in transcript_segment:
            if part["text"].lower() in CURSE_WORDS:
                curse_words += 1
        # Check for Curse words in video speech
        self.assertEqual(curse_words, 0)


if __name__ == "__main__":
    unittest.main()
