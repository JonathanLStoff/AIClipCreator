from clip_creator.conf import LOGGER
from unittest import TestCase

from clip_creator.db.db import (
    get_rows_where_tiktok_null_or_empty,
)
from clip_creator.utils.scan_text import (
    get_top_posts,
    reddit_acronym,
    reddit_remove_bad_words,
    reg_get_og,
    remove_non_letters,
    swap_words_numbers,
    remove_markdown_links_images,
)


class TestScanText(TestCase):
    def test_scan_text(self)-> None:
        LOGGER.setLevel("DEBUG")
        bad_sentence:str = """
        
        **I am NOT the Original Poster. That is** [minimum-wage-max-BS](https://www.reddit.com/user/minimum-wage-max-BS/). She posted in r/CharlotteDobreYouTube 

        # Do NOT comment on Original Posts. Latest update is 7 days old. 

        **Trigger Warning:** &gt;!transphobia; child abuse!&lt;

        **Mood Spoiler:** &gt;!sad but OOP will be ok!&lt;

        **Original** [Post](https://www.reddit.com/r/CharlotteDobreYouTube/comments/1jjc9jn/my_friend_invited_my_ex_husband_to_her_wedding_so/)**: March 25, 2025**

        I (37f) left my husband, 'Darren' (37M) two years ago, when our eldest daughter (now 19) came out and he physically attacked her for it. We have four children and I have soul custody over the three who young enough to be covered by custody agreements, which Darren has tried to fight me over for the past two years but when you have a criminal record for beating up one child, the courts are unlikely to give you custody of the others. Darren and I were in the same friendship group since Primary school but my friends told me they had all cut contact with him.

        I went to my friend, 'Rachel's' (37f) wedding, this weekend when I spotted him at the ceremony. Because it's a wedding and an important day for my friend, I chose not to acknowledge his existence. It was a big wedding anyway so I thought I could just avoid him and have a conversation with Rachel about his presence at a later date because she deserved to enjoy her day.

        However, when I was looking at the seating plan for the reception, I saw both of our names, one after the other. Rachel had put our group, including Darren on the same table. My two other friends from this group convinced me to take my seat because we hardly get to see each other anymore, promising that they had no idea why Darren was invited and vowing to 'make him regret being born' if any drama started.

        Darren sat next to me, greeted me with a 'hey, babe', as if we were still together, and I could not cope with being in his presence. All I could think about was desperately trying to restrain him while my second eldest called the police. I downed my glass of prosecco and walked to my hotel.

        Yesterday, I got a message from Rachel saying that her mum asked her to invite Darren and Rachel said yes because her parents were paying for most of the wedding. Rachel's mum is Darren's godmother. I asked her about the seating plan and, again, she said that was her mum's doing because she was adamant that there was a potential for us to get back together. She apologised for not telling me, saying that she thought I wouldn't go if I knew (which is true, I wouldn't have come). I have not replied to that message and I don't plan to. As much as I don't want to give up on an over 3 decade long friendship, I can't get past this

        ***OOP's Comments:***

        Commenter: Also fuck any "friends" who convinced her to stay and actually sit at the table. Why tf didn't any of them at least offer to swap seats so she didn't have to sit next to the POS that she should probably have a restraining order against?

        &gt;**OOP:** Thank you. My eldest has a restraining order but because his actions were towards her and not myself, I don't really have the evidence to be granted one in the UK

        Commenter: I assume, since Rachel is from the friend group, that she knows what he did. I also assume, because you’ve been friends for 30 years, that she knows your children. If these two facts are true, than she needed to protect you - this was unforgivable.

        &gt;**OOP:** Yeah, my children call her their aunty and she and her husband helped me pack up our lives after what he did. I still can't wrap my head around why she didn't even warn me

        *OOP on her reaction:*

        &gt;I was very mindful of the fact that my ex is still trying to drag me through the courts for access to my three younger children and if I reacted how I wanted to, it could be brought up further down the road, otherwise, I wouldn't have been so quiet

        Commenter: You are a badass and I hope to be the type of mom you are. You did the right thing. You respected your friend’s wedding. Your friend and her mother disrespected you and your kid. Also, the suggestion you would rekindle something with the ass hole who assaulted your kid for coming out makes me seriously concerned about being around these people at all. If your friend was your friend, she would’ve said no that isn’t gonna happen, he’s a piece of shit. End of story.

        Sorry you had such a shit experience. Sorry your kid’s coming out was traumatic, instead of the celebration it should w been. But, you’re amazing and I hope you are surrounded by people who see and support how great you are!

        &gt;**OOP:** Thank you so much. I can't believe I wasted so much time on this man. I'm just so grateful that my children weren't there. Looking back, I'm thinking that his presence is why they weren't invited (my eldest has a restraining order against him)

        *7 hours later:*

        Commenter: You might need to warn your oldest of what happened incase your ex friends try and contact them over you going NC

        &gt;**OOP:** We had a conversation with her when I got home and she has blocked Rachel and her husband

        **Update** [Post](https://www.reddit.com/r/CharlotteDobreYouTube/comments/1jkgg7e/update_my_friend_invited_my_ex_husband_to_her/)**: March 26, 2025 (Next Day/35 hours later)**

        Thank you to everyone for their support in the comments.

        Before I get into the update, I noticed a couple of comments pointing out my mistake with soul/sole custody and I'm just grateful that I have a solicitor for custody stuff because if I make a mistake doesn't come up with a wiggly red line under it, I will not pick up on it.

        Anyway, I did not reply to Rachel and just blocked her but her husband called me yesterday. He apologised but then went on bout how hard this is for Rachel and how she feels that the day was tainted for her. I told him that how she sees her day is not my responsibility and I ended up blocking him as well.

        I talked to one of the members of the friend group and he apologised for convincing me to even sit down at the table. He said he thought more about him wanting to have the group back together than how it would affect me. He then told me about how Darren told Rachel's family members who asked where I was that me seeing him reminded him too much about our 'son who died' two years ago and I had to leave. He was referring to my daughter, who is a (very much alive) transwoman. Apparently no one in the group attempted to correct him, so I have just removed myself from our group chats and am going to try to make better friends.

        Also, thank you to the people who wished my daughter well. She wanted me to say that she really appreciates it and she is starting to thrive, despite the mental scarring and tinnitus her sorry excuse for a father gave her. I could not be prouder of how far she has come in her journey and, in September, she will be the first person in my family to go to university. She is taking a page out of the petty queen's book and getting her revenge with a life well lived.

        ***OOP's Comments:***

        Commenter: I gained a daughter too just before Christmas. She’s still finding her feet but enjoying all the new outfits I’m making on the sewing machine.

        &gt;**OOP:** Aw, those outfits must mean the world to her

        Commenter: What do your other kids think why they can’t see their dad?

        &gt;**OOP:** My second eldest saw what he did and the younger two saw the state he left their sister in. They were 7, 8 and 11 at the time so they were old enough to be aware of the situation. They do talk about missing having a dad sometimes but they don't feel safe around him and my second eldest is petrified of him

        Commenter: That’s horrifying. I grew up witnessing violence in my home, and that stays with a person. Have you considered counseling for the family? 🥺

        &gt;**OOP:** I am so sorry you had to go through that. They're all in individual therapy through the nhs and their schools but I will try to get us a referral for family counselling
                
        
        Your friend gives you $200-600 to gamble and you win $262,000.54 What would you do? 85.62
        
                        UPDATE: My (25F) husband (27M) suddenly don't want too much sex? I am a bad person and I will say AITAH and TIFU,
                        
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
        tmp = remove_markdown_links_images(
                                bad_sentence
                            )
        self.assertNotIn("didn t", tmp)
        tmp = reddit_remove_bad_words(
                            tmp
                        )
        self.assertNotIn("didn t", tmp)
        tmp = reddit_acronym(
                        tmp
                    )
        self.assertNotIn("didn t", tmp)
        tmp = swap_words_numbers(
                    tmp
                )
        self.assertNotIn("didn t", tmp)
        better_sent:str = remove_non_letters(
                tmp
            )
        self.assertIn(" dont ", better_sent)
        self.assertNotIn("didn t", better_sent)
        print(better_sent)

    def test_get_top_posts(self):
        unused_posts = get_rows_where_tiktok_null_or_empty()
        posts_to_use = {}
        for post in unused_posts:
            posts_to_use[post["post_id"]] = post
        five_posts = get_top_posts(posts_to_use, 5)
        self.assertEqual(len(five_posts), 5)
        for id, post in five_posts.items():
            self.assertIn("title", post.keys())
            self.assertIsInstance(id, str)
