from pyaudio import paInt16
from typing import Literal, TypedDict, Any, Optional

SampleRate = Literal[8000, 16000, 22050, 32000, 44100, 48000]


class AudioConfig:
    """
    Configuration parameters for audio recording.

    Attributes:
        device_index (int): Index of the audio input device.
        sample_rate (int): Sample rate for the audio recording.
    """

    __slots__ = (
        "device_index",
        "sample_rate",
        "format",
        "channels",
        "frame_size",
        "bytes_per_frame",
        "frame_duration_ms",
        "frames_per_buffer",
    )

    def __init__(
        self,
        device_index: Optional[int] = None,
        sample_rate: int = 48000,
        format: int = paInt16,
        channels: int = 1,
        frame_duration_ms: int = 30,
        buffer_duration_seconds: int = 3,
    ) -> None:
        self.frame_duration_ms = frame_duration_ms
        self.device_index = device_index
        self.sample_rate = sample_rate
        self.format = format
        self.channels = channels

        self.frame_size = int(self.sample_rate * self.frame_duration_ms / 1000)
        self.bytes_per_frame = self.frame_size * 2  # 16-bit audio = 2 bytes per sample
        self.frames_per_buffer = int(
            (self.sample_rate * buffer_duration_seconds) / self.frame_size
        )

    def dict(self) -> dict:
        """
        Convert the configuration to a dictionary.

        Returns:
            dict: Dictionary representation of the audio configuration.
        """
        return {
            "device_index": self.device_index,
            "sample_rate": self.sample_rate,
            "format": self.format,
            "channels": self.channels,
            "frame_duration_ms": self.frame_duration_ms,
            "frame_size": self.frame_size,
            "bytes_per_frame": self.bytes_per_frame,
        }

    def __str__(self):
        return f"AudioConfig(device_index={self.device_index}, sample_rate={self.sample_rate}, format={self.format}, channels={self.channels}, frame_duration_ms={self.frame_duration_ms}, frame_size={self.frame_size}, bytes_per_frame={self.bytes_per_frame})"


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
