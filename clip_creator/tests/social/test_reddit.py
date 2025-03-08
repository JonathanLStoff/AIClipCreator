from clip_creator.social.reddit import reddit_json_all
import json
from unittest import TestCase, main

class TestReddit(TestCase):
    def test_json_extract(self):
        # Test with a sample JSON string
        with open("test_files/reddit.json", "r") as f:
            json_dict = json.load(f)
        
        result = reddit_json_all(json_dict)
        self.assertEqual(result["title"], "Which show started 10/10 and ended 10/10?")
if __name__ == "__main__":
    main()
