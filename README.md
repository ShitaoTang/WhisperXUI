# WhisperXUI

**WhisperXUI** is a lightweight web interface built with Flask for transcribing audio/video using [whisper.cpp](https://github.com/ggerganov/whisper.cpp), and optionally translating the subtitles into multiple languages using an AI API (currently supports [DeepSeek](https://deepseek.com/)). Transcribed videos can be played back with multiple selectable subtitle tracks via [MPV player](https://mpv.io/).

## Features

- 📄 Transcribe audio/video files (currently supports English).
- 🌍 Translate subtitles to:
  - Simplified Chinese (`zh-cn`)
  - Traditional Chinese (`zh-hk`)
  - Japanese (`ja`)
  - Korean (`ko`)
- 🎞️ Fullscreen video playback via MPV with selectable subtitle tracks.

## Requirements

- Python
- [whisper.cpp](https://github.com/ggerganov/whisper.cpp) (cloned as a submodule)
- [MPV player](https://mpv.io/) installed and accessible via terminal
- A valid API key for AI service (Only Deepseek is tested)

## Python Dependencies

Install dependencies in a virtual environment:

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Installation & Setup

### 1. Clone the repository

```sh
git clone --recurse-submodules https://github.com/ShitaoTang/WhisperXUI.git
cd WhisperXUI
```

> If you forgot --recurse-submodules, run:

```sh
git submodule update --init --recursive
```

### 2. Build whisper.cpp

```sh
cd whisper.cpp
make
```

Ensure models/ contains at least one model (e.g. ggml-base.en.bin). If not, download it manually or via models/download-ggml-model.sh. You can check the [whisper.cpp documentation](https://github.com/ggerganov/whisper.cpp) for more details.

**⚠️Note:** `gen.sh` uses whisper.cpp/models/ggml-base.en.bin for transcription. If you want to apply other models, just download it and rewrite the path in `gen.sh`.

### 3. Install MPV

- On macOS:

```sh
brew install mpv
```

- On Ubuntu/Debian:

```sh
sudo apt install mpv
```

### 4. Set up API Key

Create a .env file in the project root:

```sh
echo "DEEPSEEK_API_KEY=<your_api_key>" > .env
```

## Usage

Start the Flask server:

```sh
python app.py
```

Then open your browser and visit:

```
http://127.0.0.1:5000
```

### Steps:
1. Upload an audio or video file (preferably English-speaking).
2. Select translation languages (optional).
3. Click the **Transcribe** button.
4. Wait for transcription and translation.
5. Once subtitles are displayed, click the **🎞️ Play with MPV** button.
6. Press **J** in MPV to switch between multiple subtitle tracks.

## Demo

[Here]() is a demo video of WhisperXUI in action.

## Limitations

- Only tested with English input speech.
- Translation only tested with DeepSeek API.
- ❗ **Not real-time**: the system works in batch mode — transcription and translation are performed after file upload, not live.

## License
This project is licensed under the MIT License.
