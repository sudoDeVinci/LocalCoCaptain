from pyaudio import paInt16
from typing import TypedDict, Any


class AudioConfig:
    """
    Configuration parameters for audio recording.

    Attributes:
        device_index (int): Index of the audio input device.
        sample_rate (int): Sample rate for the audio recording.
        chunk_size (int): Size of each audio chunk in frames.
        format (int): Audio format, e.g., pyaudio.paInt16.
        channels (int): Number of audio channels, e.g., 1 for mono, 2 for stereo.
        buffer_duration (int): Duration of the audio buffer in seconds.
        chunks_per_buffer (int): Number of chunks that fit into the buffer duration.
    """

    __slots__ = (
        'device_index',
        'sample_rate',
        'chunk_size',
        'frame_duration_ms',
        'format',
        'channels',
        'buffer_duration',
        'chunks_per_buffer'
    )

    device_index: int
    sample_rate: int
    frame_duration_ms: int
    chunk_size: int
    format: int
    channels: int
    buffer_duration: int

    def __init__(
        self,
        device_index: int = 1,
        sample_rate: int = 48000,
        format: int = paInt16,
        channels: int = 1,
        frame_duration_ms: int = 30,
        buffer_duration: int = 2
    ) -> None:
        self.frame_duration_ms = frame_duration_ms
        self.device_index = device_index
        self.sample_rate = sample_rate
        self.chunk_size = 2 * (int(sample_rate * frame_duration_ms / 1000))
        self.format = format
        self.channels = channels
        self.buffer_duration = buffer_duration
        self.chunks_per_buffer = int(sample_rate * buffer_duration / self.chunk_size)

    def dict(self) -> dict:
        """
        Convert the configuration to a dictionary.

        Returns:
            dict: Dictionary representation of the audio configuration.
        """
        return {
            'device_index': self.device_index,
            'sample_rate': self.sample_rate,
            'chunk_size': self.chunk_size,
            'format': self.format,
            'channels': self.channels,
            'buffer_duration': self.buffer_duration
        }
    
class PaDeviceInfo(TypedDict):
    """
    Reflection of PyAudio's device info dictionary structure.
    That in-turn mirrors PortAudio's PaDeviceInfo structure.

    Attributes:
        index (int): The index of the audio device.
        structVersion (Any): The version of the structure.
        name (str): The name of the audio device.
        hostApi (Any): The host API associated with the device.
        maxInputChannels (int): Maximum number of input channels supported by the device.
        maxOutputChannels (int): Maximum number of output channels supported by the device.
        defaultLowInputLatency (float): Default low input latency in seconds.
        defaultLowOutputLatency (float): Default low output latency in seconds.
        defaultHighInputLatency (float): Default high input latency in seconds.
        defaultHighOutputLatency (float): Default high output latency in seconds.
        defaultSampleRate (float): Default sample rate in Hz.
    """
    index: int
    structVersion: Any
    name: str
    hostApi: Any
    maxInputChannels: int
    maxOutputChannels: int
    defaultLowInputLatency: float
    defaultLowOutputLatency: float
    defaultHighInputLatency: float
    defaultHighOutputLatency: float
    defaultSampleRate: float

