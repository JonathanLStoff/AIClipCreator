import os
import shutil
import unittest
from unittest.mock import MagicMock, patch

from moviepy import VideoFileClip

from clip_creator.video_edit import (
    add_text_to_video,
    create_captions,
    crop_video_by_coords,
    crop_video_into_another,
    edit_vid_orchestrator,
    fix_video_grb,
    get_first_frame_screenshot,
    get_word_timestamps_openai,
)


class TestVideoEditor(unittest.TestCase):
    def setUp(self):
        self.test_dir = "./test_tmp"
        os.makedirs(self.test_dir, exist_ok=True)
        os.makedirs(os.path.join(self.test_dir, "audios"), exist_ok=True)
        os.makedirs(os.path.join(self.test_dir, "caps_img"), exist_ok=True)

        # Create a dummy video file for testing
        self.dummy_video_path = os.path.join(self.test_dir, "dummy_video.mp4")
        dummy_clip = VideoFileClip("tests/dummy_video.mp4")
        dummy_clip.write_videofile(self.dummy_video_path, codec="libx264", fps=24)
        dummy_clip.close()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_edit_vid_orchestrator(self):
        output_file, transcript = edit_vid_orchestrator(
            "test",
            self.dummy_video_path,
            os.path.join(self.test_dir, "output_video.mp4"),
            text="Test text",
            start_time=0,
            end_time=5,
        )
        self.assertTrue(os.path.exists(output_file))
        self.assertIsInstance(transcript, list)

    @patch("clip_creator.video_editor.create_caption_images")
    def test_create_captions(self, mock_create_caption_images):
        mock_create_caption_images.return_value = None
        transcript = [{"text": "test", "start": 0.0, "duration": 1.0, "end": 1.0}]
        video_clip = VideoFileClip(self.dummy_video_path).subclipped(0, 1)
        output_dir, clip_list = create_captions(
            "test", transcript, video_clip, os.path.join(self.test_dir, "caps_img")
        )
        self.assertIsInstance(clip_list, list)

    def test_get_first_frame_screenshot(self):
        screenshot_path = os.path.join(self.test_dir, "screenshot.jpg")
        get_first_frame_screenshot(self.dummy_video_path, screenshot_path)
        self.assertTrue(os.path.exists(screenshot_path))

    def test_crop_video_by_coords(self):
        output_file = os.path.join(self.test_dir, "cropped_video.mp4")
        crop_video_by_coords(self.dummy_video_path, output_file, 10, 10, 100, 100)
        self.assertTrue(os.path.exists(output_file))

    def test_crop_video_into_another(self):
        output_file = os.path.join(self.test_dir, "composite_video.mp4")
        crop_video_into_another(
            self.dummy_video_path, self.dummy_video_path, output_file
        )
        self.assertTrue(os.path.exists(output_file))

    def test_add_text_to_video(self):
        output_file = os.path.join(self.test_dir, "text_video.mp4")
        add_text_to_video(
            self.dummy_video_path,
            "Test Text",
            "Arial",
            24,
            "white",
            "black",
            2,
            "center",
            0,
        )
        self.assertTrue(os.path.exists("output_video.mp4"))
        os.remove("output_video.mp4")

    @patch("clip_creator.video_editor.AutoModelForSpeechSeq2Seq.from_pretrained")
    @patch("clip_creator.video_editor.AutoProcessor.from_pretrained")
    @patch("clip_creator.video_editor.pipeline")
    def test_get_word_timestamps_openai(
        self, mock_pipeline, mock_processor, mock_model
    ):
        mock_model.return_value = MagicMock()
        mock_processor.return_value = MagicMock()
        mock_pipeline.return_value = MagicMock(
            return_value={"chunks": [{"text": "test", "timestamp": (0.0, 1.0)}]}
        )
        transcript = get_word_timestamps_openai(self.dummy_video_path, time_add=0.0)
        self.assertIsInstance(transcript, list)
        self.assertEqual(len(transcript), 1)

    def test_fix_video_grb(self):
        output_file = self.dummy_video_path.replace(".mp4", "_fixed.mp4")
        fix_video_grb(self.dummy_video_path)
        self.assertTrue(os.path.exists(output_file))
        os.remove(output_file)


if __name__ == "__main__":
    unittest.main()
