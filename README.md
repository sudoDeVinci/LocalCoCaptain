# LocalCoCaptain

[![Type Checking](https://github.com/sudoDeVinci/HYGP-lasers/actions/workflows/mypy.yml/badge.svg?branch=main)](https://github.com/sudoDeVinci/LocalCoCaptain/actions/workflows/typecheck.yml)
[![Linting](https://github.com/sudoDeVinci/HYGP-lasers/actions/workflows/linting.yml/badge.svg?branch=main)](https://github.com/sudoDeVinci/LocalCoCaptain/actions/workflows/linting.yml)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Locally run AI server extension, tailored for assistance inside wearables.
For simplicity, we just use ollama to communicate and organize models.

- For our main "choreographer", we use [a 4 billion parameter Gemma3 model](https://ollama.com/library/gemma3:4b).

- For our voice transcription, we use [a 37.8 million parameter, miniaturized/quantized version of the popular Whisper model](https://ollama.com/dimavz/whisper-tiny/tags).


## Installation

We only target Ubuntu.

### Ollama Install

First, install Ollama via curl (fastest way).

```bash
    curl -fsSL https://ollama.com/install.sh | sh
```

Install the main coordinator model.
```bash
    ollama pull gemma3:4b
```

Install the voice-to-text transcriber model.
```bash
    ollama pull dimavz/whisper-tiny
```

### Audio-Related Installs

For some basic audio processing tools, we require ffmpeg under the hood.
```bash
    sudo apt update && sudo apt install ffmpeg
```

For our audio transcription, we need to grab some global pre-reqs before creating our virtualenv.

```bash
    sudo apt install portaudio19-dev python3-pyaudio
```
