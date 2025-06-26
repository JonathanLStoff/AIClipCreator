from random import choice

import numpy as np
import soundfile as sf
import torch
from kokoro import KPipeline
from transformers import AutoTokenizer, VitsModel

from clip_creator.conf import LOGGER, TTS_VOICES


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
        LOGGER.debug(f"Audio saved to {filename}")


class TTSModelKokoro:
    def __init__(self, voice: tuple | None = None, lang_code: str = "a"):
        # Model and tokenizer (choose a VITS model that sounds similar)
        self.kp = KPipeline(lang_code=lang_code)
        if not voice:
            selection = choice(TTS_VOICES)

        else:
            selection = voice

        self.speaker, self.speed = selection[0], selection[1]
    def stop(self):
        """
        Stops the text-to-speech pipeline if it is running.
        """
        del self.kp
        del self.speaker
        del self.speed
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
            text, # pronouce a different way like [Misaki](/misˈɑki/) or [Kokoro](/kəˈkɔroʊ/) to test the TTS model
            voice=self.speaker,  # <= change voice here: af_alloy, af_heart, af_aoede, af_bella, am_echo, am_adam, am_eric
            speed=self.speed,
            split_pattern=r"\n+",
        )

        audios = []
        for _gs, _ps, audio in generator:
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
        LOGGER.debug(f"Audio saved to {filename}")
