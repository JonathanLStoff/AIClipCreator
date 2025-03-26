import unittest
from unittest.mock import MagicMock, patch

# File: clip_creator/vid_ed/test_red_vid_edit.py
from clip_creator.vid_ed.red_vid_edit import (
    create_captions,
    create_postimg_clip,
    get_audio_duration,
    get_clip_duration,
)


class TestRedVidEdit(unittest.TestCase):
    @patch("clip_creator.vid_ed.red_vid_edit.VideoFileClip")
    def test_get_clip_duration(self, mock_videoclip):
        dummy_clip = MagicMock()
        dummy_clip.duration = 10.5
        instance = MagicMock()
        instance.__enter__.return_value = dummy_clip
        mock_videoclip.return_value = instance

        video_path = "dummy_video.mp4"
        duration = get_clip_duration(video_path)
        self.assertEqual(duration, 10.5)
        mock_videoclip.assert_called_with(video_path)

    @patch("clip_creator.vid_ed.red_vid_edit.AudioSegment")
    def test_get_audio_duration(self, mock_audio_segment):
        dummy_audio = MagicMock()
        # Set the __len__ return value to simulate 5000 ms.
        dummy_audio.__len__.return_value = 5000
        mock_audio_segment.from_file.return_value = dummy_audio

        audio_path = "dummy_audio.mp3"
        duration = get_audio_duration(audio_path)
        self.assertEqual(duration, 5.0)
        mock_audio_segment.from_file.assert_called_with(audio_path)

    @patch("clip_creator.vid_ed.red_vid_edit.ImageClip")
    @patch("clip_creator.vid_ed.red_vid_edit.swap_words_numbers")
    @patch("clip_creator.vid_ed.red_vid_edit.remove_non_letters")
    def test_create_postimg_clip(self, mock_remove, mock_swap, mock_imageclip):
        # Configure the scanning functions to return the title unchanged.
        mock_remove.side_effect = lambda s: s
        mock_swap.side_effect = lambda s: s

        # Create a dummy transcript with two segments.
        transcript = [
            {"start": 2, "text": "HELLO", "duration": 1},
            {"start": 5, "text": "WORLD", "duration": 1},
        ]
        # When a segment's text is not in the title,
        # the loop breaks at the second segment. Then, since transcript[-1]['start'] equals start,
        # start should be recalculated as len(title)*(160/60).
        post_png_file = "dummy_post.png"
        title = "hello"
        dummy_clip_instance = MagicMock()
        mock_imageclip.return_value = dummy_clip_instance

        clip, start = create_postimg_clip(post_png_file, transcript, title)
        expected_start = len(title) * (160 / 60)
        self.assertAlmostEqual(start, expected_start)
        self.assertEqual(clip, dummy_clip_instance)
        # Verify that the scanning functions were called correctly.
        mock_remove.assert_called_with(title.upper())
        mock_swap.assert_called()

    @patch("clip_creator.vid_ed.red_vid_edit.create_caption_images_reddit")
    @patch("clip_creator.vid_ed.red_vid_edit.os.listdir")
    @patch("clip_creator.vid_ed.red_vid_edit.ImageClip")
    def test_create_captions_no_clips_due_to_end_image_time(
        self, mock_imageclip, mock_listdir, mock_create_caption_images
    ):
        # Setup: transcript with one dummy segment.
        transcript = [{"start": 0, "text": "dummy", "duration": 2}]
        # Simulate no matching files found
        mock_listdir.return_value = []
        # Patch ImageClip to return a dummy clip.
        dummy_imageclip = MagicMock()
        mock_imageclip.return_value = dummy_imageclip

        # Call create_captions with end_image_time greater than the segment start.
        output_dir, clip_list = create_captions(
            prefix="testprefix",
            paragraph="test paragraph",
            transcript=transcript,
            target_size=(480, 640),
            output_dir="./tmp/caps_img",
            part=0,
            end_image_time=1,
        )
        # Verify that create_caption_images_reddit was called since file wasn't found.
        mock_create_caption_images.assert_called_once_with(
            "testprefix", transcript, 640, "./tmp/caps_img", 0
        )
        # Since section start (0) is less than end_image_time (1), the caption clip is skipped.
        self.assertEqual(clip_list, [])


if __name__ == "__main__":
    unittest.main()
