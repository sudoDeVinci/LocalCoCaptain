import pyaudio
import wave
import numpy as np
import python_speech_features as psf
import whisper

TRANSCRIBER = whisper.load_model("base")

def preprocess_audio(file_path):
    chunk = 1024
    wf = wave.open(file_path, 'rb')
    p = pyaudio.PyAudio()

    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)

    data = wf.readframes(chunk)

    while data:
        stream.write(data)
        data = wf.readframes(chunk)

    stream.stop_stream()
    stream.close()
    p.terminate()

def extract_features(audio_data, sample_rate: int):
    mfcc_features = psf.mfcc(audio_data, samplerate=sample_rate, numcep=13)
    return mfcc_features