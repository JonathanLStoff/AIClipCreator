from forcealign import ForceAlign
from clip_creator.conf import LOGGER

def force_align(file:str, yt_ft_transcript:str, device:str):
    
    # Provide path to audio file and corresponding transcript
    align = ForceAlign(audio_file=file, transcript=yt_ft_transcript)

    # Run prediction and return alignment results
    words = align.inference()

    # Show predicted word-level alignments
    ts_trans = []
    for word in words:
        LOGGER.info(f"Word: {word.word}, Start: {word.time_start}s, End: {word.time_end}s")
        ts_trans.append({"text": word.word, "start": word.time_start, "end": word.time_end})
    return ts_trans