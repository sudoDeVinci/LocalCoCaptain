from whisper import (
    Whisper,
    load_model,
    log_mel_spectrogram,
    DecodingOptions,
    decode as decode_whisper,
)
from numpy import (ndarray,
                   float32,
                   uint32,
                   ceil,
                   zeros,
)

from numba import (njit,
                   types,
                   prange,
)
from typing import List
from torch import (
    inference_mode,
)


TRANSCRIBER: Whisper | None = None
"""
Transcription Whisper model for voice to text conversion.
This model is loaded once and used for all transcriptions.
"""


@njit(
    types.Array(types.float32, 1, 'C')(
        types.Array(types.float32, 1, 'C'),
        types.uint32,
    ),
    fastmath=True,
    cache=True,
)
def pad_or_trim(
    array:ndarray,
    length: uint32=480000
) -> ndarray[float32, 1]:
    """
    NumPy-only pad/trim implementation for Numba use. Performance is about equal.
    """
    # Simple slice for 1D array trimming
    if array.shape[0] > length:
        return array[:length]
    
    # Manual padding for 1D array
    if array.shape[0] < length:
        result = zeros(length, dtype=array.dtype)
        result[:array.shape[0]] = array
        return result
    
    # Return as-is if already the right length
    return array


@njit(
    types.List(types.Array(types.float32, 1, 'C'))(
        types.Array(types.float32, 1, 'C'),
        types.uint32,
    ),
    fastmath=True,
    cache=True,
)
def chunk_audio(audio: ndarray[float32, 1],
                CHUNK_LIM: uint32 = 480000,
) -> List[ndarray[float32]]:
    """
    Chunk audio into fixed-size segments of CHUNK_LIM samples.
    Args:
        audio (ndarray[float32, 1]): Audio sample as a 1D NumPy array.
        CHUNK_LIM (uint32): Length of each chunk in samples (default: 480000, which is 30 seconds at 16kHz).
    Returns:
        List[ndarray[float32]]: List of audio chunks, each padded or trimmed to CHUNK_LIM samples.
    """
    # Pre-allocate arrays for better memory efficiency
    audio_length = audio.shape[0]
    num_chunks = max(1, uint32(ceil(audio_length / CHUNK_LIM)))

    # Pre-allocate the list with zeros
    # Since we either pad or trim each chunk to CHUNK_LIM,
    # we can pre-allocate a 2D array for all chunks
    audios = zeros(shape=(num_chunks, CHUNK_LIM), dtype=float32)

    # if smaller than 30 sec, move on
    if num_chunks == 1:
        padded = pad_or_trim(audio, CHUNK_LIM)
        audios[0] = padded  # Use index instead of append

    # if larger than 30 sec, chunk it and pad last piece
    else:
         # Multiple chunks case
        for i in prange(num_chunks):
            start_idx = i * CHUNK_LIM
            end_idx = min((i + 1) * CHUNK_LIM, audio_length)
            
            # Use NumPy's advanced slicing
            chunk = audio[start_idx:end_idx]
            
            # Only pad if needed
            if len(chunk) < CHUNK_LIM:
                chunk = pad_or_trim(chunk, CHUNK_LIM)
            
            audios[i] = chunk  # Use index instead of append

    return audios


def transcribe_audio(audio: list[ndarray[float32, 1]]) -> str:
    """
    Transcribe audio using Whisper english model
    Args:
        audio (list[ndarray[float32, 1]]): List of audio chunks as 1D NumPy arrays.
    Returns:
        str: Transcribed text from the audio chunks.
    Raises:
        RuntimeError: If the Whisper transcriber fails to initialize.
    Note:
        This function assumes the audio is already preprocessed and in the correct format.
        It uses the Whisper model to decode the audio chunks into text.
        The audio chunks should be in the format expected by Whisper (e.g., 16kHz, mono).
    """

    if TRANSCRIBER is None:
        try:
            init_transcriber()
        except Exception as e:
            raise RuntimeError("Failed to initialize Whisper transcriber") from e

    device = TRANSCRIBER.device
    options = DecodingOptions(
        temperature=0,              # Temperature to 0 for deterministic results
        fp16=False,                 # No clue why but fp16 is leagues slower
        language="en",              # Set language to English - usually faster
        without_timestamps=True,    # Skip timestamp generation
        beam_size=1                 # Smaller beam size is faster
    )

    results: list[str] = []
    with inference_mode():
        for i, chunk in enumerate(audio):
            # make log-Mel spectrogram and move to the same device as the model
            mel = log_mel_spectrogram(chunk).to(device)
            result = decode_whisper(TRANSCRIBER, mel, options)
            if result is not None and result.text:
                results.append(result.text.strip())

    return " ".join(results)


def init_transcriber(model_name: str = "base") -> None:
    """
    Initialize the Whisper transcriber model.
    Args:
        model_name (str): Name of the Whisper model to load (default: "base").
    """
    global TRANSCRIBER

    TRANSCRIBER = load_model(model_name, in_memory=True) if TRANSCRIBER is None else TRANSCRIBER