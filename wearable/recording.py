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
        'transcriptionProcess',
        'transcription',
        'EOF'
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
        eof: str | None = None
    ) -> None:
        self.audioConfig = audioConfig
        self.audioInterface = audioInterface if audioInterface else pyaudio.PyAudio()
        self.audioQueue = queue if queue else Queue()
        self.audioLock = Lock()
        self.EOF = eof


    def __del__(self):
        self.audioLock.acquire()
        self.audioInterface.terminate()
        self.audioLock.release()


    def _detect_voice_activity(self, audiochunk: AudioChunk) -> bool:
        # TODO: Implement voice activity detection logic
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

            isTalking: bool = False

            while self.isRecording:
                #TODO: Check if voice activity is detected - set isTalking to True.
                data = stream.read(self.audioConfig.chunk_size,
                                   exception_on_overflow=False)
                chunk_array: AudioChunk = frombuffer(data, int16).astype(float32) / 32768.0


                if self._detect_voice_activity(chunk_array):
                    self.audioQueue.put(chunk_array)


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
            # When there's enough chunks, send for transcription
            if len(self.audioQueue) >= self.audioConfig.chunks_per_buffer:
                # TODO: send for transcription
                try:
                    self._transcribe_audio()
                except ValueError as err:
                    print(f"Transcription error: {err}")
                    continue


    def _transcribe_audio(self) -> None:
        snippet: AudioChunk = concatenate([self.audioQueue.get() for _ in range(self.audioConfig.chunks_per_buffer)])
        chunks = chunk_audio(audio=snippet)
        text = transcribe_audio(chunks).strip()
        self.transcription.put(text)



    def start_recording(self) -> None:
        if self.isRecording:
            print("Recording is already in progress.")
            return
        
        if not self.audioQueue.empty():
            print("Clearing existing audio queue.")
            while not self.audioQueue.empty():
                self.audioQueue.get()

        
        self.isRecording = True
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
        if not self.isRecording:
            print("Recording is not in progress.")
            return
        
        self.isRecording = False

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
