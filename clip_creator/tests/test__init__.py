from unittest import main
from urlextract import URLExtract

from clip_creator.tests.test_ai import *
from clip_creator.tests.test_video_edit import *
from clip_creator.tests.utils.test_scan_text import *

from clip_creator.conf import LOGGER
from reddit_com import main_reddit_coms_orch
from clip_creator.utils.scan_text import remove_markdown_links_images, reddit_remove_bad_words, reddit_acronym, swap_words_numbers, remove_non_letters
import random

class TestRedditComments(unittest.TestCase):
    def test_reddit_comments_script_format(self):
        LOGGER.setLevel("DEBUG")
        bad_words = ["damn", "hell", "crap", "shit"]
        links = ["https://example.com", "http://testsite.org", "https://anotherlink.net"]
        emojis = ["😃", "😂", "🤔", "😡", "👍"]
        symbols = ["@", "#", "$", "%", "&", "*"]
        title = "What do I call my dead girlfriend? shit-head shit-for-brains stupidass stupid-ass brass motherfucker f4g (24f)"
        body = "(https://anotherlink.net)[https://anotherlink.net]So last year my girlfriend died and when I talk about her I don’t know how I should refer to her? To call her my girlfriend who died seems so long winded and un poetic, calling her my ex doesn’t work because we were together her last days. Do I call her my late gf?  "
        comments = [{"author": "EatPumpkinPie", "upvotes": 1591, "content": "Late GF. \ud83d\udc4d", "parent_id": "t3_1jhzlkp", "posted_at": "2025-03-23T13:48:25.000000+0000", "best_reply": {}, "reply": {"upvotes": 0}}, {"author": "Cliffy73", "upvotes": 468, "content": "Yes, late would be appropriate. I\u2019m sorry for your loss.", "parent_id": "t3_1jhzlkp", "posted_at": "2025-03-23T13:53:45.000000+0000", "best_reply": {}, "reply": {"author": "FAITH2016", "upvotes": 29, "content": "Yes. This should be specific enough so that no one asks any questions.", "posted_at": "2025-03-23T14:02:55.000000+0000", "parent_id": "t1_mjb5zzj"}}, {"author": "emryldmyst", "upvotes": 341, "content": "My former or late partner.\n\n\nDon't let anyone call her your ex.\u00a0 I hate that crap because it's not true.\n\n\nI'm very sorry for your loss.\u00a0 There's a widow group on here you're welcome to join.", "parent_id": "t3_1jhzlkp", "posted_at": "2025-03-23T14:12:37.000000+0000", "best_reply": {}, "reply": {"author": "Weseu666", "upvotes": 28, "content": "Out of curiosity, would late girlfriend still be appropriate to use if a lot of time has passed and you're now seeing someone else?", "posted_at": "2025-03-23T15:59:09.000000+0000", "parent_id": "t1_mjb98ht"}}, {"author": "k_lo970", "upvotes": 68, "content": "Late girlfriend if you are comfortable saying that.\n\nOr just call her by her name. My best friend passed away a long time ago. His girlfriend and our friends just call him by his name like he could be in the other room to this day. He had a really big personality which might be why it seems so normal.", "parent_id": "t3_1jhzlkp", "posted_at": "2025-03-23T14:31:32.000000+0000", "best_reply": {}, "reply": {"author": "JarkJark", "upvotes": 11, "content": "I'm terrible with names. I have a client that lost their husband last year, shortly before I met her. I won't ever forget her husband's name, because she talks about \"Richard\" and it's important.", "posted_at": "2025-03-23T15:41:50.000000+0000", "parent_id": "t1_mjbck9u"}}, {"author": "RedMageMajure", "upvotes": 15, "content": "My wife lost her first husband when they were very young. Its been almost 25 years and she still refers to him by a pet name (and always a twinge of sadness in her eyes)", "parent_id": "t3_1jhzlkp", "posted_at": "2025-03-23T15:25:07.000000+0000", "best_reply": {}, "reply": {"author": "Pleasant-Pattern-566", "upvotes": 4, "content": "That would kill me", "posted_at": "2025-03-23T16:07:18.000000+0000", "parent_id": "t1_mjbmcsp"}}, {"author": "Possible-Estimate748", "upvotes": 10, "content": "Never had this experience so I feel but if someone told me \"late gf/bf\" I would understand.", "parent_id": "t3_1jhzlkp", "posted_at": "2025-03-23T14:03:01.000000+0000", "best_reply": {}, "reply": {"author": "Axel_Dino", "upvotes": 5, "content": "Yes, just like saying \"my late husband/wife\"", "posted_at": "2025-03-23T14:14:39.000000+0000", "parent_id": "t1_mjb7k9a"}}, {"author": "houseonpost", "upvotes": 1, "content": "Sorry for your loss. I'm assuming the people you are talking to know the both of you. So just call her by her name when talking about her. \n\nIf you are bringing her up in conversations with people you barely know regularly it might mean you aren't processing things in a long term healthy way. Talk to a therapist. They can really help with your grief.", "parent_id": "t3_1jhzlkp", "posted_at": "2025-03-23T16:18:07.000000+0000", "best_reply": {}, "reply": {"upvotes": 0}}]
        
        parts = [
            random.choice(bad_words),
            random.choice(links),
            random.choice(emojis),
            random.choice(symbols),
            random.choice(bad_words),
            random.choice(links),
            random.choice(emojis),
            random.choice(symbols),
            title,
            body,
        ]
        for comment in comments:
            parts.append(comment["content"])
        url_finder = URLExtract()
        random_string = " ".join(parts)
        if url_finder.has_urls(random_string):
            found_urls:list[str] = url_finder.find_urls(random_string)
            for url in found_urls:
                random_string = random_string.replace(url, "")
        created_string = remove_non_letters(
                swap_words_numbers(
                    reddit_acronym(
                        reddit_remove_bad_words(
                            remove_markdown_links_images(
                                random_string
                            )
                        )
                    )
                )
            ).lower()
        self.assertNotIn("http", created_string)
        self.assertNotIn("www", created_string)
        self.assertNotIn(".com", created_string)
        self.assertNotIn(".org", created_string)
        self.assertNotIn("shit", created_string)
        self.assertNotIn("(24f)", created_string)
        self.assertIn('twenty four f', created_string)
        LOGGER.debug(str(created_string).encode("ASCII", "ignore").decode())

if __name__ == "__main__":
    main()
