import torch
from random import choice
from kokoro import KPipeline

import soundfile as sf
from clip_creator.conf import LOGGER, TTS_VOICES
from transformers import VitsModel, AutoTokenizer
import numpy as np

class TTSModel:
    def __init__(self):
        # Model and tokenizer (choose a VITS model that sounds similar)
        self.model_name = "facebook/mms-tts-eng"  # Example: A multilingual VITS model
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = VitsModel.from_pretrained(self.model_name)

    def text_to_speech(self, text, sample_rate=22050):
        """
        Generates speech from text using a VITS model.

        Args:
            text (str): The text to convert to speech.
            sample_rate (int): The desired sample rate of the output audio.

        Returns:
            numpy.ndarray: The audio waveform as a NumPy array.
        """
        inputs = self.tokenizer(text, return_tensors="pt")
        with torch.no_grad():
            outputs = self.model(**inputs)
            waveform = outputs.waveform[0].numpy()  # Extract the waveform

        return waveform, sample_rate

    def run_it(self, filename, text):

        try:
            waveform, sample_rate = self.text_to_speech(text)

        except Exception as e:
            LOGGER.error(f"An error occurred: {e}")

        # Example of saving the audio to a file
        
        sf.write(filename, waveform, sample_rate)
        LOGGER.info(f"Audio saved to {filename}")

class TTSModelKokoro:
    def __init__(self, voice:int|None=None):
        # Model and tokenizer (choose a VITS model that sounds similar)
        self.kp = KPipeline(lang_code='a')
        if not voice:
            selection = choice(TTS_VOICES)
            
        else:
            selection = TTS_VOICES[voice]
        self.speaker, self.speed = selection[0], selection[1]
    def text_to_speech(self, text, sample_rate=24000):
        """
        Generates speech from text using a VITS model.

        Args:
            text (str): The text to convert to speech.
            sample_rate (int): The desired sample rate of the output audio.

        Returns:
            numpy.ndarray: The audio waveform as a NumPy array.
        """
        generator = self.kp(
                            text, voice=self.speaker, # <= change voice here: af_alloy, af_heart, af_aoede, af_bella, am_echo, am_adam, am_eric
                            speed=self.speed, split_pattern=r'\n+'
                        )
        
        audios = []
        for gs, ps, audio in generator:
            audios.append(audio)
        waveform = np.concatenate(audios, axis=0)
        return waveform, sample_rate

    def run_it(self, filename, text):

        try:
            waveform, sample_rate = self.text_to_speech(text)

        except Exception as e:
            LOGGER.error(f"An error occurred: {e}")

        # Example of saving the audio to a file
        
        sf.write(filename, waveform, sample_rate)
        LOGGER.info(f"Audio saved to {filename}")