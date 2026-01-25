import os
import requests
import socket
import time
import subprocess
from pathlib import Path
from pydub import AudioSegment
from core.utils import *
from core.utils.models import *

# IndexTTS2 API configuration
try:
    INDEXTTS_HOST = load_key("index_tts.host")
except KeyError:
    INDEXTTS_HOST = "127.0.0.1"

try:
    INDEXTTS_PORT = load_key("index_tts.port")
except KeyError:
    INDEXTTS_PORT = 9880

INDEXTTS_API_URL = f"http://{INDEXTTS_HOST}:{INDEXTTS_PORT}"

# Global cache: best reference audio URL found
_CACHED_REF_AUDIO = None


def check_index_tts_server():
    """Check if IndexTTS server is running"""
    try:
        response = requests.get(f"{INDEXTTS_API_URL}/health", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def ensure_index_tts_server():
    """Ensure IndexTTS server is running"""
    if check_index_tts_server():
        rprint("[green]✅ IndexTTS server is running[/green]")
        return True

    rprint("[yellow]⚠️ IndexTTS server is not running[/yellow]")
    rprint("[yellow]Please start your IndexTTS API server first:[/yellow]")
    rprint(f"[cyan]→ API URL: {INDEXTTS_API_URL}[/cyan]")
    rprint("[yellow]Example command to start:[/yellow]")
    rprint("[cyan]python your_indextts_api.py[/cyan]")

    # Ask user if server has been manually started
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
    Call IndexTTS API to generate speech

    Args:
        text: Text to convert
        save_path: Save path
        speaker: Preset speaker name (e.g. "voice_01")
        ref_voice: Custom reference audio full path

    Returns:
        bool: True on success
    """
    params = {"text": text}

    if ref_voice:
        # Convert to absolute path
        ref_voice_abs = str(Path(ref_voice).resolve())
        params["ref_voice"] = ref_voice_abs
        rprint(f"[cyan]🎤 Using custom reference audio:[/cyan] {ref_voice_abs}")
    elif speaker:
        params["speaker"] = speaker
        rprint(f"[cyan]🎤 Using preset speaker:[/cyan] {speaker}")
    else:
        raise ValueError("Either 'speaker' or 'ref_voice' must be provided")

    # Call IndexTTS API
    response = requests.get(
        INDEXTTS_API_URL,
        params=params,
        timeout=60
    )

    if response.status_code == 200:
        # Ensure directory exists
        save_path_obj = Path(save_path)
        save_path_obj.parent.mkdir(parents=True, exist_ok=True)

        # Save audio file
        with open(save_path, 'wb') as f:
            f.write(response.content)

        rprint(f"[green]✅ Audio saved to:[/green] {save_path}")
        return True
    else:
        error_msg = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
        raise Exception(f"IndexTTS API error (HTTP {response.status_code}): {error_msg}")


def find_best_ref_audio(task_df, min_duration=3.0, max_duration=10.0):
    """
    Find best reference audio (3-10s)

    Args:
        task_df: Task dataframe
        min_duration: Minimum duration (seconds)
        max_duration: Maximum duration (seconds)

    Returns:
        str: Reference audio path, None if not found
    """
    rprint(f"[blue]🎯 Looking for best reference audio ({min_duration}s-{max_duration}s)...[/blue]")

    # Search by priority: first find single matching segments, then combined ones
    # 1. First look for single segments matching 3-10s
    for _, row in task_df.iterrows():
        duration = row['duration']
        if min_duration <= duration <= max_duration:
            ref_path = f"{_AUDIO_REFERS_DIR}/{row['number']}.wav"
            if Path(ref_path).exists():
                rprint(f"[green]✅ Found single segment: {row['number']}.wav ({duration:.2f}s)[/green]")
                return ref_path

    # 2. No single segment matches, combine multiple segments
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

    # Save combined reference audio
    combined_ref = f"{_AUDIO_REFERS_DIR}/index_tts_refer.wav"
    combined.export(combined_ref, format="wav")
    rprint(f"[green]✅ Created combined reference: {len(selected_files)} segments, {total_duration:.2f}s[/green]")

    return combined_ref


def index_tts_for_videolingo(text: str, save_as: str, number: int, task_df):
    """
    VideoLingo integrated IndexTTS entry function

    Args:
        text: Translated text
        save_as: Save path
        number: Current segment number
        task_df: Task dataframe
    """
    global _CACHED_REF_AUDIO
    ensure_index_tts_server()

    try:
        mode = load_key("index_tts.mode")
    except KeyError:
        mode = "preset"

    if mode == "preset":
        # Use preset speaker
        try:
            speaker = load_key("index_tts.speaker")
        except KeyError:
            speaker = "voice_01"
        index_tts(text=text, save_path=save_as, speaker=speaker)

    elif mode == "global":
        # Global unified reference audio
        if _CACHED_REF_AUDIO is None:
            ref_audio = find_best_ref_audio(task_df)
            if ref_audio is None:
                raise Exception("Could not find suitable reference audio (3-10s)")
            _CACHED_REF_AUDIO = ref_audio
            rprint(f"[green]✅ Global reference audio cached for all segments[/green]")

        index_tts(text=text, save_path=save_as, ref_voice=_CACHED_REF_AUDIO)

    elif mode == "dynamic":
        # Independent reference audio for each segment
        ref_audio_path = f"{_AUDIO_REFERS_DIR}/{number}.wav"

        if not Path(ref_audio_path).exists():
            rprint(f"[yellow]⚠️ Reference audio not found: {ref_audio}[/yellow]")
            raise Exception(f"Reference audio not found: {ref_audio_path}")

        index_tts(text=text, save_path=save_as, ref_voice=ref_audio_path)

    else:
        raise ValueError(f"Invalid mode: {mode}. Please choose 'preset', 'global', or 'dynamic'")


if __name__ == "__main__":
    # Test code
    print("Testing IndexTTS...")

    # Test preset mode
    test_text = "Hello, this is a test of IndexTTS."
    index_tts(test_text, "test_preset.wav", speaker="voice_01")

    # Test dynamic mode (if reference audio is available)
    # index_tts(test_text, "test_dynamic.wav", ref_voice="path/to/reference.wav")
