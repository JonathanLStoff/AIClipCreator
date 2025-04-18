import os
import unittest

from clip_creator.tts.ai import TTSModelKokoro


class TestTTS(unittest.TestCase):
    def test_tts(self):
        tts_model = TTSModelKokoro(voice=1)
        # FIX sample rate!!!!
        filename = "tmp/audios/test_tts.wav"
        content = (
            "AITA for telling my husband he doesn't know how to use chopsticks? Okay so"
            " some background. I'm Hispanic and when my family immigrated from Mexico"
            " they were in an ESL program with a lot of other Mexican and Japanese"
            " people. My Dad learned how to properly use chopsticks from a Japanese"
            " immigrant and showed me how to do it when I was a toddler. I've been"
            " doing it my whole life and find it really easy and honestly better than"
            " forks for some foods.\n  \n\n    My husband and his sisters taught"
            " themselves how to use chopsticks when they were teenagers. I notice they"
            " all struggle with them but I haven't said anything critical about it.\n "
            " \n\n    So my husband and I went to an udon festival at a Buddhist temple"
            " and this much older Japanese lady was staring at me eating udon and"
            " praised how I was using my chopsticks. Saying I was holding them well and"
            " asking who taught me. Then she turned to my husband and criticized him,"
            " saying he broke the wooden chopsticks wrong (they were lopsided) and he's"
            " holding them improperly. He looked really embarrassed and tried to defend"
            " himself.\n  \n\n    Fast forward to this week. My sister-in-law visited"
            " us from out of state. My husband prepared a rice bowl and my sil plated"
            " them with forks. I went ahead and grabbed chopsticks to replace my fork"
            " with (I left their bowls alone). They both immediately made fun of me,"
            " saying why can't I eat it with a fork and do I need chopsticks. When I"
            " said I feel weird eating Japanese food with a fork they said I was being"
            " pretentious and just take the fork. I then retorted that at least I know"
            " how to use chopsticks correctly. They both went silent and my husband"
            " turned red in embarrassment. He later told me in private this hurt him.\n"
            "  \n\n    I realize this was rude on my part and didn't help. I don't"
            " normally say anything on what type of utensils other people use but they"
            " kept picking on me for it. AITA here?"
        )
        tts_model.run_it(filename, content)
        self.assertTrue(os.path.exists(filename))
