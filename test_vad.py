import pyaudio
import webrtcvad
import time
from wearable.utils import (
    list_devices,
    list_supported_sample_rates,
    downsample_audio
)


def test_vad_directly(device_index: int = 20):
    """
    Test VAD directly without the full AudioWatchDog class.
    """
    
    print("🎯 Testing webrtcvad directly...")
    
    devices = list_devices()
    print("Available audio input devices:")
    for i, device in enumerate(devices):
        if device['maxInputChannels'] > 0:
            print(f" [{i}] {device['name']} (ID: {device['index']})")

    supported = list_supported_sample_rates(device_index)
    print(f"Supported sample rates for device ID {device_index}: {supported}")
    for rate in supported:
        print(f"  - {rate} Hz")

    # Initialize VAD
    vad = webrtcvad.Vad()
    vad.set_mode(3)  # Aggressiveness level 0-3
    
    # Audio configuration
    sample_rate = 48000

    frame_duration_ms = 30  # 30ms frames
    device_frame_length = int(sample_rate * frame_duration_ms / 1000)
    bytes_per_frame = device_frame_length * 2  # 16-bit audio = 2 bytes per sample

    print(f"Device sample rate: {sample_rate} Hz")
    print(f"Frame duration: {frame_duration_ms} ms")
    print(f"Device frame length: {device_frame_length} samples")
    
    # Initialize PyAudio
    audio = pyaudio.PyAudio()
    
    try:
        stream = audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=sample_rate,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=device_frame_length
        )
        
        print("🎤 Recording for 10 seconds... Speak to test VAD!")
        print("📊 '+' = speech detected, '.' = no speech")
        
        start_time = time.time()
        speech_frames = 0
        total_frames = 0
        
        while time.time() - start_time < 10:
            # Read exactly one frame from device
            data = stream.read(device_frame_length, exception_on_overflow=False)

            if len(data) > 0:
                # Downsample to 16kHz for VAD
                #print("Downsampling...")

                if len(data) >= bytes_per_frame:
                    #downsampled_data = downsample_audio(data, device_sample_rate, vad_sample_rate)
                    frame = data[:bytes_per_frame]
                    
                    try:
                        is_speech = vad.is_speech(frame, sample_rate)
                        print('+' if is_speech else '.', end='', flush=True)
                        
                        if is_speech:
                            speech_frames += 1
                        total_frames += 1
                    except Exception as vad_error:
                        print('E', end='', flush=True)  # Error marker
                        continue
        
        
        print(f"\n\n✅ Test completed!")
        print(f"📊 Speech detected in {speech_frames}/{total_frames} frames ({speech_frames/total_frames*100:.1f}%)")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        if 'stream' in locals():
            stream.stop_stream()
            stream.close()
        audio.terminate()

if __name__ == "__main__":
    test_vad_directly()
