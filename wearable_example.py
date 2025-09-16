from typing import Callable, Final, Optional
from numpy import ndarray, concatenate, frombuffer
from numpy import float32
from wearable.recording import AudioWatchDog, AudioConfig, AudioChunk
import time
import asyncio
from whisper import load_audio
from wearable.utils import (
    transcribe_audio,
    chunk_audio,
    downsample_audio,
    init_transcriber,
    list_devices,
    list_supported_sample_rates,
    get_default_input_device,
    PaDeviceInfo
)

from copy import deepcopy

DEVICE: Final[Optional[PaDeviceInfo]] = get_default_input_device()
print(f">> Using default input device: {DEVICE['name']} (ID: {DEVICE['index']})")

audioservice = AudioWatchDog(
    audioConfig=AudioConfig(
        buffer_duration=3,
        sample_rate=48000,
        device_index=DEVICE['index'] if DEVICE else None,
        channels=1,
    )
)


def facilitate_audio(
) -> ndarray[float32]:
    global audioservice

    audio_data: list[AudioChunk] = []

    def audio_consumer(chunk: AudioChunk) -> None:
        print(f">> Received audio chunk of size: {len(chunk)} bytes")
        audio_data.append(deepcopy(chunk))
        print(f">> Total collected chunks: {len(audio_data)}")

    audioservice.register_audio_consumer(audio_consumer)

    print("\n\n")
    
    audioservice.start_recording()
    time.sleep(5)  # Simulate recording for 5 seconds
    audioservice.stop_recording()

    print(f">> Recorded audio data: {len(audio_data)} chunks")


if __name__ == "__main__":
    facilitate_audio()
    
    #init_transcriber()
    #audio = load_audio("example.mp3")
    #chunks = chunk_audio(audio, 480000)
    #results = transcribe_audio(chunks)
    #print(f">> Transcription Result: {results}")
