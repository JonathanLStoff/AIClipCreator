import librosa
from pydub.utils import mediainfo
from pydub import AudioSegment
from pathlib import Path
import numpy as np
import soundfile as sf
import os
import wave

from clip_creator.conf import LOGGER

def find_silence(audio_file, silence_threshold=40, min_silence_length=10):
    """
    Finds silent segments in an audio file.

    Args:
        audio_file (str): Path to the audio file.
        silence_threshold (float): Silence threshold in dBFS.
        min_silence_length (int): Minimum length of silence in milliseconds.

    Returns:
        list: List of tuples containing start and end times of silent segments.
    """
    y, sr = librosa.load(audio_file, sr=None)
    non_silent_intervals = librosa.effects.split(y, top_db=silence_threshold, frame_length=2048, hop_length=512)
    non_silent_intervals_ms = [(s / sr * 1000, e / sr * 1000) for s, e in non_silent_intervals]
    silence_intervals = []
    for i in range(len(non_silent_intervals_ms) - 1):
        end_prev = non_silent_intervals_ms[i][1]
        start_next = non_silent_intervals_ms[i+1][0]
        silence_duration = start_next - end_prev

        if silence_duration >= min_silence_length:
            silence_intervals.append((end_prev, start_next))
    return silence_intervals

def find_splits_each_sm(audio_file, length=2):
    """
    Finds split points in an audio file based on silence detection.
    """
    audio_length = librosa.get_duration(path=audio_file)
    audio_length_ms = (audio_length)*1000  # 27.8 minutes in milliseconds
    runs_count = audio_length / (length*60) # number of runs in 2 minutes
    clip_parts:list[float] = []
    for i in range(1,int(runs_count+1)):
        start_run = i * 2 * 60 * 1000
        for start, end in find_silence(audio_file, silence_threshold=40, min_silence_length=400):
            if start >= start_run:
                clip_parts.append((start + end)/2)  # Average of start and end times
                break  # Stop after the first silence found in this run
    return clip_parts
def find_splits_each_trans(transcript:list[dict], length=5):
    """
    Finds split points in an transcript based on period detection.
    """
    audio_length = transcript[-1]["duration"] +  transcript[-1]["start"] # Assuming the last entry has the total duration
    runs_count = audio_length / (length*60) # number of runs in 2 minutes
    clip_parts:list[list[dict]] = []
    for i in range(0,int(runs_count)):
        tmp_clip_parts: list[dict] = []
        start_run = i * length * 60
        end_run = (i + 1) * length * 60
        if end_run > audio_length or i == runs_count - 1:
            end_run = audio_length
        for idx, section in enumerate(transcript):
            if section["start"] < start_run:
                continue
            elif section["start"] >= start_run and section["start"] < end_run and tmp_clip_parts==[] and idx!=0:
                tmp_clip_parts.append(transcript[idx-1])  # Add the previous section if it exists
                tmp_clip_parts.append(section)
            elif section["start"] > start_run and section["start"] < end_run:
                tmp_clip_parts.append(section)
            elif section["start"] >= end_run and section["start"] - end_run > length*5 and end_run != audio_length: # Avoid adding sections that are too far from the end of the run
                tmp_clip_parts.append(section)  # Average of start and end times
                break
            elif section["start"] >= end_run and end_run != audio_length:
                for end_of_word in [".", "!", "?"]:
                    if end_of_word in section['text']:
                        tmp_clip_parts.append(section)
                        break
                break  # Stop after the first silence found in this run
            else:
                tmp_clip_parts.append(section)
        clip_parts.append(tmp_clip_parts)

    return clip_parts
def combine_audio_files(audio_files: list, output_file: str):
    """
    Combines multiple audio files into a single audio file.
    """
    combined = AudioSegment.empty()
    for audio_file in audio_files:
        if os.path.exists(audio_file):
            LOGGER.debug(f"Combining audio file: {audio_file}")
            segment = AudioSegment.from_file(audio_file)
            combined += segment
        else:
            LOGGER.warning(f"Audio file {audio_file} does not exist. Skipping.")
    combined.export(output_file, format="wav")
    for audio_file in audio_files:
        try:
            os.remove(audio_file)  # Clean up individual files after combining
        except Exception as e:
            LOGGER.error(f"Error removing file {audio_file}: {e}")

def audio_length(audio_file: str) -> float:
    """
    Returns the length of the audio file in seconds.
    Args:
        audio_file (str): Path to the audio file that is a wav.
    Returns:
        float: Length of the audio file in seconds.
    """
    with wave.open(audio_file, 'rb') as wf:
        frames = wf.getnframes()
        framerate = wf.getframerate()
        duration = frames / float(framerate)
        return duration
def split_audio_at_timestamps(audio_file, timestamps_ms:list):
    """
    Splits the audio file at the given list of millisecond timestamps.

    Args:
        audio_file (str): Path to the audio file.
        timestamps_ms (list): List of timestamps in milliseconds to split at.

    Returns:
        list: List of file paths to the split audio segments.
    """
    y, sr = librosa.load(audio_file, sr=None)
    timestamps = [0] + sorted([int(ts) for ts in timestamps_ms]) + [int(len(y) / sr * 1000)]
    output_files = []
    base_name = audio_file.rsplit('.', 1)[0]
    for i in range(len(timestamps) - 1):
        start_sample = int(timestamps[i] * sr / 1000)
        end_sample = int(timestamps[i+1] * sr / 1000)
        segment = y[start_sample:end_sample]
        out_file = f"{base_name}_part{i+1}.wav"
        sf.write(out_file, segment, sr)
        output_files.append(out_file)
    return output_files
if __name__ == "__main__":
    audio_file = "tmp/test/SCXX6n7iy0w.wav"
    splits = find_splits_each_sm(audio_file, length=2)