import pyaudio

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
        
        # Check if device supports input (microphone)
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

if __name__ == "__main__":
    list_microphones()