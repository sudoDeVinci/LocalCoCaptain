from whisper import load_model

from typing import Optional

from pyaudio import PyAudio, paInt16

from ..common import transcriber_init_hook, PaDeviceInfo, DEVICE, TRANSCRIBER


def init_transcriber(model_name: str = "base") -> None:
    """
    Initialize the Whisper transcriber model.
    This is for local transscribtion, which we would rather not do.
    Args:
        model_name (str): Name of the Whisper model to load (default: "base").
    """
    global TRANSCRIBER

    TRANSCRIBER = (
        load_model(model_name, device=DEVICE, in_memory=True)
        if TRANSCRIBER is None
        else TRANSCRIBER
    )


transcriber_init_hook = init_transcriber


def list_devices() -> list[PaDeviceInfo]:
    """
    List available audio input devices using PyAudio.
    Returns:
        list[PaDeviceInfo]: A list of dictionaries containing device information.
    """
    audio = PyAudio()
    device_count = audio.get_device_count()
    devices = []

    for i in range(device_count):
        device_info = audio.get_device_info_by_index(i)
        devices.append(device_info)

    audio.terminate()
    return devices


def get_default_input_device() -> Optional[PaDeviceInfo]:
    """
    Get the default audio input device using PyAudio.
    Returns:
        device (Optional[PaDeviceInfo]): A dictionary containing device information, or None if no default input device is found.
    """
    try:
        devices = list_devices()
        for device in devices:
            if device["name"].lower() == "default" and device["maxInputChannels"] > 0:
                return device
    except Exception:
        return None

    return None


def list_supported_sample_rates(device_index: int) -> list[int]:
    """
    List supported sample rates for a given audio input device.
    Args:
        device_index (int): The index of the audio input device.
    Returns:
        list[int]: A list of supported sample rates in Hz.
    """
    audio = PyAudio()
    supported_rates = []
    test_rates = [8000, 16000, 22050, 44100, 48000]

    for rate in test_rates:
        try:
            if audio.is_format_supported(
                rate=rate,
                input_device=device_index,
                input_channels=1,
                input_format=paInt16,
            ):
                supported_rates.append(rate)
        except:
            pass

    audio.terminate()
    return supported_rates
