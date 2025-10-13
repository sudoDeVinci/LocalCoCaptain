from ._types import PaDeviceInfo, AudioConfig

from .transcription import (
    TRANSCRIBER,
    DEVICE,
    downsample_audio,
    pad_or_trim,
    chunk_audio,
    transcriber_init_hook,
    transcribe_audio,
)
