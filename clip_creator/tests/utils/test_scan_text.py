from unittest import TestCase, mock
from clip_creator.utils.scan_text import reddit_remove_bad_words, reddit_acronym, swap_words_numbers, remove_non_letters, reg_get_og, get_top_posts
from clip_creator.db.db import (
    get_rows_where_tiktok_null_or_empty,
)

class TestScanText(TestCase):

    def test_scan_text(self):
        bad_sentence = """UPDATE: My (25F) husband (27M) suddenly wants too much sex? I am a bad person and I will say AITAH and TIFU, 
                        For those who didn’t read the first post here it is -> https://www.reddit.com/r/relationship_advice/s/U9YwaI307N


                        Some of you commented (and most DMed me) saying it could be something shady like cheating, guilt, etc. I really didn’t think that was the case, but my overthinking got the best of me. So last night I went through his phone. I know, not nice of me, but I was just so curious and he doesnt even have a password. I wasn’t even expecting anything crazy, maybe just a ton of porn or something. I found nothing weird though.
                    

                        While I was doing this, he woke up, looked at me all sleepy, and said, “Is that my phone?” I panicked and just said “Yeah.” He literally just mumbled “Oh,” rolled over, and went back to sleep.
                    

                        In the morning, he didn’t say anything about it, so I was like, “Uh… aren’t you gonna say something about the fact that I went through your phone last night?” And he didn't even understand what I was saying.
                    

                        I reminded him, and he laughed. He genuinely thought I was just watching a movie or show (I sometimes use his phone for that if mine is charging), so he didn’t even notice I was snooping.
                    

                        At this point, I just told him everything, how I got paranoid, why I checked, how I was worried something was wrong. He got quiet for a second, then kind of shyly admitted that he thought I was enjoying all the extra sex, so he just kept initiating more. But the real reason, he said he sometimes feels disconnected from me.
                    

                        He’s very introverted, doesn’t talk to many people, keeps his circle small. Meanwhile, my entire job is social (I work in PR), and I spend a lot of time with my coworkers. He admitted that sometimes he feels like I have this whole world outside of our relationship, and since he’s not super talkative, he worries he doesn’t always connect with me the way I do with others. Sex, for him, is one of the most intimate things we share, so in his mind, having more of it made him feel closer to me.
                    

                        I almost cried when he said this because I never thought of it that way. I reassured him that just because I talk to a million people a day doesn’t mean I don’t prioritize him. And we both agreed to make more of an effort to connect outside of just sex, more quality time, deeper conversations, little gestures. I also promised to communicate better if something is overwhelming me instead of silently suffering and then having a breakdown about it (lol).
                    

                        Basically, I love him soo much i am fuckeD.
                    """
        no_acros = reddit_acronym(bad_sentence)
        self.assertNotIn("AITAH", no_acros.upper())
        self.assertNotIn("TIFU", no_acros.upper())
        no_bad_words = reddit_remove_bad_words(bad_sentence)
        self.assertNotIn("sex", no_bad_words)
        self.assertNotIn("fucked", no_bad_words)
        no_numbers = swap_words_numbers(bad_sentence)
        self.assertNotIn("25", no_numbers)
        self.assertNotIn("27", no_numbers)
        no_other_chars = remove_non_letters(bad_sentence)
        self.assertNotIn("(", no_other_chars)
        self.assertNotIn(")", no_other_chars)
        self.assertNotIn("’", no_other_chars)
        links, no_sites = reg_get_og(bad_sentence, "UPDATE: My (25F) husband (27M) suddenly wants too much sex?")
        self.assertNotIn("https:/", no_sites)
        self.assertIsNotNone(no_sites)
        self.assertIn("https://www.reddit.com/r/relationship_advice/s/U9YwaI307N", links)
    def test_get_top_posts(self):
        unused_posts = get_rows_where_tiktok_null_or_empty()
        posts_to_use = {}
        for post in unused_posts:
            posts_to_use[post['post_id']] = (post)
        five_posts = get_top_posts(posts_to_use, 5)
        self.assertEqual(len(five_posts), 5)
        for id, post in five_posts.items():
            self.assertIn("title", post.keys())
            self.assertIsInstance(id, str)