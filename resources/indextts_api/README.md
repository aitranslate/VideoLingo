# IndexTTS API Server

这是 VideoLingo 配套的 IndexTTS 2.0 API 服务器参考实现。

> 官方项目: https://github.com/index-tts/index-tts

## 文件说明

- `api_server.py` - IndexTTS 2.0 Flask API 服务器

## 部署步骤

### 1. 安装依赖

```bash
pip install flask
```

确保已安装 [IndexTTS](https://github.com/index-tts/index-tts) 并配置好模型文件：

```bash
# 目录结构示例
your-indextts-directory/
├── api_server.py          # 从这里复制此文件
├── checkpoints/
│   └── 2.0/
│       ├── config.yaml
│       └── model files...
└── voices/
    ├── voice_01.wav
    ├── voice_02.wav
    └── ...
```

### 2. 复制 API 文件

将 `api_server.py` 复制到你的 IndexTTS 目录中：

```bash
cp resources/indextts_api/api_server.py /path/to/your-indextts/api_server.py
```

### 3. 启动服务器

```bash
cd /path/to/your-indextts
python api_server.py
```

服务器默认运行在 `http://0.0.0.0:9880`

## API 接口

### TTS 接口

**URL:** `http://127.0.0.1:9880/`

**方法:** GET 或 POST

**参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `text` | string | 是 | 要转换的文本 |
| `speaker` | string | 否* | 预设音色文件名 (如 `voice_01`)，放在 `voices/` 目录 |
| `ref_voice` | string | 否* | 自定义参考音频的完整路径 (优先级高于 speaker) |
| `output_format` | string | 否 | 输出格式，默认 `wav` |

> * `speaker` 和 `ref_voice` 二选一

**GET 请求示例:**
```bash
curl "http://127.0.0.1:9880/?text=你好，世界&speaker=voice_01"
```

**POST 请求示例:**
```bash
curl -X POST http://127.0.0.1:9880/ \
  -H "Content-Type: application/json" \
  -d '{"text": "你好，世界", "speaker": "voice_01"}'
```

### 健康检查

**URL:** `http://127.0.0.1:9880/health`

**响应:**
```json
{
  "status": "healthy",
  "device": "cuda",
  "model": "IndexTTS2"
}
```

## 与 VideoLingo 集成

在 VideoLingo 的 `config.yaml` 中配置 IndexTTS：

```yaml
# TTS 配置
tts: "index"

# IndexTTS 配置
index_tts:
  host: "127.0.0.1"  # API 服务器地址
  port: 9880          # API 服务器端口
  mode: "preset"      # 模式: preset/global/dynamic
  speaker: "voice_01" # preset 模式下的音色名称
```

## 三种工作模式

| 模式 | 说明 | 配置 |
|------|------|------|
| `preset` | 使用预设音色 | 设置 `speaker` 为 `voices/` 目录中的音色名 |
| `global` | 全局统一参考音频 | 自动选择 3-10 秒的最佳参考音频用于所有片段 |
| `dynamic` | 每段独立参考音频 | 为每个字幕片段使用对应的原始语音作为参考 |

## 高级参数 (IndexTTS 2.0 特有)

以下参数可选，用于更精细的控制：

| 参数 | 说明 |
|------|------|
| `emo_audio_prompt` | 情感参考音频文件 |
| `emo_alpha` | 情感强度 (0.0-1.0) |
| `emo_vector` | 情感向量 (8个浮点数，逗号分隔) |
| `use_emo_text` | 启用情感文本引导 (true/false) |
| `emo_text` | 情感文本描述 |
| `use_random` | 启用随机采样 (true/false) |
| `interval_silence` | 片段间静音时长，毫秒 |

## 常见问题

### 1. 端口被占用

修改 `api_server.py` 最后一行的 `port=9880` 为其他端口，并同步更新 VideoLingo 的 `config.yaml`。

### 2. CUDA 内存不足

将 `use_fp16=True` 改为 `use_fp16=False` 可减少显存占用。

### 3. 参考音频找不到

确保参考音频路径正确，`speaker` 模式下音频文件应放在 `voices/` 目录。
