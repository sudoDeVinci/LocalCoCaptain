from pyaudio import paInt16


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
    """

    __slots__ = (
        'device_index',
        'sample_rate',
        'chunk_size',
        'format',
        'channels'
        'buffer_duration',
        'chunks_per_buffer'
    )

    device_index: int
    sample_rate: int
    chunk_size: int
    format: int
    channels: int
    buffer_duration: int

    def __init__(
        self,
        device_index: int = 1,
        sample_rate: int = 16000,
        chunk_size: int = 1024,
        format: int = paInt16,
        channels: int = 1,
        buffer_duration: int = 2
    ) -> None:
        self.device_index = device_index
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.format = format
        self.channels = channels
        self.buffer_duration = buffer_duration
        self.chunks_per_buffer = int(sample_rate * buffer_duration / chunk_size)