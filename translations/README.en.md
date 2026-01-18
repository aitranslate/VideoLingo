<div align="center">

<img src="/resources/logo.png" alt="VideoLingo Logo" height="140">

# Connect the World, Frame by Frame

<a href="https://trendshift.io/repositories/12200" target="_blank"><img src="https://trendshift.io/api/badge/repositories/12200" alt="Huanshere%2FVideoLingo | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>

[**简体中文**](/README.md) ｜  [**English**](/translations/README.en.md)

</div>

## 📝 My Modifications & Improvements

### Recent Updates
- **2025-01**: Replaced `demucs` with `audio-separator[gpu]==0.41.0` for better vocal separation
  - Updated all dependencies to latest versions (PyTorch 2.8.0, WhisperX, etc.)
  - Removed cloud-based transcription channels (elevenlabs, whisperX_302)
  - Changed audio output format from MP3 to WAV for better quality
  - Simplified installation process with automatic GPU detection
- **2025-01**: Added **IndexTTS 2.0** integration with 3 modes (preset/global/dynamic)
  - Removed all API-based TTS services (302.ai, SiliconFlow) for privacy
  - Now only supports local/offline TTS: Edge TTS, GPT-SoVITS, IndexTTS, Custom TTS

### Technical Improvements
- Fixed PyTorch 2.6+ compatibility issues with omegaconf
- Optimized audio processing pipeline with audio-separator's Kim_Vocal_2.onnx model
- Removed unnecessary files and cleaned up codebase
- Updated translations and configuration

---

## 🌟 Overview

VideoLingo is an all-in-one video translation, localization, and dubbing tool aimed at generating Netflix-quality subtitles. It eliminates stiff machine translations and multi-line subtitles while adding high-quality dubbing, enabling global knowledge sharing across language barriers.

Key features:
- 🎥 YouTube video download via yt-dlp

- **🎙️ Word-level and Low-illusion subtitle recognition with WhisperX**

- **📝 NLP and AI-powered subtitle segmentation**

- **📚 Custom + AI-generated terminology for coherent translation**

- **🔄 3-step Translate-Reflect-Adaptation for cinematic quality**

- **✅ Netflix-standard, Single-line subtitles Only**

- **🗣️ Local dubbing with GPT-SoVITS, IndexTTS, Edge TTS**

- 🚀 One-click startup and processing in Streamlit

- 📝 Detailed logging with progress resumption

Difference from similar projects: **Single-line subtitles only, superior translation quality, seamless dubbing experience**

## 🎥 Demo

<table>
<tr>
<td width="33%">

### Dual Subtitles
---
https://github.com/user-attachments/assets/a5c3d8d1-2b29-4ba9-b0d0-25896829d951

</td>
<td width="33%">

### Cosy2 Voice Clone
---
https://github.com/user-attachments/assets/e065fe4c-3694-477f-b4d6-316917df7c0a

</td>
<td width="33%">

### GPT-SoVITS with my voice
---
https://github.com/user-attachments/assets/47d965b2-b4ab-4a0b-9d08-b49a7bf3508c

</td>
</tr>
</table>

## Installation

