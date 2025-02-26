import os
from clip_creator.video_edit import edit_video
from clip_creator.utils.scan_text import (
    sanitize_filename,
)
from clip_creator.conf import (
    CLIPS_FOLDER,
    DOWNLOAD_FOLDER,
    LOGGER,
    SECTIONS_TYPES,
    TMP_CLIPS_FOLDER,
    TMP_DOWNLOAD_FOLDER,
    ERRORS_TYPES
)
def main():
    # No text
    
    id = "SXoQ5gJLJdY"
    transcript = [{"text": "stuck down we got to figure out what", "start": 157.959, "duration": 3.121}, {"text": "went wrong some animals are loose watch", "start": 159.04, "duration": 4.479}, {"text": "out for the animals yeah okay wait I", "start": 161.08, "duration": 5.12}, {"text": "found a healing syringe wait highy guys", "start": 163.519, "duration": 5.201}, {"text": "you want to see me shoot this up oh [\u00a0__\u00a0]", "start": 166.2, "duration": 4.52}, {"text": "oh [\u00a0__\u00a0]", "start": 168.72, "duration": 6.32}, {"text": "oh oh [\u00a0__\u00a0] me when I just learned how to", "start": 170.72, "duration": 8.159}, {"text": "swear okay fair enough Val anyway drug", "start": 175.04, "duration": 6.64}, {"text": "time", "start": 178.879, "duration": 7.041}, {"text": "oh what the [\u00a0__\u00a0] open Silo 3 to retrieve", "start": 181.68, "duration": 6.919}, {"text": "power cells that's what we need to do", "start": 185.92, "duration": 4.679}, {"text": "okay okay are we going to survive", "start": 188.599, "duration": 4.56}, {"text": "getting there I don't know check my give", "start": 190.599, "duration": 4.161}, {"text": "me a second sorry sorry I was being a", "start": 193.159, "duration": 3.201}, {"text": "piece of [\u00a0__\u00a0] damn this thing takes", "start": 194.76, "duration": 3.96}, {"text": "hours to swing oh my God you almost ran", "start": 196.36, "duration": 3.92}, {"text": "into that because they were watching me", "start": 198.72, "duration": 2.599}, {"text": "I think we just have to do the level", "start": 200.28, "duration": 2.959}, {"text": "three thing why is he dying still with", "start": 201.319, "duration": 5.64}, {"text": "that see we have to go fine everybody on", "start": 203.239, "duration": 4.72}, {"text": "the", "start": 206.959, "duration": 3.36}, {"text": "lift this is", "start": 207.959, "duration": 4.721}, {"text": "on this this thing here it says to take", "start": 210.319, "duration": 5.2}, {"text": "iodine and I have it so I'm going to try", "start": 212.68, "duration": 4.6}, {"text": "and taking iodine and entering this", "start": 215.519, "duration": 2.881}, {"text": "thing", "start": 217.28, "duration": 3.319}]
    text = "what the fuck 😭"
    edit_video(
        sanitize_filename(id),
        f"{TMP_DOWNLOAD_FOLDER}/{id}.mp4",
        f"tmp/test/{id}.mp4",
        target_size=(1080, 1920),
        start_time=157,
        end_time=165,
        text=text,
        transcript=transcript,
    )
    id = "qCuEQGLtfQ8"
    transcript = [{"text": "it's over", "start": 539.44, "duration": 2.399}, {"text": "here the same thing three", "start": 546.0, "duration": 4.32}, {"text": "[Music]", "start": 551.44, "duration": 3.199}, {"text": "times oh okay you go down there there's", "start": 558.48, "duration": 4.76}, {"text": "more down here wait not literally just", "start": 561.399, "duration": 6.481}, {"text": "push the carrot down I'm going to grab", "start": 563.24, "duration": 8.08}, {"text": "it are you sure", "start": 567.88, "duration": 5.16}, {"text": "seems like you forgot to do the grabbing", "start": 571.32, "duration": 4.28}, {"text": "it part", "start": 573.04, "duration": 2.56}, {"text": "dog all right you did that to yourself", "start": 578.12, "duration": 5.12}, {"text": "okay you did that to", "start": 580.68, "duration": 4.96}, {"text": "me okay you did that to", "start": 583.24, "duration": 5.4}, {"text": "me all right I think I just", "start": 585.64, "duration": 7.36}, {"text": "Dro be careful oh my ass I'm bleeding", "start": 588.64, "duration": 6.56}, {"text": "come down it's fine you you've had worse", "start": 593.0, "duration": 4.88}, {"text": "yeah true here wait hold on hold", "start": 595.2, "duration": 5.8}, {"text": "on ready yep wait we're dying we're", "start": 597.88, "duration": 4.519}, {"text": "dying if we do", "start": 601.0, "duration": 4.519}, {"text": "this I was", "start": 602.399, "duration": 5.401}]
    edit_video(
        sanitize_filename(id),
        f"{TMP_DOWNLOAD_FOLDER}/{id}.mp4",
        f"tmp/test/{id}.mp4",
        target_size=(1080, 1920),
        start_time=539,
        end_time=545,
        text="it windy out here",
        transcript=transcript,
    )

if __name__ == "__main__":
    main()