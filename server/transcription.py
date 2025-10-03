from whisper import (
    Whisper,
    load_model,
    load_audio,
    log_mel_spectrogram,
    DecodingOptions,
    decode as decode_whisper,
)

from numpy import (
    ndarray,
    float32,
    uint32,
    int16,
    ceil,
    zeros,
    frombuffer
)

from numba import (
    njit,
    types,
    prange,
)

from typing import Final, TypedDict, Optional, Any

from torch import (
    inference_mode,
    device as torch_device,
    cuda
)
from pyaudio import PyAudio, paInt16









