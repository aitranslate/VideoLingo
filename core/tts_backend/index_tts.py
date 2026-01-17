import os
import requests
import socket
import time
import subprocess
from pathlib import Path
from pydub import AudioSegment
from core.utils import *
from core.utils.models import *

# IndexTTS2 API 配置
try:
    INDEXTTS_HOST = load_key("index_tts.host")
except KeyError:
    INDEXTTS_HOST = "127.0.0.1"

try:
    INDEXTTS_PORT = load_key("index_tts.port")
except KeyError:
    INDEXTTS_PORT = 9880

INDEXTTS_API_URL = f"http://{INDEXTTS_HOST}:{INDEXTTS_PORT}"

# 全局缓存：找到的最佳参考音频 URL
_CACHED_REF_AUDIO = None


def check_index_tts_server():
    """检查 IndexTTS 服务器是否运行"""
    try:
        response = requests.get(f"{INDEXTTS_API_URL}/health", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def ensure_index_tts_server():
    """确保 IndexTTS 服务器正在运行"""
    if check_index_tts_server():
        rprint("[green]✅ IndexTTS server is running[/green]")
        return True

    rprint("[yellow]⚠️ IndexTTS server is not running[/yellow]")
    rprint("[yellow]Please start your IndexTTS API server first:[/yellow]")
    rprint(f"[cyan]→ API URL: {INDEXTTS_API_URL}[/cyan]")
    rprint("[yellow]Example command to start:[/yellow]")
    rprint("[cyan]python your_indextts_api.py[/cyan]")

    # 询问用户是否已手动启动服务器
    from InquirerPy import inquirer
    from translations.translations import translate as t

    if inquirer.confirm(
        message=t("Have you started the IndexTTS server?"),
        default=False
    ).execute():
        if check_index_tts_server():
            rprint("[green]✅ IndexTTS server detected![/green]")
            return True

    raise Exception("IndexTTS server is not running. Please start it first.")


@except_handler("Failed to generate audio using IndexTTS", retry=2, delay=1)
def index_tts(text: str, save_path: str, speaker: str = None, ref_voice: str = None) -> bool:
    """
    调用 IndexTTS API 生成语音

    Args:
        text: 要转换的文本
        save_path: 保存路径
        speaker: 预设音色名称 (如 "voice_01")
        ref_voice: 自定义参考音频完整路径

    Returns:
        bool: 成功返回 True
    """
    params = {"text": text}

    if ref_voice:
        # 转换为绝对路径
        ref_voice_abs = str(Path(ref_voice).resolve())
        params["ref_voice"] = ref_voice_abs
        rprint(f"[cyan]🎤 Using custom reference audio:[/cyan] {ref_voice_abs}")
    elif speaker:
        params["speaker"] = speaker
        rprint(f"[cyan]🎤 Using preset speaker:[/cyan] {speaker}")
    else:
        raise ValueError("Either 'speaker' or 'ref_voice' must be provided")

    # 调用 IndexTTS API
    response = requests.get(
        INDEXTTS_API_URL,
        params=params,
        timeout=60
    )

    if response.status_code == 200:
        # 确保目录存在
        save_path_obj = Path(save_path)
        save_path_obj.parent.mkdir(parents=True, exist_ok=True)

        # 保存音频文件
        with open(save_path, 'wb') as f:
            f.write(response.content)

        rprint(f"[green]✅ Audio saved to:[/green] {save_path}")
        return True
    else:
        error_msg = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
        raise Exception(f"IndexTTS API error (HTTP {response.status_code}): {error_msg}")


def find_best_ref_audio(task_df, min_duration=3.0, max_duration=10.0):
    """
    找到最佳参考音频 (3-10秒)

    Args:
        task_df: 任务数据框
        min_duration: 最小时长 (秒)
        max_duration: 最大时长 (秒)

    Returns:
        str: 参考音频路径，找不到返回 None
    """
    rprint(f"[blue]🎯 Looking for best reference audio ({min_duration}s-{max_duration}s)...[/blue]")

    # 按优先级查找：先找单段符合的，再找合并后符合的
    # 1. 优先找单个符合 3-10 秒的片段
    for _, row in task_df.iterrows():
        duration = row['duration']
        if min_duration <= duration <= max_duration:
            ref_path = f"{_AUDIO_REFERS_DIR}/{row['number']}.wav"
            if Path(ref_path).exists():
                rprint(f"[green]✅ Found single segment: {row['number']}.wav ({duration:.2f}s)[/green]")
                return ref_path

    # 2. 没有单段符合的，合并多段
    rprint(f"[yellow]⏭️ No single segment found, combining multiple segments...[/yellow]")

    combined = AudioSegment.empty()
    selected_files = []
    total_duration = 0

    for _, row in task_df.iterrows():
        if total_duration >= max_duration:
            break

        audio_path = f"{_AUDIO_REFERS_DIR}/{row['number']}.wav"
        if not Path(audio_path).exists():
            continue

        audio = AudioSegment.from_wav(audio_path)
        combined += audio
        selected_files.append(audio_path)
        total_duration = len(combined) / 1000.0  # ms to seconds

        if total_duration >= min_duration:
            break

    if total_duration < min_duration:
        rprint(f"[red]❌ Could not reach minimum duration {min_duration}s (got {total_duration:.2f}s)[/red]")
        return None

    # 保存合并的参考音频
    combined_ref = f"{_AUDIO_REFERS_DIR}/index_tts_refer.wav"
    combined.export(combined_ref, format="wav")
    rprint(f"[green]✅ Created combined reference: {len(selected_files)} segments, {total_duration:.2f}s[/green]")

    return combined_ref


def index_tts_for_videolingo(text: str, save_as: str, number: int, task_df):
    """
    VideoLingo 集成的 IndexTTS 入口函数

    Args:
        text: 翻译后的文本
        save_as: 保存路径
        number: 当前片段编号
        task_df: 任务数据框
    """
    global _CACHED_REF_AUDIO
    ensure_index_tts_server()

    try:
        mode = load_key("index_tts.mode")
    except KeyError:
        mode = "preset"

    if mode == "preset":
        # 使用预设音色
        try:
            speaker = load_key("index_tts.speaker")
        except KeyError:
            speaker = "voice_01"
        index_tts(text=text, save_path=save_as, speaker=speaker)

    elif mode == "global":
        # 全局统一参考音频
        if _CACHED_REF_AUDIO is None:
            ref_audio = find_best_ref_audio(task_df)
            if ref_audio is None:
                raise Exception("Could not find suitable reference audio (3-10s)")
            _CACHED_REF_AUDIO = ref_audio
            rprint(f"[green]✅ Global reference audio cached for all segments[/green]")

        index_tts(text=text, save_path=save_as, ref_voice=_CACHED_REF_AUDIO)

    elif mode == "dynamic":
        # 每段独立参考音频
        ref_audio_path = f"{_AUDIO_REFERS_DIR}/{number}.wav"

        if not Path(ref_audio_path).exists():
            rprint(f"[yellow]⚠️ Reference audio not found: {ref_audio}[/yellow]")
            raise Exception(f"Reference audio not found: {ref_audio_path}")

        index_tts(text=text, save_path=save_as, ref_voice=ref_audio_path)

    else:
        raise ValueError(f"Invalid mode: {mode}. Please choose 'preset', 'global', or 'dynamic'")


if __name__ == "__main__":
    # 测试代码
    print("Testing IndexTTS...")

    # 测试 preset 模式
    test_text = "Hello, this is a test of IndexTTS."
    index_tts(test_text, "test_preset.wav", speaker="voice_01")

    # 测试 dynamic 模式 (如果有参考音频)
    # index_tts(test_text, "test_dynamic.wav", ref_voice="path/to/reference.wav")
