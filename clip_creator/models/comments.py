import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, HttpUrl


class CommentReply(BaseModel):
    author: str | None = None
    upvotes: int = 0
    content: str | None = None
    posted_at: datetime | None = None
    parent_id: str | None = None


class Comment(BaseModel):
    author: str
    upvotes: int
    content: str
    parent_id: str
    posted_at: datetime
    best_reply: dict[str, Any] = Field(default_factory=dict)
    reply: CommentReply | None = None


class Post(BaseModel):
    post_id: str
    title: str
    content: str
    upvotes: int
    comments: int
    nsfw: bool
    posted_at: datetime
    url: HttpUrl
    tiktok_posted: bool | None = None
    insta_posted: bool | None = None
    yt_posted: bool | None = None
    transcript: str | None = None
    comments_json: list[Comment]
    length: int | None = None
    author: str
    updated_at: datetime | None = None
    tiktok_uploaded: bool | None = None
    chunks: dict[uuid, dict[str, Any]] | None = None
    comments_above_rpl: int
    comments_above: int
    sched: str | None = None
    chunks_es: dict[uuid, dict[str, Any]] | None = None
    audio_length: int


if __name__ == "__main__":
    # Example usage (using the provided data):
    data = {
        "post_id": "1jhq9r3",
        "title": "Guys, what’s the best pickup line ever used on you from a woman?",
        "content": (
            "I always see a ton of pickup lines used by men on women, but I’ve been"
            " searching for a hot minute here trying to find/come up with something"
            " that would make my man smile. He’s been under a lot of pressure lately"
            " finding work and distracted by life’s stresses, and I want to cheer him"
            " up a little.\n\nWhat would be the male equivalent of a panty-dropper for"
            " you?"
        ),
        "upvotes": 16,
        "comments": 76,
        "nsfw": 0,
        "posted_at": "2025-03-23T03:29:19.000000+0000",
        "url": "/r/AskMen/comments/1jhq9r3/guys_whats_the_best_pickup_line_ever_used_on_you/",
        "tiktok_posted": None,
        "insta_posted": None,
        "yt_posted": None,
        "transcript": None,
        "comments_json": [
            {
                "author": "dgroeneveld9",
                "upvotes": 45,
                "content": (
                    "Will you take me to my junior prom. I said yes and weve been"
                    " together for 10 years now. Finally planning a wedding. Lmao"
                ),
                "parent_id": "t3_1jhq9r3",
                "posted_at": "2025-03-23T03:34:19.000000+0000",
                "best_reply": {},
                "reply": {"upvotes": 0},
            },
            {
                "author": "Not_Cool_Ice_Cold",
                "upvotes": 25,
                "content": "Hi!\n\nThat usually works for me.",
                "parent_id": "t3_1jhq9r3",
                "posted_at": "2025-03-23T03:52:48.000000+0000",
                "best_reply": {},
                "reply": {"upvotes": 0},
            },
            {
                "author": "Dorkimus-Maximus",
                "upvotes": 12,
                "content": (
                    'Once asked a girl in high school "My heart has a vacancy, does'
                    ' yours need a place to stay?"'
                ),
                "parent_id": "t3_1jhq9r3",
                "posted_at": "2025-03-23T04:01:46.000000+0000",
                "best_reply": {},
                "reply": {
                    "author": "homegrown_rebel",
                    "upvotes": 11,
                    "content": "Sounds like an emo song lol",
                    "posted_at": "2025-03-23T04:34:03.000000+0000",
                    "parent_id": "t1_mj9cn6m",
                },
            },
            {
                "author": "hatred-shapped",
                "upvotes": 7,
                "content": (
                    "Man you look like a really bad decision. How'd you like to make"
                    " some memories we'll regret later in life.\xa0"
                ),
                "parent_id": "t3_1jhq9r3",
                "posted_at": "2025-03-23T04:32:30.000000+0000",
                "best_reply": {},
                "reply": {"upvotes": 0},
            },
            {
                "author": "catch_my_drift",
                "upvotes": 6,
                "content": (
                    "A bit of sarcasm, coupled with constant eye fucking works on me"
                    " every time."
                ),
                "parent_id": "t3_1jhq9r3",
                "posted_at": "2025-03-23T03:55:28.000000+0000",
                "best_reply": {},
                "reply": {"upvotes": 0},
            },
            {
                "author": "niveapeachshine",
                "upvotes": 2,
                "content": "Bro did you just fart? Because you blew me away.",
                "parent_id": "t3_1jhq9r3",
                "posted_at": "2025-03-23T05:00:20.000000+0000",
                "best_reply": {},
                "reply": {"upvotes": 0},
            },
            {
                "author": "StreetSea9588",
                "upvotes": 1,
                "content": (
                    "I've only been hit on by women twice in my life.\n\n1. The first"
                    " time a woman hit on me at a bar and took me back to her place"
                    ' began with "Can I sit here?" \n\n\n2. This second one happened'
                    " when I was 20 and was driving a 25-year-old friend of my"
                    ' sister\'s home:\n\nHer: "Can I ask you a blunt question?"\nMe:'
                    ' "Sure."\nHer: "Wanna fuck?"\n\nCame out of nowhere. In the 0.3'
                    " seconds before saying yes I calculated the chances of a woman"
                    " ever asking me that question again. Mathematically I had to"
                    " do it."
                ),
                "parent_id": "t3_1jhq9r3",
                "posted_at": "2025-03-23T06:02:07.000000+0000",
                "best_reply": {},
                "reply": {"upvotes": 0},
            },
            {
                "author": "CptJFK",
                "upvotes": 1,
                "content": (
                    "When I was around 25ish a beautiful yet obviously older-than-me"
                    " woman approached me at a bar. She started an actually nice"
                    " conversation, talked for a bit.\n\nThen she said something like"
                    ' "i\'m tired. Would you bring me home safe and tuck me in?"'
                    " \n\nTODAY I know what all the little arm-touching, 'accidental'"
                    " little contacts on knees or thighs mean. A brush on your hand or"
                    " forearm.\n\nBut then?\nI walked her home (safely), wished a good"
                    " night and went back to the bar."
                ),
                "parent_id": "t3_1jhq9r3",
                "posted_at": "2025-03-23T06:08:03.000000+0000",
                "best_reply": {},
                "reply": {"upvotes": 0},
            },
        ],
        "length": 0,
        "author": "AutoModerator",
    }
