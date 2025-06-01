import pyaudio
from os import environ
from numpy import (
    frombuffer,
    float32,
    int16,
    concatenate,
    ndarray
)

from multiprocessing import Queue, Process
from threading import Lock
from typing import Literal
from wearable.audio_to_text import transcribe_audio, chunk_audio
from wearable._types import AudioConfig

AudioChunk = ndarray[tuple[Literal[1024]], float32]



# Suppress ALSA error messages
environ['ALSA_PCM_CARD'] = 'default'
environ['ALSA_PCM_DEVICE'] = '0'




class AudioWatchDog:
    """
    AudioWatchDog is a class that manages audio recording for transcription.
    It handles the audio interface, recording process, and transcription process.
    It uses a queue to store audio chunks and a lock to manage access to the audio interface.

    During transcription, it processes audio chunks and transcribes in separate processes.
    The transcribed text is stored in a queue to enable a non-blocking retrieval.

    Attributes:
        audioInterface (pyaudio.PyAudio): The audio interface for recording.
        audioQueue (Queue[AudioChunk]): Queue to store audio chunks.
        audioConfig (AudioConfig): Configuration for audio recording.
        audioLock (Lock): Lock to manage access to the audio interface.
        isRecording (bool): Flag indicating if recording is active.
        recordingProcess (Process | None): Process for recording audio.
        transcriptionProcess (Process | None): Process for transcribing audio.
        transcription (Queue[str]): Queue to store transcribed text.
    """
    __slots__ = (
        'audioInterface',
        'audioQueue',
        'audioConfig',
        'audioLock',
        'isRecording',
        'recordingProcess',
        'transcriptionProcess'
    )
    
    audioInterface: pyaudio.PyAudio
    audioQueue: Queue[AudioChunk]
    audioConfig: AudioConfig
    audioLock: Lock
    isRecording: bool = False
    recordingProcess: Process | None = None
    transcriptionProcess: Process | None = None
    transcription: Queue[str] = Queue()


    def __init__(
        self,
        audioConfig: AudioConfig,
        queue: Queue | None = None,
        audioInterface: pyaudio.PyAudio | None = None,
    ) -> None:
        self.audioConfig = audioConfig
        self.audioInterface = audioInterface if audioInterface else pyaudio.PyAudio()
        self.audioQueue = queue if queue else Queue()
        self.audioLock = Lock()


    def __del__(self):
        self.audioLock.acquire()
        self.audioInterface.terminate()
        self.audioLock.release()
    

    def get_interface(self, timeout=1.0) -> pyaudio.PyAudio:
        aquired = self.audioLock.acquire(timeout=timeout)
        out = self.audioInterface if aquired else None
        if aquired:
            self.audioLock.release()
        return out


    def _audio_producer_callback(self) -> None:
        try:
            self.audioLock.acquire()

            stream = self.audioInterface.open(
                format=self.audioConfig.format,
                channels=self.audioConfig.channels,
                rate=self.audioConfig.sample_rate,
                input=True,
                input_device_index=self.audioConfig.device_index,
                frames_per_buffer=self.audioConfig.chunk_size
            )

            print("🎤 Recording started... ")

            isTalking: bool = False

            while self.isRecording:
                # Check if voice activity is detected - set isTalking to True.
                data = stream.read(self.audioConfig.chunk_size,
                                   exception_on_overflow=False)

                if isTalking:
                    # TODO: Maybe this should be a separate process, to preprocess the audio data
                    chunk_array: AudioChunk = frombuffer(data, int16).astype(float32) / 32768.0
                    self.audioQueue.put(chunk_array)

                else:
                    # If no voice activity, skip processing
                    continue

        except ValueError as err:
            print(f"Error: {err}")
            print("Please check if the device index is correct and the microphone is connected.")
        
        finally:
            if 'stream' in locals():
                stream.stop_stream()
                stream.close()
            self.audioLock.release()
            print("🎤 Recording stopped.")


    def _audio_transcriber_callback(self) -> None:
        while self.isRecording and not self.audioQueue.empty():
            # Move audio chunk into temporary queue to build up snippet
            audio_chunk = self.audioQueue.get(timeout=1.0)

            # When there's enough chunks, send for transcription
            if len(self.audioQueue) >= self.audioConfig.chunks_per_buffer:
                # TODO: send for transcription
                self._transcribe_audio()


    def _transcribe_audio(self) -> None:
        snippet: AudioChunk = concatenate([self.audioQueue.get() for _ in range(self.audioConfig.chunks_per_buffer)])
        chunks = chunk_audio(audio=snippet)
        text = transcribe_audio(chunks).strip()
        self.transcription.put(text)

if __name__ == "__main__":
    
    DURATION = 10
    SAMPLE_RATE = 16000  # Match your target sample rate
    CHUNK_SIZE = 1024
    
    print("\n" + "="*50)