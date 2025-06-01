import pyaudio
from os import environ
from numpy import (
    frombuffer,
    float32,
    int16,
    concatenate,
    ndarray
)

from multiprocessing import Queue, Process, Manager
from multiprocessing.managers import SyncManager, ValueProxy
from threading import Lock
from typing import Literal
from wearable.utils import transcribe_audio, chunk_audio
from wearable._types import AudioConfig
from time import sleep
from webrtcvad import Vad

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
        'EOF',
        'audioInterface',
        'audioQueue',
        'audioConfig',
        'audioLock',
        'isRecording',
        'recordingProcess',
        'transcriptionProcess',
        'transcription',
        'processManager'
        'voiceActivityDetector',
    )

    EOF: str | None = None 
    audioInterface: pyaudio.PyAudio
    audioQueue: Queue[AudioChunk]
    audioConfig: AudioConfig
    audioLock: Lock = Lock()

    isRecording: ValueProxy[bool]
    recordingProcess: Process | None = None
    transcriptionProcess: Process | None = None
    transcription: Queue[str]
    processManager: SyncManager

    voiceActivityDetector: Vad | None = None

    def __init__(
        self,
        audioConfig: AudioConfig,
        audioInterface: pyaudio.PyAudio | None = None,
        eof: str | None = None
    ) -> None:
        self.audioConfig = audioConfig
        self.audioInterface = audioInterface if audioInterface else pyaudio.PyAudio()
        self.EOF = eof
        self.voiceActivityDetector = Vad()
        self.voiceActivityDetector.set_mode(0)

        # Shared values require a manager to keep syncd
        self.processManager = Manager()
        self.audioQueue = self.processManager.Queue()
        self.transcription = self.processManager.Queue()
        self.isRecording = self.processManager.Value(bool, False)


    def __del__(self):
        if hasattr(self, 'isRecording') and self.isRecording.value:
            self.stop_recording()
        self.audioLock.acquire()
        self.audioInterface.terminate()
        self.audioLock.release()


    def _detect_voice_activity(self, audiochunk: AudioChunk) -> bool:
        return self.voiceActivityDetector.is_speech(
            audiochunk.tobytes(),
            sample_rate=self.audioConfig.sample_rate
        )


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


            while self.isRecording.value:
                data = stream.read(self.audioConfig.chunk_size,
                                   exception_on_overflow=False)


                if self._detect_voice_activity(data):
                    chunk_array: AudioChunk = frombuffer(data, int16).astype(float32) / 32768.0
                    self.audioQueue.put(chunk_array)


        except Exception as err:
            print(f"Error recording Audio ::: {err}")
            # Signal end of processing
            self.isRecording.value = False
        
        finally:
            if 'stream' in locals():
                stream.stop_stream()
                stream.close()
            self.audioLock.release()
            print("🎤 Recording stopped.")


    def _audio_transcriber_callback(self) -> None:
        while self.isRecording.value:
            # When there's enough chunks, send for transcription
            if self.audioQueue.qsize() >= self.audioConfig.chunks_per_buffer:
                try:
                    self._transcribe_audio()
                except ValueError as err:
                    print(f"Transcription error: {err}")
                    continue
            else:
                sleep(0.1)

        # If recording is stopped, process any remaining audio chunks
        while not self.audioQueue.empty():
            if self.audioQueue.qsize() >= self.audioConfig.chunks_per_buffer:
                try:
                    self._transcribe_audio()
                except ValueError as err:
                    print(f"Transcription error: {err}")
                    break


    def _transcribe_audio(self) -> None:
        snippet: AudioChunk = concatenate([self.audioQueue.get() for _ in range(self.audioConfig.chunks_per_buffer)])
        chunks = chunk_audio(audio=snippet)
        text = transcribe_audio(chunks).strip()
        self.transcription.put(text)



    def start_recording(self) -> None:
        if self.isRecording.value:
            print("Recording is already in progress.")
            return
        
        if not self.audioQueue.empty():
            print("Clearing existing audio queue.")
            while not self.audioQueue.empty():
                self.audioQueue.get_nowait()

        
        self.isRecording.value = True
        self.recordingProcess = Process(
            target=self._audio_producer_callback,
            name="AudioProducer"
        )

        self.transcriptionProcess = Process(
            target=self._audio_transcriber_callback,
            name="AudioTranscriber"
        )

        self.recordingProcess.start()
        self.transcriptionProcess.start()


        print("🚀 AudioWatchDog started.")


    def stop_recording(self) -> None:
        if not self.isRecording.value:
            print("Recording is not in progress.")
            return
        
        self.isRecording.value = False

        if self.recordingProcess and self.recordingProcess.is_alive():
            self.recordingProcess.join(timeout=1.0)
            if self.recordingProcess.is_alive():
                print("Recording process did not terminate gracefully - terminating forcefully.")
                self.recordingProcess.terminate()
        self.recordingProcess = None


        if self.transcriptionProcess and self.transcriptionProcess.is_alive():
            self.transcriptionProcess.join(timeout=1.0)
            if self.transcriptionProcess.is_alive():
                print("Transcription process did not terminate gracefully - terminating forcefully.")
                self.transcriptionProcess.terminate()
        self.transcriptionProcess = None

        # Signal end of transcription
        self.transcription.put(self.EOF)

        print("⏹️ AudioWatchDog stopped.")


