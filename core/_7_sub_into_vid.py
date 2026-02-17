import os, subprocess, time
import cv2
import numpy as np
import platform
import pysubs2
from core._1_ytdlp import find_video_files
from core.utils import *

# ==================== 核心开关 ====================
# Read from config: subtitle.dual_subtitle
try:
    IS_DUAL_SUB = load_key("subtitle.dual_subtitle")
except KeyError:
    IS_DUAL_SUB = False
# ==================================================

# ================= 剪映风格样式设置 =================
# 1. 英文样式 (仅在双语模式下生效)
SRC_FONT_SIZE = 60
FONT_NAME = 'Microsoft YaHei'
SRC_FONT_COLOR_RGB = (255, 186, 0)  # 金黄色
SRC_OUTLINE_COLOR_RGB = (0, 0, 0)
SRC_OUTLINE_WIDTH = 1.5

# 2. 中文样式 (使用系统自带字体)
TRANS_FONT_SIZE = 70
TRANS_FONT_NAME = 'Microsoft YaHei'

if platform.system() == 'Linux':
    TRANS_FONT_NAME = 'WenQuanYi Micro Hei'
    FONT_NAME = 'DejaVu Sans'
elif platform.system() == 'Darwin':
    TRANS_FONT_NAME = 'PingFang SC'
    FONT_NAME = 'Helvetica'

TRANS_FONT_COLOR_RGB = (255, 186, 0)  # 金黄色
TRANS_OUTLINE_COLOR_RGB = (0, 0, 0)
TRANS_OUTLINE_WIDTH = 1.5
TRANS_BACK_COLOR_RGB = (0, 0, 0)
MARGIN_V = 50
BOLD = True
# ======================================================

OUTPUT_DIR = "output"
OUTPUT_VIDEO = f"{OUTPUT_DIR}/output_sub.mp4"
SRC_SRT = f"{OUTPUT_DIR}/src.srt"
TRANS_SRT = f"{OUTPUT_DIR}/trans.srt"


def srt_to_ass(srt_path, ass_path, is_dual=False, src_srt_path=None):
    """
    Convert SRT to ASS subtitle format with proper styling

    Args:
        srt_path: Path to translated SRT
        ass_path: Output ASS path
        is_dual: Whether to show dual subtitles
        src_srt_path: Path to source SRT (for dual mode)
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

    if is_dual and src_srt_path and os.path.exists(src_srt_path):
        # Dual subtitle mode: load both SRTs
        src_subs = pysubs2.load(src_srt_path, encoding="utf-8")

        # Create ASS color tag (BGR format for ASS)
        r, g, b = TRANS_FONT_COLOR_RGB
        color_tag = f"{{\\1c&H{b:02X}{g:02X}{r:02X}&}}"

        # Process each line - match by index (1:1 correspondence)
        for i, line in enumerate(subs):
            line.style = "Default"
            zh_text = line.text.strip()

            # Match by index directly
            en_text = ""
            if i < len(src_subs):
                en_text = src_subs[i].text.strip()

            if en_text:
                line.text = f"{color_tag}{zh_text}\\N{{\\fs{SRC_FONT_SIZE}}}{en_text}"
            else:
                line.text = f"{color_tag}{zh_text}"
    else:
        # Single subtitle mode
        # Create ASS color tag (BGR format for ASS)
        r, g, b = TRANS_FONT_COLOR_RGB
        color_tag = f"{{\\1c&H{b:02X}{g:02X}{r:02X}&}}"

        for line in subs:
            line.style = "Default"
            text = line.text.strip()
            line.text = f"{color_tag}{text}"

    subs.save(ass_path)
    rprint(f"[green]✅ ASS subtitle generated:[/green] {ass_path}")


def merge_subtitles_to_video():
    video_file = find_video_files()
    os.makedirs(os.path.dirname(OUTPUT_VIDEO), exist_ok=True)

    if os.path.exists(OUTPUT_VIDEO):
        try: os.remove(OUTPUT_VIDEO)
        except: pass

    if not load_key("burn_subtitles"):
        frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(OUTPUT_VIDEO, fourcc, 1, (1920, 1080))
        out.write(frame)
        out.release()
        return

    if not os.path.exists(TRANS_SRT):
        rprint("[bold red]错误: 找不到中文字幕文件。[/bold red]")
        return

    video = cv2.VideoCapture(video_file)
    TARGET_WIDTH = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    TARGET_HEIGHT = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    video.release()

    # Generate ASS subtitle
    temp_ass = os.path.join(OUTPUT_DIR, "temp_subtitle.ass")
    srt_to_ass(TRANS_SRT, temp_ass, is_dual=IS_DUAL_SUB, src_srt_path=SRC_SRT)

    def escape_path(path):
        return path.replace(':', '\\:').replace('\\', '/')

    safe_ass = escape_path(temp_ass)

    # Video scale and pad filter
    scale_pad = f"scale={TARGET_WIDTH}:{TARGET_HEIGHT}:force_original_aspect_ratio=decrease,pad={TARGET_WIDTH}:{TARGET_HEIGHT}:(ow-iw)/2:(oh-ih)/2"

    if IS_DUAL_SUB:
        rprint("[bold cyan]当前渲染模式：双语 (中+英)[/bold cyan]")
    else:
        rprint("[bold cyan]当前渲染模式：单语 (仅中文)[/bold cyan]")

    sub_filter = f"{scale_pad},ass='{safe_ass}'"

    ffmpeg_cmd = ['ffmpeg', '-y', '-i', video_file, '-vf', sub_filter]

    ffmpeg_gpu = load_key("ffmpeg_gpu")
    if ffmpeg_gpu:
        ffmpeg_cmd.extend(['-c:v', 'h264_nvenc'])
    else:
        ffmpeg_cmd.extend(['-c:v', 'libx264', '-preset', 'fast'])

    ffmpeg_cmd.append(OUTPUT_VIDEO)

    rprint("🎬 开始烧录字幕...")
    start_time = time.time()

    process = subprocess.run(
        ffmpeg_cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        encoding='utf-8',
        errors='ignore'
    )

    # Clean up temp ASS file
    if os.path.exists(temp_ass):
        try: os.remove(temp_ass)
        except: pass

    if process.returncode == 0:
        rprint(f"\n✅ 烧录完成! 耗时: {time.time() - start_time:.2f} 秒")
    else:
        rprint(f"\n❌ FFmpeg 报错: {process.stderr}")


if __name__ == "__main__":
    merge_subtitles_to_video()
