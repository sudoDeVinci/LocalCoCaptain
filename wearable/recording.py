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
from typing import Literal, Callable
from wearable._types import AudioConfig
from time import sleep
from webrtcvad import Vad
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from multiprocessing import Queue as QueueType
else:
    QueueType = Queue

AudioChunk = ndarray[tuple[Literal[1024]], float32]


class AudioWatchDog:
    """
    AudioWatchDog is a class that manages audio recording for transcription.
    It handles the audio interface, recording process, and transcription process.
    It uses a queue to store audio chunks and a lock to manage access to the audio interface.

    During transcription, it processes audio chunks and transcribes in separate processes.
    The transcribed text is stored in a queue to enable a non-blocking retrieval.

    Attributes:
        audioInterface (pyaudio.PyAudio): The audio interface for recording.
        audioQueue (QueueType[AudioChunk]): Queue to store audio chunks.
        audioConfig (AudioConfig): Configuration for audio recording.
        audioLock (Lock): Lock to manage access to the audio interface.
        isRecording (bool): Flag indicating if recording is active.
        recordingProcess (Process | None): Process for recording audio.
        transcriptionProcess (Process | None): Process for transcribing audio.
        transcription (QueueType[str]): Queue to store transcribed text.
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
        'processManager',
        'voiceActivityDetector',
        'audioConsumers',
    )


    def __init__(
        self,
        audioConfig: AudioConfig,
        audioInterface: Optional[pyaudio.PyAudio] = None,
        audioConsumers: Optional[list[Callable[[], None]]] = None,
        eof: Optional[str] = None
    ) -> None:
        print(">> Initializing AudioWatchDog...")
        self.audioConfig: AudioConfig = audioConfig
        self.audioInterface: pyaudio.PyAudio = audioInterface if audioInterface else pyaudio.PyAudio()
        self.EOF: str | None = eof
        self.voiceActivityDetector: Vad | None = Vad()
        self.voiceActivityDetector.set_mode(0)
        print(f"Audio configuration: {self.audioConfig}")

        # Shared values require a manager to keep syncd
        self.processManager: SyncManager = Manager()
        self.audioQueue: 'QueueType[AudioChunk]' = self.processManager.Queue()
        self.transcription: 'QueueType[str]' = self.processManager.Queue()
        self.isRecording: ValueProxy[bool] = self.processManager.Value(bool, False)

        self.audioConsumers: list[Callable[[], None]] = audioConsumers if audioConsumers else []

        self.audioLock: Lock = Lock()

        self.recordingProcess: Process | None = None
        self.transcriptionProcess: Process | None = None


    def __del__(self):
        if self.isRecording.value:
            self.stop_recording()
        self.audioLock.acquire()
        self.audioInterface.terminate()
        self.audioLock.release()

    def _detect_voice_activity(self, audio_chunk: bytes) -> bool:
        #TODO: Implement a more robust voice activity detection
        return True


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

    def register_audio_consumer(self, callback: Callable) -> None:
        """
        Register a callback function that will be called to process audio chunks.
        This allows for custom processing of audio data in a separate thread or process.
        
        Args:
            callback (Callable): A function that takes no arguments and returns None.
        """
        if not callable(callback):
            raise ValueError("Callback must be a callable function.")
        self.audioConsumers.append(callback)
        print(f"✅ Audio consumer callback registered: {callback.__name__}")


    def _audio_consumer_callback(self) -> None:
        while self.isRecording.value:
            # When there's enough chunks, send for transcription
            if self.audioQueue.qsize() >= self.audioConfig.chunks_per_buffer:
                try:
                    chunk = concatenate(
                        [self.audioQueue.get_nowait() for _ in range(self.audioConfig.chunks_per_buffer)]
                    )
                    for consumer in self.audioConsumers:
                        consumer(chunk)
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
            target=self._audio_consumer_callback,
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
            self.recordingProcess.join(timeout=1.5)
            if self.recordingProcess.is_alive():
                print("Recording process did not terminate gracefully - terminating forcefully.")
                self.recordingProcess.terminate()
        self.recordingProcess = None


        if self.transcriptionProcess and self.transcriptionProcess.is_alive():
            self.transcriptionProcess.join(timeout=1.5)
            if self.transcriptionProcess.is_alive():
                print("Transcription process did not terminate gracefully - terminating forcefully.")
                self.transcriptionProcess.terminate()
        self.transcriptionProcess = None

        # Signal end of transcription
        self.transcription.put(self.EOF)

        print("⏹️ AudioWatchDog stopped.")


