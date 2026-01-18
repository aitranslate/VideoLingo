<div align="center">

<img src="/resources/logo.png" alt="VideoLingo Logo" height="140">

# 连接世界每一帧

<a href="https://trendshift.io/repositories/12200" target="_blank"><img src="https://trendshift.io/api/badge/repositories/12200" alt="Huanshere%2FVideoLingo | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>

[**简体中文**](/README.md) ｜  [**English**](/translations/README.en.md)

**QQ群：875297969**

</div>

## 📝 我的修改与优化

### 最近更新
- **2025-01**: 使用 `audio-separator[gpu]==0.41.0` 替代 `demucs` 以实现更好的人声分离
  - 更新所有依赖到最新版本（PyTorch 2.8.0、WhisperX 等）
  - 移除基于云端的转录渠道（elevenlabs、whisperX_302）
  - 将音频输出格式从 MP3 改为 WAV 以获得更高质量
  - 简化安装流程，支持自动 GPU 检测
- **2025-01**: 添加 **IndexTTS 2.0** 集成，支持 3 种模式（preset/global/dynamic）
  - 移除所有基于 API 的 TTS 服务（302.ai、SiliconFlow）以保护隐私
  - 现在仅支持本地/离线 TTS：Edge TTS、GPT-SoVITS、IndexTTS、Custom TTS

### 技术改进
- 修复 PyTorch 2.6+ 与 omegaconf 的兼容性问题
- 使用 audio-separator 的 Kim_Vocal_2.onnx 模型优化音频处理流程
- 清理不必要的文件和代码
- 更新翻译和配置

---

## 🌟 简介

VideoLingo 是一站式视频翻译本地化配音工具，能够一键生成 Netflix 级别的高质量字幕，告别生硬机翻，告别多行字幕，还能加上高质量的克隆配音，让全世界的知识能够跨越语言的障碍共享。

主要特点和功能：
- 🎥 使用 yt-dlp 从 Youtube 链接下载视频

- **🎙️ 使用 WhisperX 进行单词级和低幻觉字幕识别**

- **📝 使用 NLP 和 AI 进行字幕分割**

- **📚 自定义 + AI 生成术语库，保证翻译连贯性**

- **🔄 三步直译、反思、意译，实现影视级翻译质量**

- **✅ 按照 Netflix 标准检查单行长度，绝无双行字幕**

- **🗣️ 支持 Edge TTS、GPT-SoVITS、IndexTTS、Custom TTS 本地配音方案**

- 🚀 一键启动，在 streamlit 中一键出片

- 📝 详细记录每步操作日志，支持随时中断和恢复进度

与同类项目相比的优势：**绝无多行字幕，最佳的翻译质量，无缝的配音体验**

## 🎥 演示

<table>
<tr>
<td width="33%">

### 双语字幕
---
https://github.com/user-attachments/assets/a5c3d8d1-2b29-4ba9-b0d0-25896829d951

</td>
<td width="33%">

### Cosy2 声音克隆
---
https://github.com/user-attachments/assets/e065fe4c-3694-477f-b4d6-316917df7c0a

</td>
<td width="33%">

### GPT-SoVITS 配音
---
https://github.com/user-attachments/assets/47d965b2-b4ab-4a0b-9d08-b49a7bf3508c

</td>
</tr>
</table>

## 安装

