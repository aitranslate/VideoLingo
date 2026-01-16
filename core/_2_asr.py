from core.utils import *
from core.utils.vocal_separator import separate_vocals_and_background
from core.asr_backend.audio_preprocess import process_transcription, convert_video_to_audio, split_audio, save_results, normalize_audio_volume
from core._1_ytdlp import find_video_files
from core.utils.models import *

@check_file_exists(_2_CLEANED_CHUNKS)
def transcribe():
    video_file = find_video_files()
    convert_video_to_audio(video_file)

    if load_key("audio_separator"):
        separate_vocals_and_background()
        vocal_audio = normalize_audio_volume(_VOCAL_AUDIO_FILE, _VOCAL_AUDIO_FILE)
    else:
        vocal_audio = _RAW_AUDIO_FILE

    segments = split_audio(_RAW_AUDIO_FILE)

    all_results = []
    from core.asr_backend.whisperX_local import transcribe_audio as ts
    rprint("[cyan]🎤 Transcribing audio with local model...[/cyan]")

    for start, end in segments:
        result = ts(_RAW_AUDIO_FILE, vocal_audio, start, end)
        all_results.append(result)

    combined_result = {'segments': []}
    for result in all_results:
        combined_result['segments'].extend(result['segments'])

    df = process_transcription(combined_result)
    save_results(df)
        
if __name__ == "__main__":
    transcribe()