import pyaudio
import wave
import time

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

def record_audio(device_index=None, duration=5, sample_rate=44100, chunk_size=1024, output_file="recording.wav"):
    """
    Record audio from a microphone
    
    Args:
        device_index: Index of the microphone device (None for default)
        duration: Recording duration in seconds
        sample_rate: Sample rate for recording
        chunk_size: Buffer size
        output_file: Output WAV file path
    """
    # Initialize PyAudio
    p = pyaudio.PyAudio()
    
    # Audio format settings
    format = pyaudio.paInt16  # 16-bit resolution
    channels = 1  # Mono recording
    
    try:
        # Open audio stream
        stream = p.open(
            format=format,
            channels=channels,
            rate=sample_rate,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=chunk_size
        )
        
        print(f"Recording for {duration} seconds...")
        print("Speak now!")
        
        frames = []
        
        # Record audio in chunks
        for i in range(0, int(sample_rate / chunk_size * duration)):
            data = stream.read(chunk_size)
            frames.append(data)
            
            # Optional: show progress
            if i % (sample_rate // chunk_size) == 0:
                remaining = duration - (i * chunk_size / sample_rate)
                print(f"Time remaining: {remaining:.1f}s", end="\r")
        
        print("\nRecording finished!")
        
        # Stop and close stream
        stream.stop_stream()
        stream.close()
        
        # Save to WAV file
        with wave.open(output_file, 'wb') as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(p.get_sample_size(format))
            wf.setframerate(sample_rate)
            wf.writeframes(b''.join(frames))
        
        print(f"Audio saved to: {output_file}")
        
    except Exception as e:
        print(f"Error during recording: {e}")
    finally:
        p.terminate()

def play_audio(file_path):
    """
    Play back a WAV audio file
    
    Args:
        file_path: Path to the WAV file to play
    """
    try:
        # Open the WAV file
        with wave.open(file_path, 'rb') as wf:
            # Initialize PyAudio
            p = pyaudio.PyAudio()
            
            # Open audio stream for playback
            stream = p.open(
                format=p.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True
            )
            
            print(f"Playing: {file_path}")
            
            # Read and play audio in chunks
            chunk_size = 1024
            data = wf.readframes(chunk_size)
            
            while data:
                stream.write(data)
                data = wf.readframes(chunk_size)
            
            print("Playback finished!")
            
            # Clean up
            stream.stop_stream()
            stream.close()
            p.terminate()
            
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found")
    except Exception as e:
        print(f"Error during playback: {e}")

if __name__ == "__main__":
    # List available microphones first
    list_microphones()
    
    # Record from default microphone for 5 seconds
    print("\n" + "="*50)
    record_audio(
        device_index=2,
        duration=5,
        output_file="test_recording.wav")
    
    from audio_to_text import load_audio, transcribe_audio, chunk_audio
    
    audio = load_audio("test_recording.wav")
    chunks = chunk_audio(audio, 44100)
    results = transcribe_audio(chunks)
    print(f">> Transcription Result: {results}")