> **注意:** 在 Windows 上使用 NVIDIA GPU 加速需要先完成以下步骤:
> 1. 安装 [CUDA Toolkit 12.6](https://developer.download.nvidia.com/compute/cuda/12.6.0/local_installers/cuda_12.6.0_560.76_windows.exe)
> 2. 安装 [CUDNN 9.3.0](https://developer.download.nvidia.com/compute/cudnn/9.3.0/local_installers/cudnn_9.3.0_windows.exe)
> 3. 将 `C:\Program Files\NVIDIA\CUDNN\v9.3\bin\12.6` 添加到系统环境变量 PATH 中
> 4. 重启电脑

> **注意:** FFmpeg 是必需的，请通过包管理器安装：
> - Windows：```winget install ffmpeg```（Windows 自带包管理器）
> - macOS：```brew install ffmpeg```（通过 [Homebrew](https://brew.sh/)）
> - Linux：```sudo apt install ffmpeg```（Debian/Ubuntu）

1. 克隆仓库

```bash
git clone https://github.com/aitranslate/VideoLingo.git
cd VideoLingo
```

2. 安装依赖（需要 `python=3.10`）

```bash
conda create -n videolingo python=3.10.0 -y
conda activate videolingo
python install.py
```

3. 启动应用

```bash
streamlit run st.py
```

## API
VideoLingo 支持 OpenAI-Like API 格式和本地 TTS 接口：
- LLM: `claude-3-5-sonnet`, `gpt-4.1`, `deepseek-v3`, `gemini-2.0-flash`, ...（按效果排序）
- WhisperX: 本地运行 WhisperX (large-v3)
- TTS（仅支持本地/离线）：`edge-tts`（免费）、`GPT-SoVITS`（本地克隆）、`IndexTTS`（本地克隆）、`custom-tts`（自定义）

> **注意：** IndexTTS 支持 3 种模式：**preset**（预设音色）、**global**（3-10秒参考音频用于所有片段）、**dynamic**（每段使用单独的参考音频）

## 📁 资源目录

`resources/` 目录包含用于扩展 VideoLingo 的参考资料和资源文件：

```
resources/
├── logo.png          # VideoLingo 标志 (PNG 格式)
├── logo.svg          # VideoLingo 标志 (SVG 格式，用作网页图标)
└── indextts_api/
    ├── api_server.py # IndexTTS 2.0 Flask API 服务器参考实现
    └── README.md     # IndexTTS 详细设置和使用指南
```

### 使用 IndexTTS 配合 VideoLingo

1. 安装 [IndexTTS](https://github.com/index-tts/index-tts) 并下载所需模型
2. 将 `resources/indextts_api/api_server.py` 复制到你的 IndexTTS 目录
3. 启动 API 服务器：`python api_server.py`
4. 在 VideoLingo 的 `config.yaml` 中配置：
   ```yaml
   tts: "index"
   index_tts:
     host: "127.0.0.1"
     port: 9880
     mode: "preset"  # 或 "global" / "dynamic"
     speaker: "voice_01"
   ```

详细说明请参阅 `resources/indextts_api/README.md`。

## 当前限制
1. WhisperX 转录效果可能受到视频背景声影响，因为使用了 wav2vac 模型进行对齐。对于背景音乐较大的视频，请开启人声分离增强。另外，如果字幕以数字或特殊符号结尾，可能会导致提前截断，这是因为 wav2vac 无法将数字字符（如"1"）映射到其发音形式（"one"）。

2. 使用较弱模型时容易在中间过程报错，这是因为对响应的 json 格式要求较为严格。如果出现此错误，请删除 `output` 文件夹后更换 llm 重试，否则重复执行会读取上次错误的响应导致同样错误。

3. 配音功能由于不同语言的语速和语调差异，还受到翻译步骤的影响，可能不能 100% 完美，但本项目做了非常多的语速上的工程处理，尽可能保证配音效果。

4. **多语言视频转录识别仅仅只会保留主要语言**，这是由于 whisperX 在强制对齐单词级字幕时使用的是针对单个语言的特化模型，会因为不认识另一种语言而删去。

5. **无法多角色分别配音**，whisperX 的说话人区分效果不够好用。

## 📄 许可证

本项目采用 Apache 2.0 许可证，衷心感谢以下开源项目的贡献：

[whisperX](https://github.com/m-bain/whisperX), [yt-dlp](https://github.com/yt-dlp/yt-dlp), [json_repair](https://github.com/mangiucugna/json_repair), [BELLE](https://github.com/LianjiaTech/BELLE)

## 📬 联系

- 加入 QQ 群寻求解答：875297969
- 在 GitHub 上提交 [Issues](https://github.com/Huanshere/VideoLingo/issues) 或 [Pull Requests](https://github.com/Huanshere/VideoLingo/pulls)
- 关注我的 Twitter：[@Huanshere](https://twitter.com/Huanshere)
- 联系邮箱：team@videolingo.io

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=Huanshere/VideoLingo&type=Timeline)](https://star-history.com/#Huanshere/VideoLingo&Timeline)