from whisper import (
    Whisper,
    load_model,
    load_audio,
    pad_or_trim,
    log_mel_spectrogram,
    DecodingOptions,
    decode as decode_whisper,
)
import numpy as np
from typing import List
import os
from torch import cuda
from datetime import datetime
import torch

TRANSCRIBER: Whisper = load_model("base",
                                  device="cuda" if cuda.is_available() else "cpu",
                                  in_memory=True)
print(f">> Using device: {TRANSCRIBER.device}\n")
os.environ["OMP_NUM_THREADS"] = "4"  # Set to number of physical cores
torch.set_num_threads(4)  # Same as above
if torch.cuda.is_available():
    torch.backends.cudnn.benchmark = True  # May help with repeated operations

def chunk_audio(audio: np.ndarray, CHUNK_LIM: int = 480000) -> str:

    # Pre-allocate arrays for better memory efficiency
    audio_length = len(audio)
    num_chunks = max(1, int(np.ceil(audio_length / CHUNK_LIM)))
    # Pre-allocate the audios array instead of appending
    audios = [None] * num_chunks
    device = TRANSCRIBER.device
    options = DecodingOptions(
        temperature=0,
        fp16=False,
        language="en",
        without_timestamps=True,  # Skip timestamp generation
        beam_size=1  # Smaller beam size is faster
    )

    # if smaller than 30 sec, move on
    if audio_length <= CHUNK_LIM:
        padded = pad_or_trim(audio)
        audios[0] = padded  # Use index instead of append

    # if larger than 30 sec, chunk it and pad last piece
    else:
         # Multiple chunks case
        for i in range(num_chunks):
            start_idx = i * CHUNK_LIM
            end_idx = min((i + 1) * CHUNK_LIM, audio_length)
            
            # Use NumPy's advanced slicing
            chunk = audio[start_idx:end_idx]
            
            # Only pad if needed
            if len(chunk) < CHUNK_LIM:
                chunk = pad_or_trim(chunk)
            
            audios[i] = chunk  # Use index instead of append

    # Pre-allocate the results list with the exact size needed
    results = [None] * len(audios)

    with torch.inference_mode():
        for i, chunk in enumerate(audios):
            # make log-Mel spectrogram and move to the same device as the model
            mel = log_mel_spectrogram(chunk).to(device)
            result = decode_whisper(TRANSCRIBER, mel, options)
        results[i] = result.text

    return " ".join(results)


audio = load_audio("example.mp3")
audio = np.ascontiguousarray(audio, dtype=np.float32)
start = datetime.now()
results = chunk_audio(audio)
end = datetime.now()

print(f">> Result: {results}")
print(f">> Time taken: {end - start}")