> **Note:** For Windows users with NVIDIA GPU, follow these steps before installation:
> 1. Install [CUDA Toolkit 12.6](https://developer.download.nvidia.com/compute/cuda/12.6.0/local_installers/cuda_12.6.0_560.76_windows.exe)
> 2. Install [CUDNN 9.3.0](https://developer.download.nvidia.com/compute/cudnn/9.3.0/local_installers/cudnn_9.3.0_windows.exe)
> 3. Add `C:\Program Files\NVIDIA\CUDNN\v9.3\bin\12.6` to your system PATH
> 4. Restart your computer

> **Note:** FFmpeg is required. Please install it via package managers:
> - Windows: ```winget install ffmpeg``` (built-in package manager)
> - macOS: ```brew install ffmpeg``` (via [Homebrew](https://brew.sh/))
> - Linux: ```sudo apt install ffmpeg``` (Debian/Ubuntu)

1. Clone the repository

```bash
git clone https://github.com/aitranslate/VideoLingo.git
cd VideoLingo
```

2. Install dependencies(requires `python=3.10`)

```bash
conda create -n videolingo python=3.10.0 -y
conda activate videolingo
python install.py
```

3. Start the application

```bash
streamlit run st.py
```

## APIs
VideoLingo supports OpenAI-Like API format and local TTS interfaces:
- LLM: `claude-3-5-sonnet`, `gpt-4.1`, `deepseek-v3`, `gemini-2.0-flash`, ... (sorted by performance)
- WhisperX: Run whisperX (large-v3) locally
- TTS (Local/Offline only): `edge-tts` (free), `GPT-SoVITS` (local cloning), `IndexTTS` (local cloning), `custom-tts` (DIY)

> **Note:** IndexTTS supports 3 modes: **preset** (preset voices), **global** (3-10s reference for all segments), **dynamic** (per-segment reference)

## 📁 Resources Directory

The `resources/` directory contains reference materials and assets for extending VideoLingo:

```
resources/
├── logo.png          # VideoLingo logo (PNG format)
├── logo.svg          # VideoLingo logo (SVG format, used as favicon)
└── indextts_api/
    ├── api_server.py # Reference Flask API server for IndexTTS 2.0
    └── README.md     # Detailed IndexTTS setup and usage guide
```

### Using IndexTTS with VideoLingo

To use IndexTTS 2.0 for local dubbing:

1. Install [IndexTTS](https://github.com/index-tts/index-tts) and download the required models
2. Copy `resources/indextts_api/api_server.py` to your IndexTTS directory
3. Start the API server: `python api_server.py`
4. Configure VideoLingo in `config.yaml`:
   ```yaml
   tts: "index"
   index_tts:
     host: "127.0.0.1"
     port: 9880
     mode: "preset"  # or "global" / "dynamic"
     speaker: "voice_01"
   ```

See `resources/indextts_api/README.md` for detailed instructions.

## Current Limitations

1. WhisperX transcription performance may be affected by video background noise, as it uses wav2vac model for alignment. For videos with loud background music, please enable Voice Separation Enhancement. Additionally, subtitles ending with numbers or special characters may be truncated early due to wav2vac's inability to map numeric characters (e.g., "1") to their spoken form ("one").

2. Using weaker models can lead to errors during processes due to strict JSON format requirements for responses (tried my best to prompt llm😊). If this error occurs, please delete the `output` folder and retry with a different LLM, otherwise repeated execution will read the previous erroneous response causing the same error.

3. The dubbing feature may not be 100% perfect due to differences in speech rates and intonation between languages, as well as the impact of the translation step. However, this project has implemented extensive engineering processing for speech rates to ensure the best possible dubbing results.

4. **Multilingual video transcription recognition will only retain the main language**. This is because whisperX uses a specialized model for a single language when forcibly aligning word-level subtitles, and will delete unrecognized languages.

5. **For now, cannot dub multiple characters separately**, as whisperX's speaker distinction capability is not sufficiently reliable.

## 📄 License

This project is licensed under the Apache 2.0 License. Special thanks to the following open source projects for their contributions:

[whisperX](https://github.com/m-bain/whisperX), [yt-dlp](https://github.com/yt-dlp/yt-dlp), [json_repair](https://github.com/mangiucugna/json_repair), [BELLE](https://github.com/LianjiaTech/BELLE)

## 📬 Contact Me

- Submit [Issues](https://github.com/Huanshere/VideoLingo/issues) or [Pull Requests](https://github.com/Huanshere/VideoLingo/pulls) on GitHub
- DM me on Twitter: [@Huanshere](https://twitter.com/Huanshere)
- Email me at: team@videolingo.io

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=Huanshere/VideoLingo&type=Timeline)](https://star-history.com/#Huanshere/VideoLingo&Timeline)

---

<p align="center">If you find VideoLingo helpful, please give me a ⭐️!</p>
