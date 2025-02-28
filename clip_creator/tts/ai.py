import torch
import sounddevice as sd
import soundfile as sf
from transformers import VitsModel, AutoTokenizer

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

    def play_audio(self, waveform, sample_rate):
        """
        Plays the generated audio.

        Args:
            waveform (numpy.ndarray): The audio waveform.
            sample_rate (int): The sample rate of the audio.
        """
        sd.play(waveform, samplerate=sample_rate)
        sd.wait()  # Wait until playback is finished
    def run_it(self):
        text = "Hello, this is a test of the AI voice."

        try:
            waveform, sample_rate = self.text_to_speech(text)
            self.play_audio(waveform, sample_rate)

        except Exception as e:
            print(f"An error occurred: {e}")

        # Example of saving the audio to a file
        
        filename = "output.wav"
        sf.write(filename, waveform, sample_rate)
        print(f"Audio saved to {filename}")
    