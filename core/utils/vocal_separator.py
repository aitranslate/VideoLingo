"""
Audio vocal separation module using audio-separator library
Enhances ASR transcription accuracy in noisy environments
"""
import os
from audio_separator.separator import Separator
from core.utils.models import _RAW_AUDIO_FILE, _VOCAL_AUDIO_FILE, _BACKGROUND_AUDIO_FILE
from core.utils.config_utils import load_key
from rich.console import Console

console = Console()

VOCAL_MODEL = "UVR-MDX-NET-Inst_HQ_3.onnx"
MODEL_DIR = load_key("model_dir")


def separate_vocals_and_background(input_file=None, vocal_output=None, background_output=None, model_name=None):
    """
    Separate vocals and background from audio

    Args:
        input_file: Input audio file path (default: RAW_AUDIO_FILE from config)
        vocal_output: Vocal output file path (default: output/audio/vocal.wav)
        background_output: Background output file path (default: output/audio/background.wav)
        model_name: Separation model name (default: UVR-MDX-NET-Inst_HQ_3.onnx)

    Returns:
        bool: True if successful, False otherwise
    """
    if input_file is None:
        input_file = _RAW_AUDIO_FILE
    if vocal_output is None:
        vocal_output = _VOCAL_AUDIO_FILE
    if background_output is None:
        background_output = _BACKGROUND_AUDIO_FILE
    if model_name is None:
        model_name = VOCAL_MODEL

    if not os.path.exists(input_file):
        console.print(f"[red]Input file not found: {input_file}[/red]")
        return False

    if os.path.exists(vocal_output) and os.path.exists(background_output):
        console.print(f"[yellow]Skip separation, files already exist[/yellow]")
        return True

    output_dir = os.path.dirname(vocal_output)
    os.makedirs(output_dir, exist_ok=True)

    console.print(f"[cyan]Separating vocals and background (model: {model_name})...[/cyan]")

    try:
        separator = Separator(
            model_file_dir=MODEL_DIR,
            output_dir=output_dir,
            output_format="wav",
            log_level=40
        )

        separator.load_model(model_filename=model_name)

        output_names = {
            "Vocals": os.path.splitext(os.path.basename(vocal_output))[0],
            "Instrumental": os.path.splitext(os.path.basename(background_output))[0],
        }

        output_files = separator.separate(input_file, output_names)

        console.print(f"[dim]Output files: {output_files}[/dim]")
        console.print(f"[green]Audio separation completed![/green]")

        return True

    except Exception as e:
        console.print(f"[red]Audio separation failed: {e}[/red]")
        return False


if __name__ == "__main__":
    separate_vocals_and_background()
