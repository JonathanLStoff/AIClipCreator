import logging
from clip_creator.conf import (
    LOGGER,
    TMP_DOWNLOAD_FOLDER,
)
from clip_creator.utils.scan_text import (
    sanitize_filename,
)
from clip_creator.vid_ed.video_edit import edit_vid_orchestrator, timestamps

def main():
    # No text
    LOGGER.setLevel(logging.DEBUG)
    #exit()
    # eager == []
    # spda == [{'text': ' Oh', 'start': 6.52, 'end': 6.66, 'duration': 0.14000000000000057}, {'text': ' my', 'start': 6.66, 'end': 6.82, 'duration': 0.16000000000000014}]
    id = "l6oJa69LFuI"
    transcript = [
        {
            "text": "not like that not like that not like",
            "start": 326.88,
            "duration": 3.439,
        },
        {"text": "that", "start": 329.08, "duration": 3.08},
        {
            "text": "see too well so let me know if you see",
            "start": 330.319,
            "duration": 4.641,
        },
        {"text": "something oh my", "start": 332.16, "duration": 2.8},
        {"text": "gosh what is", "start": 336.039, "duration": 6.88},
        {
            "text": "happening is he is he okay um John John",
            "start": 338.96,
            "duration": 5.359,
        },
        {"text": "we can't hear you if you're", "start": 342.919, "duration": 3.521},
        {
            "text": "talking did you activate your mic I",
            "start": 344.319,
            "duration": 4.121,
        },
        {"text": "forgot I had to double press the", "start": 346.44, "duration": 3.56},
        {"text": "voice", "start": 348.44, "duration": 4.44},
        {
            "text": "bro what the [\u00a0__\u00a0] just happening there I",
            "start": 350.0,
            "duration": 5.199,
        },
        {
            "text": "think there's no way what happened what",
            "start": 352.88,
            "duration": 5.72,
        },
        {
            "text": "the [\u00a0__\u00a0] was that what happened no what",
            "start": 355.199,
            "duration": 5.201,
        },
        {"text": "did you do swag", "start": 358.6, "duration": 4.599},
        {"text": "Jay died", "start": 360.4, "duration": 2.799},
        {"text": "again", "start": 363.28, "duration": 5.24},
        {
            "text": "ran ran a trip M we're at base camp",
            "start": 364.919,
            "duration": 6.161,
        },
        {
            "text": "number two right now we need to do those",
            "start": 368.52,
            "duration": 4.119,
        },
        {
            "text": "two objectives we need connect satellite",
            "start": 371.08,
            "duration": 2.959,
        },
        {
            "text": "and then upload the computer files we",
            "start": 372.639,
            "duration": 2.96,
        },
        {
            "text": "need to find the satellite where would",
            "start": 374.039,
            "duration": 4.961,
        },
        {
            "text": "that be what happened there dude what is",
            "start": 375.599,
            "duration": 6.88,
        },
        {
            "text": "going on over there hey I got a I have a",
            "start": 379.0,
            "duration": 5.88,
        },
        {
            "text": "serious weapon in my hand and I'm not a",
            "start": 382.479,
            "duration": 6.521,
        },
        {"text": "yeah okay who", "start": 384.88, "duration": 4.12},
    ]
    true_trans = [
        {"text": " We", "start": 15.86, "end": 15.98, "duration": 0.120000000000001},
        {
            "text": " can't",
            "start": 15.98,
            "end": 16.28,
            "duration": 0.3000000000000007,
        },
        {
            "text": " hear",
            "start": 16.28,
            "end": 16.42,
            "duration": 0.14000000000000057,
        },
        {"text": " you", "start": 16.42, "end": 16.54, "duration": 0.11999999999999744},
        {"text": " if", "start": 16.54, "end": 16.68, "duration": 0.14000000000000057},
        {
            "text": " you're",
            "start": 16.68,
            "end": 16.76,
            "duration": 0.08000000000000185,
        },
        {
            "text": " talking.",
            "start": 16.76,
            "end": 18.16,
            "duration": 1.3999999999999986,
        },
        {"text": " Did", "start": 18.16, "end": 18.64, "duration": 0.4800000000000004},
        {"text": " you", "start": 18.64, "end": 18.72, "duration": 0.0799999999999983},
        {
            "text": " activate",
            "start": 18.72,
            "end": 19.0,
            "duration": 0.28000000000000114,
        },
        {"text": " your", "start": 19.0, "end": 19.2, "duration": 0.1999999999999993},
        {"text": " mic?", "start": 19.2, "end": 19.34, "duration": 0.14000000000000057},
        {"text": " Damn", "start": 19.34, "end": 19.34, "duration": 0.1},
        {"text": " it,", "start": 19.34, "end": 19.44, "duration": 0.10000000000000142},
        {"text": " I", "start": 19.44, "end": 19.52, "duration": 0.0799999999999983},
        {
            "text": " forgot",
            "start": 19.52,
            "end": 19.66,
            "duration": 0.14000000000000057,
        },
        {"text": " I", "start": 19.66, "end": 19.78, "duration": 0.120000000000001},
        {"text": " had", "start": 19.78, "end": 19.9, "duration": 0.11999999999999744},
        {"text": " to", "start": 19.9, "end": 20.0, "duration": 0.10000000000000142},
        {
            "text": " double",
            "start": 20.0,
            "end": 20.22,
            "duration": 0.21999999999999886,
        },
        {
            "text": " press",
            "start": 20.22,
            "end": 20.5,
            "duration": 0.28000000000000114,
        },
        {"text": " the", "start": 20.5, "end": 20.68, "duration": 0.17999999999999972},
        {
            "text": " voice.",
            "start": 20.68,
            "end": 21.34,
            "duration": 0.6600000000000001,
        },
        {"text": " Whoa!", "start": 21.34, "end": 22.46, "duration": 1.120000000000001},
        {"text": " What", "start": 22.46, "end": 22.8, "duration": 0.33999999999999986},
        {"text": " the", "start": 22.8, "end": 24.28, "duration": 1.4800000000000004},
        {"text": " fuck", "start": 24.28, "end": 24.66, "duration": 0.379999999999999},
        {"text": " is", "start": 24.66, "end": 24.86, "duration": 0.1999999999999993},
        {
            "text": " happening",
            "start": 24.86,
            "end": 25.16,
            "duration": 0.3000000000000007,
        },
        {
            "text": " there?",
            "start": 25.16,
            "end": 25.52,
            "duration": 0.35999999999999943,
        },
        {"text": " I", "start": 25.52, "end": 25.74, "duration": 0.21999999999999886},
        {
            "text": " think,",
            "start": 25.74,
            "end": 26.16,
            "duration": 0.4200000000000017,
        },
        {"text": " dude!", "start": 26.16, "end": 27.66, "duration": 1.5},
        {"text": " What", "start": 27.66, "end": 27.8, "duration": 0.14000000000000057},
        {
            "text": " happened?",
            "start": 27.8,
            "end": 28.26,
            "duration": 0.46000000000000085,
        },
        {"text": " What", "start": 28.26, "end": 28.26, "duration": 0.1},
        {"text": " the", "start": 28.26, "end": 28.32, "duration": 0.05999999999999872},
        {
            "text": " fuck",
            "start": 28.32,
            "end": 28.54,
            "duration": 0.21999999999999886,
        },
        {"text": " was", "start": 28.54, "end": 28.74, "duration": 0.1999999999999993},
        {
            "text": " that?",
            "start": 28.74,
            "end": 29.14,
            "duration": 0.40000000000000213,
        },
        {
            "text": " What",
            "start": 29.14,
            "end": 29.32,
            "duration": 0.17999999999999972,
        },
        {
            "text": " happened",
            "start": 29.32,
            "end": 29.98,
            "duration": 0.6600000000000001,
        },
        {"text": " No!", "start": 30.0, "end": 31.12, "duration": 1.12},
        {"text": " What", "start": 31.12, "end": 31.76, "duration": 0.6399999999999999},
        {"text": " did", "start": 31.76, "end": 31.9, "duration": 0.1399999999999999},
        {"text": " you", "start": 31.9, "end": 32.06, "duration": 0.16000000000000014},
        {"text": " do,", "start": 32.06, "end": 32.42, "duration": 0.3599999999999999},
        {"text": " Swagger?", "start": 32.42, "end": 33.38, "duration": 0.96},
        {"text": " Jay", "start": 33.38, "end": 33.7, "duration": 0.3200000000000003},
        {"text": " died", "start": 33.7, "end": 34.12, "duration": 0.41999999999999993},
        {
            "text": " again?",
            "start": 34.12,
            "end": 34.980000000000004,
            "duration": 0.8600000000000003,
        },
        {"text": " Hit", "start": 34.980000000000004, "end": 40.46, "duration": 5.48},
        {"text": " M,", "start": 40.46, "end": 40.78, "duration": 0.3199999999999985},
        {
            "text": " we're",
            "start": 40.78,
            "end": 40.92,
            "duration": 0.14000000000000057,
        },
        {
            "text": " at",
            "start": 40.92,
            "end": 41.019999999999996,
            "duration": 0.09999999999999964,
        },
        {
            "text": " base",
            "start": 41.019999999999996,
            "end": 41.28,
            "duration": 0.2599999999999998,
        },
        {
            "text": " camp",
            "start": 41.28,
            "end": 41.56,
            "duration": 0.28000000000000114,
        },
        {
            "text": " number",
            "start": 41.56,
            "end": 41.82,
            "duration": 0.2599999999999998,
        },
        {"text": " two", "start": 41.82, "end": 42.06, "duration": 0.2400000000000002},
        {"text": " right", "start": 42.06, "end": 42.3, "duration": 0.2400000000000002},
        {"text": " now.", "start": 42.3, "end": 43.0, "duration": 0.6999999999999993},
        {"text": " We", "start": 43.0, "end": 43.4, "duration": 0.40000000000000036},
        {
            "text": " need",
            "start": 43.4,
            "end": 43.519999999999996,
            "duration": 0.11999999999999922,
        },
        {
            "text": " to",
            "start": 43.519999999999996,
            "end": 43.7,
            "duration": 0.17999999999999972,
        },
        {"text": " do", "start": 43.7, "end": 43.94, "duration": 0.2400000000000002},
        {"text": " those", "start": 43.94, "end": 44.2, "duration": 0.2599999999999998},
        {"text": " two", "start": 44.2, "end": 44.34, "duration": 0.14000000000000057},
        {
            "text": " objectives.",
            "start": 44.34,
            "end": 44.88,
            "duration": 0.5400000000000009,
        },
        {"text": " We", "start": 44.88, "end": 44.88, "duration": 0.1},
        {
            "text": " need",
            "start": 44.88,
            "end": 44.980000000000004,
            "duration": 0.09999999999999964,
        },
        {
            "text": " to",
            "start": 44.980000000000004,
            "end": 45.22,
            "duration": 0.2400000000000002,
        },
        {"text": " connect", "start": 45.22, "end": 45.22, "duration": 0.1},
        {
            "text": " satellite",
            "start": 45.22,
            "end": 45.62,
            "duration": 0.3999999999999986,
        },
        {"text": " and", "start": 45.62, "end": 45.82, "duration": 0.20000000000000107},
        {
            "text": " then",
            "start": 45.82,
            "end": 45.92,
            "duration": 0.09999999999999964,
        },
        {
            "text": " upload",
            "start": 45.92,
            "end": 46.2,
            "duration": 0.27999999999999936,
        },
        {"text": " the", "start": 46.2, "end": 46.34, "duration": 0.14000000000000057},
        {
            "text": " computer",
            "start": 46.34,
            "end": 46.6,
            "duration": 0.26000000000000156,
        },
        {
            "text": " files.",
            "start": 46.6,
            "end": 47.120000000000005,
            "duration": 0.5199999999999996,
        },
        {
            "text": " We",
            "start": 47.120000000000005,
            "end": 47.14,
            "duration": 0.019999999999999574,
        },
        {
            "text": " need",
            "start": 47.14,
            "end": 47.239999999999995,
            "duration": 0.09999999999999787,
        },
        {
            "text": " to",
            "start": 47.239999999999995,
            "end": 47.36,
            "duration": 0.120000000000001,
        },
        {"text": " find", "start": 47.36, "end": 47.6, "duration": 0.240000000000002},
        {
            "text": " the",
            "start": 47.6,
            "end": 47.760000000000005,
            "duration": 0.16000000000000014,
        },
        {
            "text": " satellite.",
            "start": 47.760000000000005,
            "end": 48.379999999999995,
            "duration": 0.6199999999999974,
        },
        {
            "text": " Where",
            "start": 48.379999999999995,
            "end": 48.5,
            "duration": 0.120000000000001,
        },
        {
            "text": " would",
            "start": 48.5,
            "end": 48.64,
            "duration": 0.14000000000000057,
        },
        {
            "text": " that",
            "start": 48.64,
            "end": 48.82,
            "duration": 0.17999999999999972,
        },
        {"text": " be", "start": 48.82, "end": 49.04, "duration": 0.21999999999999886},
        {
            "text": " Hey,",
            "start": 53.86,
            "end": 54.22,
            "duration": 0.35999999999999943,
        },
        {
            "text": " I",
            "start": 54.22,
            "end": 54.480000000000004,
            "duration": 0.26000000000000156,
        },
        {
            "text": " got",
            "start": 54.480000000000004,
            "end": 54.6,
            "duration": 0.120000000000001,
        },
        {
            "text": " a",
            "start": 54.6,
            "end": 54.760000000000005,
            "duration": 0.16000000000000014,
        },
        {
            "text": "-",
            "start": 54.760000000000005,
            "end": 54.980000000000004,
            "duration": 0.21999999999999886,
        },
        {
            "text": " I",
            "start": 54.980000000000004,
            "end": 55.14,
            "duration": 0.16000000000000014,
        },
        {
            "text": " have",
            "start": 55.14,
            "end": 55.28,
            "duration": 0.14000000000000057,
        },
        {"text": " a", "start": 55.28, "end": 55.4, "duration": 0.11999999999999744},
        {
            "text": " serious",
            "start": 55.4,
            "end": 55.86,
            "duration": 0.46000000000000085,
        },
        {
            "text": " weapon",
            "start": 55.86,
            "end": 56.260000000000005,
            "duration": 0.40000000000000213,
        },
        {
            "text": " in",
            "start": 56.260000000000005,
            "end": 56.42,
            "duration": 0.16000000000000014,
        },
        {"text": " my", "start": 56.42, "end": 56.56, "duration": 0.13999999999999702},
        {
            "text": " hand",
            "start": 56.56,
            "end": 56.82,
            "duration": 0.26000000000000156,
        },
        {"text": " and", "start": 56.82, "end": 56.94, "duration": 0.120000000000001},
        {"text": " I'm", "start": 56.94, "end": 57.1, "duration": 0.16000000000000014},
        {
            "text": " not",
            "start": 57.1,
            "end": 57.239999999999995,
            "duration": 0.13999999999999702,
        },
        {
            "text": " a",
            "start": 57.239999999999995,
            "end": 57.34,
            "duration": 0.10000000000000142,
        },
        {"text": " f", "start": 57.34, "end": 57.5, "duration": 0.16000000000000014},
        {
            "text": "-",
            "start": 57.5,
            "end": 57.620000000000005,
            "duration": 0.120000000000001,
        },
        {
            "text": " Yeah,",
            "start": 57.620000000000005,
            "end": 58.2,
            "duration": 0.5799999999999983,
        },
        {"text": " okay.", "start": 58.2, "end": 58.78, "duration": 0.5800000000000018},
        {
            "text": " Whoa",
            "start": 58.78,
            "end": 59.120000000000005,
            "duration": 0.33999999999999986,
        },
        {"text": " Oh", "start": 60.0, "end": 60.08, "duration": 0.08},
    ]
    output_file, true_transcript = edit_vid_orchestrator(
        sanitize_filename(id),
        f"{TMP_DOWNLOAD_FOLDER}/{id}.mp4",
        f"tmp/test/{id}.mp4",
        target_size=(1080, 1920),
        start_time=326,
        end_time=334,
        text="music name?",
    )
    LOGGER.info("Output file: %s", output_file)
    LOGGER.info("True transcript: %s", true_transcript)
    
    timestamps_obj = timestamps()
    LOGGER.info(timestamps_obj.get_word_timestamps_openai("tmp/raw/audio_l6oJa69LFuI_whis_err.mp3", 0, audio_clip_length=8))
    LOGGER.info(timestamps_obj.get_word_timestamps_openai("tmp/raw/audio_l6oJa69LFuI_whis_err.mp3", 0))
    LOGGER.info(timestamps_obj.get_word_timestamps_openai("tmp/raw/audio_l6oJa69LFuI_whis_err.mp3", 0, audio_clip_length=1))
    id = "SXoQ5gJLJdY"
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
    text = "what the fuck 😭"
    edit_vid_orchestrator(
        sanitize_filename(id),
        f"{TMP_DOWNLOAD_FOLDER}/{id}.mp4",
        f"tmp/test/{id}.mp4",
        target_size=(1080, 1920),
        start_time=157,
        end_time=165,
        text=text,
    )
    


if __name__ == "__main__":
    main()
