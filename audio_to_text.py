from whisper import (
    Whisper,
    load_model,
    load_audio,
    log_mel_spectrogram,
    DecodingOptions,
    decode as decode_whisper,
)
from numpy import (ndarray,
                   float32,
                   uint32,
                   ceil,
                   zeros)

from numba import (njit,
                   jit,
                   types,
                   prange,
)
from typing import List
import os
from torch import cuda
from datetime import datetime
import torch


TRANSCRIBER: Whisper = load_model("base",
                                  device="cuda" if cuda.is_available() else "cpu",
                                  in_memory=True)
print(f">> Using device: {TRANSCRIBER.device}\n")
os.environ["OMP_NUM_THREADS"] = "4"
torch.set_num_threads(4)
if torch.cuda.is_available():
    torch.backends.cudnn.benchmark = True  # May help with repeated operations


@njit(
    types.Array(types.float32, 1, 'C')(
        types.Array(types.float32, 1, 'C'),
        types.uint32,
    ),
    fastmath=True,
    cache=True,
)
def pad_or_trim(array:ndarray,
                      length: uint32=480000
) -> ndarray[float32, 1]:
    """NumPy-only version optimized for Numba"""
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
def chunk_audio(audio: ndarray[float32],
                CHUNK_LIM: uint32 = 480000,
) -> List[ndarray[float32]]:
    # Pre-allocate arrays for better memory efficiency
    audio_length = audio.shape[0]
    num_chunks = max(1, uint32(ceil(audio_length / CHUNK_LIM)))
    audios = [zeros(shape=(1,),
                    dtype=float32)] * num_chunks

    # if smaller than 30 sec, move on
    if audio_length <= CHUNK_LIM:
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
    """Transcribe audio using Whisper"""
    device = TRANSCRIBER.device
    options = DecodingOptions(
        temperature=0,
        fp16=False,  # No clue why but fp16 is leagues slower
        language="en",
        without_timestamps=True,  # Skip timestamp generation
        beam_size=1  # Smaller beam size is faster
    )

    # Pre-allocate the results list with the exact size needed
    results = [""] * len(audio)
    # audio = [snippet.astype(dtype=float16, order='C', copy=False) for snippet in audio]
    with torch.inference_mode():
        for i, chunk in enumerate(audio):
            # make log-Mel spectrogram and move to the same device as the model
            mel = log_mel_spectrogram(chunk).to(device)
            result = decode_whisper(TRANSCRIBER, mel, options)
            results[i]+=result.text

    return " ".join(results)