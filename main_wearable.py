from typing import Callable
from numpy import ndarray, concatenate, frombuffer
from numpy import float32
from wearable.recording import AudioWatchDog, AudioConfig
import time


import asyncio
from socketio import AsyncClient


audioservice = AudioWatchDog(
    audioConfig=AudioConfig(
        buffer_duration=5,
        sample_rate=44100
    )
)


async def facilitate_audio(
) -> ndarray[float32]:
    global audioservice

    audio_data: list[ndarray[float32]] = []
    audioservice.register_audio_consumer(lambda chunk: audio_data.append(chunk))

    print("\n\n")
    
    audioservice.start_recording()
    time.sleep(5)  # Simulate recording for 5 seconds
    audioservice.stop_recording()

    print(f">> Recorded audio data: {len(audio_data)} chunks")
    
    """
    socket: AsyncClient = AsyncClient()

    joined: bool = False
    configured: bool = False

    @socket.on('join::ACK')
    def join_ack(username: str):
        print(f">>> Joined the server as '{username}'")
        nonlocal joined
        joined = True

    @socket.on('audio::config::ACK')
    def config_ack(data: dict):
        print(f">>> Audio configuration acknowledged.")
        nonlocal configured
        configured = True

    try:
        await socket.connect('ws://localhost:5000')
        print(">> Connected to LocalCoCaptain server.")

        await socket.emit('join', 'Wearable Device')
        print(">> Joining the server as 'Wearable Device'.")

        while not joined:
            await asyncio.sleep(0.2)

        await socket.emit('audio::config', audioservice.audioConfig.dict())
        print(">>> Audio configuration sent to server.")

        while not configured:
            await asyncio.sleep(0.2)

        await socket.disconnect()
        print(">> Disconnected from LocalCoCaptain server.")
    
    except Exception as e:
        print(f"An error occurred while initializing audio recording: {e}")
        return None
    """


if __name__ == "__main__":
    from wearable.utils import chunk_audio, transcribe_audio
    from whisper import load_audio
    
    
    asyncio.run(facilitate_audio())
    
    
    #audio = load_audio("example.mp3")
    #chunks = chunk_audio(audio, 480000)
    #results = transcribe_audio(chunks)
    #print(f">> Transcription Result: {results}")