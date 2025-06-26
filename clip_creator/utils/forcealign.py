import torch
import os
import torchaudio
from forcealign import ForceAlign
from forcealign.transcriber import speech_to_text
from forcealign.utils import alphabetical, get_breath_idx
from clip_creator.conf import LOGGER
from clip_creator.tts.audio_edit import split_audio_at_timestamps, find_splits_each_sm, audio_length

def force_align_aiyt(file: str, yt_ft_transcript: str, device: str):
    '''
    This version of force_align is used for AIYT, which splits the audio file into smaller segments so the gpu can handle it.
    '''
    LOGGER.debug("Force aligning audio %s, %s", file, yt_ft_transcript)
    
    number_of_splits = find_splits_each_sm(file, length=2)  # Get split points in the audio file
    files_list = split_audio_at_timestamps(file, number_of_splits)
    full_transcript = []
    running_offset = 0  # Initialize running offset for timestamps
    for split_file in files_list:
        
        align = ForceAlignFix(audio_file=split_file, transcript=yt_ft_transcript, device=device)

        # Run prediction and return alignment results
        words = align.inference()

        # Show predicted word-level alignments
        ts_trans = []
        for word in words:
            LOGGER.debug(
                f"Word: {word.word}, Start: {word.time_start}s, End: {word.time_end}s"
            )
            ts_trans.append({
                "text": word.word,
                "start": word.time_start  + running_offset,  # Adjust start time with running offset
                "end": word.time_end + running_offset,  # Adjust end with running offset,
                "duration": word.time_end - word.time_start,
            })
        del align  # Clean up to free memory
        del words
        os.remove(split_file)  # Remove the split file after processing
        full_transcript.extend(ts_trans)
        running_offset += audio_length(split_file)  # Update running offset
    return full_transcript
def force_align(file: str, yt_ft_transcript: str, device: str):
    # Provide path to audio file and corresponding transcript
    LOGGER.debug("Force aligning audio %s, %s", file, yt_ft_transcript)
    align = ForceAlignFix(audio_file=file, transcript=yt_ft_transcript, device=device)

    # Run prediction and return alignment results
    words = align.inference()

    # Show predicted word-level alignments
    ts_trans = []
    for word in words:
        LOGGER.debug(
            f"Word: {word.word}, Start: {word.time_start}s, End: {word.time_end}s"
        )
        ts_trans.append({
            "text": word.word,
            "start": word.time_start,
            "end": word.time_end,
            "duration": word.time_end - word.time_start,
        })
    del align  # Clean up to free memory
    del words
    return ts_trans
class ForceAlignFix(ForceAlign):
    def __init__(self, audio_file: str, transcript: str = None, device: str = "cuda"):
        """Turns an audio file with a transcript into a force alignment

        Args:
            audio_file (str): Path to an audio file of a person talking.
            transcript (str, optional): Text transcript. If None, transcript will be generated automatically.
        """
        self.device = device
        self.SPEECH_FILE = audio_file
        self.bundle = torchaudio.pipelines.WAV2VEC2_ASR_BASE_960H
        self.model = self.bundle.get_model().to(self.device)
        self.labels = self.bundle.get_labels()
        self.dictionary = {c: i for i, c in enumerate(self.labels)}

        # Load and preprocess audio
        self._load_audio()

        # Handle transcript
        if transcript is None:
            print("No transcript provided. Generating transcript using speech_to_text...")
            self.raw_text = speech_to_text(self.SPEECH_FILE)  # Use transcriber.speech_to_text
            print(f"Generated Transcript: {self.raw_text}")
        else:
            self.raw_text = transcript

        text = alphabetical(self.raw_text).upper().split()
        self.transcript = f'{"|".join(text)}|'
        self.tokens = [self.dictionary[c] for c in self.transcript]
        self.breath_idx = get_breath_idx(self.raw_text)
        self.word_alignments = None
        self.phoneme_alignments = []