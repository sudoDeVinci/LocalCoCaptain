import pyaudio
import wave
from os import environ
from numpy import frombuffer, float32, int16, ndarray, concatenate
from io import BytesIO
from subprocess import CalledProcessError, run

# Suppress ALSA error messages
environ['ALSA_PCM_CARD'] = 'default'
environ['ALSA_PCM_DEVICE'] = '0'

def list_microphones():
    """List all available audio input devices (microphones)"""
    # Initialize PyAudio
    p = pyaudio.PyAudio()
    
    print("Available microphones:")
    print("-" * 50)
    
    # Get the number of audio devices
    device_count = p.get_device_count()
    
    for i in range(device_count):
        device_info = p.get_device_info_by_index(i)
        
        # Check if device supports input (microphone)ä
        if device_info['maxInputChannels'] > 0:
            print(f"Device {i}: {device_info['name']}")
            print(f"  Max Input Channels: {device_info['maxInputChannels']}")
            print(f"  Default Sample Rate: {device_info['defaultSampleRate']}")
            print(f"  Host API: {p.get_host_api_info_by_index(device_info['hostApi'])['name']}")
            print()
    
    # Get default input device
    try:
        default_device = p.get_default_input_device_info()
        print(f"Default microphone: Device {default_device['index']} - {default_device['name']}")
    except OSError:
        print("No default input device found")
    
    # Clean up
    p.terminate()

def record_audio(device_index: int = 1,
                          duration: int = 5,
                          sample_rate: int = 16000,
                          chunk_size: int = 1024
) -> ndarray[float32]:
    """
    Record audio directly as NumPy array, avoiding unnecessary conversions
    """
    p = pyaudio.PyAudio()
    
    format = pyaudio.paInt16
    channels = 1
    chunk_count = int(sample_rate / chunk_size * duration)
    
    # Pre-allocate NumPy array for efficiency
    audio_data = []
    
    try:
        stream = p.open(
            format=format,
            channels=channels,
            rate=sample_rate,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=chunk_size
        )
        
        print(f"Recording for {duration} seconds...")
        
        for i in range(chunk_count):
            data = stream.read(chunk_size)
            # Convert directly to float32 without intermediate storage
            chunk_array = frombuffer(data, int16).astype(float32) / 32768.0
            audio_data.append(chunk_array)
        
        stream.stop_stream()
        stream.close()

    except ValueError as err:
        print(f"Error: {err}")
        print("Please check if the device index is correct and the microphone is connected.")
        
    finally:
        p.terminate()    
        # Concatenate all chunks efficiently
        return concatenate(audio_data)

# Update your main section:
if __name__ == "__main__":
    from audio_to_text import transcribe_audio, chunk_audio
    DURATION = 10
    SAMPLE_RATE = 16000  # Match your target sample rate
    CHUNK_SIZE = 1024
    
    print("\n" + "="*50)
    # Get audio directly as NumPy array
    audio = record_audio(
        device_index=1,
        duration=DURATION,
        sample_rate=SAMPLE_RATE,
        chunk_size=CHUNK_SIZE
    )
    
    chunks = chunk_audio(audio=audio, CHUNK_LIM=480000)
    results = transcribe_audio(chunks)
    print(f"\n\n\n>> Transcription ::: {results}\n\n")
