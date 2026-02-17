import os
import platform
import subprocess

import cv2
import numpy as np
import pysubs2
from rich.console import Console

from core._1_ytdlp import find_video_files
from core.utils import *
from core.utils.models import *

console = Console()

DUB_VIDEO = "output/output_dub.mp4"
DUB_SUB_FILE = 'output/dub.srt'
DUB_AUDIO = 'output/dub.mp3'

# ================= 字幕样式设置 =================
TRANS_FONT_SIZE = 70
TRANS_FONT_NAME = 'Microsoft YaHei'
if platform.system() == 'Linux':
    TRANS_FONT_NAME = 'WenQuanYi Micro Hei'
if platform.system() == 'Darwin':
    TRANS_FONT_NAME = 'PingFang SC'

TRANS_FONT_COLOR_RGB = (255, 186, 0)  # 金黄色
TRANS_OUTLINE_COLOR_RGB = (0, 0, 0)
TRANS_OUTLINE_WIDTH = 1.5
MARGIN_V = 50
BOLD = True
# ===============================================


def srt_to_ass_simple(srt_path, ass_path):
    """
    Convert SRT to ASS subtitle format for dubbing

    Args:
        srt_path: Path to SRT
        ass_path: Output ASS path
    """
    subs = pysubs2.load(srt_path, encoding="utf-8")

    # Lock to 1080p baseline
    subs.info["PlayResX"] = 1920
    subs.info["PlayResY"] = 1080

    # Define default style
    style = pysubs2.SSAStyle()
    style.fontname = TRANS_FONT_NAME
    style.fontsize = TRANS_FONT_SIZE
    style.bold = BOLD

    # Colors (RGB -> ASS Color)
    style.primarycolour = pysubs2.Color(*TRANS_FONT_COLOR_RGB)
    style.backcolour = pysubs2.Color(0, 0, 0, 0)
    style.outlinecolour = pysubs2.Color(*TRANS_OUTLINE_COLOR_RGB)

    style.outline = TRANS_OUTLINE_WIDTH
    style.shadow = 0
    style.alignment = 2  # Bottom center
    style.marginv = MARGIN_V

    subs.styles["Default"] = style

    # Create ASS color tag (BGR format for ASS)
    r, g, b = TRANS_FONT_COLOR_RGB
    color_tag = f"{{\\1c&H{b:02X}{g:02X}{r:02X}&}}"

    for line in subs:
        line.style = "Default"
        text = line.text.strip()
        line.text = f"{color_tag}{text}"

    subs.save(ass_path)


def merge_video_audio():
    """Merge video and audio, and reduce video volume"""
    VIDEO_FILE = find_video_files()
    background_file = _BACKGROUND_AUDIO_FILE

    if not load_key("burn_subtitles"):
        rprint("[bold yellow]Warning: A 0-second black video will be generated as a placeholder as subtitles are not burned in.[/bold yellow]")

        # Create a black frame
        frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(DUB_VIDEO, fourcc, 1, (1920, 1080))
        out.write(frame)
        out.release()

        rprint("[bold green]Placeholder video has been generated.[/bold green]")
        return

    # Merge video and audio with translated subtitles
    video = cv2.VideoCapture(VIDEO_FILE)
    TARGET_WIDTH = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    TARGET_HEIGHT = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    video.release()
    rprint(f"[bold green]Video resolution: {TARGET_WIDTH}x{TARGET_HEIGHT}[/bold green]")

    # Generate ASS subtitle
    temp_ass = os.path.join("output", "temp_dub_subtitle.ass")
    srt_to_ass_simple(DUB_SUB_FILE, temp_ass)

    def escape_path(path):
        return path.replace(':', '\\:').replace('\\', '/')

    safe_ass = escape_path(temp_ass)

    # Video scale/pad + ASS subtitle filter
    video_filter = (
        f'[0:v]scale={TARGET_WIDTH}:{TARGET_HEIGHT}:force_original_aspect_ratio=decrease,'
        f'pad={TARGET_WIDTH}:{TARGET_HEIGHT}:(ow-iw)/2:(oh-ih)/2,'
        f'ass=\'{safe_ass}\'[v]'
    )

    cmd = [
        'ffmpeg', '-y', '-i', VIDEO_FILE, '-i', background_file, '-i', DUB_AUDIO,
        '-filter_complex',
        f'{video_filter};[1:a][2:a]amix=inputs=2:duration=first:dropout_transition=3[a]'
    ]

    if load_key("ffmpeg_gpu"):
        rprint("[bold green]Using GPU acceleration...[/bold green]")
        cmd.extend(['-map', '[v]', '-map', '[a]', '-c:v', 'h264_nvenc'])
    else:
        cmd.extend(['-map', '[v]', '-map', '[a]'])

    cmd.extend(['-c:a', 'aac', '-b:a', '96k', DUB_VIDEO])

    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Clean up temp ASS file
    if os.path.exists(temp_ass):
        try: os.remove(temp_ass)
        except: pass

    rprint(f"[bold green]Video and audio successfully merged into {DUB_VIDEO}[/bold green]")


if __name__ == '__main__':
    merge_video_audio()
