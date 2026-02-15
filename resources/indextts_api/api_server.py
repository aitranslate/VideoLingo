from flask import Flask, request, send_file, jsonify
from indextts.infer_v2 import IndexTTS2
import torch
import os
import tempfile
import threading
import io  # Import io module
from datetime import datetime
import time

app = Flask(__name__)

# Initialize TTS model
# Note: Ensure 'checkpoints' directory and 'checkpoints/config.yaml' file exist
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

# Use IndexTTS2 model with more parameters
tts = IndexTTS2(cfg_path="checkpoints/config.yaml", model_dir="checkpoints", use_fp16=True, use_cuda_kernel=True, use_deepspeed=False)

# Add thread lock (kept to ensure CUDA inference processes serially in order)
tts_lock = threading.Lock()

# Removed cleanup_file and cleanup_temp_files functions and related global variables

@app.route('/', methods=['GET', 'POST'])
def tts_endpoint():
    """
    TTS API endpoint for IndexTTS2
    Parameters:
    - text: The text to convert to speech
    - speaker: Reference audio file name in voices directory (optional, used if ref_voice not provided)
    - ref_voice: Full path to reference audio file (optional, takes priority over speaker)
    - output_format: Output format (optional, defaults to wav)
    - emo_audio_prompt: Emotion reference audio file (optional)
    - emo_alpha: Emotion strength (0.0-1.0, optional, defaults to 1.0)
    - emo_vector: Emotion vector as comma-separated values (optional)
    - use_emo_text: Enable emotion text guidance (0/1 or true/false, optional)
    - emo_text: Emotion text description (optional)
    - use_random: Enable random sampling (0/1 or true/false, optional, defaults to false)
    - interval_silence: Silence interval between segments in milliseconds (optional)
    """
    # Support GET request parameter retrieval (URL query parameters)
    text = request.args.get('text', '')
    speaker = request.args.get('speaker', 'voice_01.wav')
    ref_voice = request.args.get('ref_voice', '')
    output_format = request.args.get('output_format', 'wav')

    # IndexTTS2 specific parameters
    emo_audio_prompt = request.args.get('emo_audio_prompt', '')
    emo_alpha = request.args.get('emo_alpha', '1.0')
    emo_vector = request.args.get('emo_vector', '')
    use_emo_text = request.args.get('use_emo_text', 'false')
    emo_text = request.args.get('emo_text', '')
    use_random = request.args.get('use_random', 'false')
    interval_silence = request.args.get('interval_silence', '200')

    # Support POST request parameter retrieval (form or JSON data)
    if request.method == 'POST':
        if not text:  # If GET parameters are empty, try to get from POST data
            if request.is_json:
                json_data = request.get_json()
                text = json_data.get('text', '') if json_data else ''
                speaker = json_data.get('speaker', 'voice_01.wav') if json_data else 'voice_01.wav'
                ref_voice = json_data.get('ref_voice', '') if json_data else ''
                output_format = json_data.get('output_format', 'wav') if json_data else 'wav'

                # IndexTTS2 specific parameters
                emo_audio_prompt = json_data.get('emo_audio_prompt', '') if json_data else ''
                emo_alpha = json_data.get('emo_alpha', '1.0') if json_data else '1.0'
                emo_vector = json_data.get('emo_vector', '') if json_data else ''
                use_emo_text = json_data.get('use_emo_text', 'false') if json_data else 'false'
                emo_text = json_data.get('emo_text', '') if json_data else ''
                use_random = json_data.get('use_random', 'false') if json_data else 'false'
                interval_silence = json_data.get('interval_silence', '200') if json_data else '200'
            else:
                text = request.form.get('text', '')
                speaker = request.form.get('speaker', 'voice_01.wav')
                ref_voice = request.form.get('ref_voice', '')
                output_format = request.form.get('output_format', 'wav')

                # IndexTTS2 specific parameters
                emo_audio_prompt = request.form.get('emo_audio_prompt', '')
                emo_alpha = request.form.get('emo_alpha', '1.0')
                emo_vector = request.form.get('emo_vector', '')
                use_emo_text = request.form.get('use_emo_text', 'false')
                emo_text = request.form.get('emo_text', '')
                use_random = request.form.get('use_random', 'false')
                interval_silence = request.form.get('interval_silence', '200')

    if not text:
        return jsonify({"error": "Text parameter is required"}), 400

    # Record start time
    start_time = time.time()

    # Build voice file path: ref_voice takes priority, otherwise use speaker
    if ref_voice:
        voice_path = ref_voice
    else:
        voice_path = f"./voices/{speaker}"
        if not voice_path.endswith('.wav'):
            voice_path += ".wav"

    # Check if voice file exists
    if not os.path.exists(voice_path):
        return jsonify({"error": f"Speaker file does not exist: {voice_path}"}), 400

    # Handle emotion audio path
    emo_audio_path = None
    if emo_audio_prompt:
        emo_audio_path = f"./voices/{emo_audio_prompt}"
        if not emo_audio_path.endswith('.wav'):
            emo_audio_path += ".wav"
        if not os.path.exists(emo_audio_path):
            return jsonify({"error": f"Emotion audio file does not exist: {emo_audio_path}"}), 400

    # Handle emotion vector
    emo_vector_list = None
    if emo_vector:
        try:
            emo_vector_list = [float(x.strip()) for x in emo_vector.split(',')]
            if len(emo_vector_list) != 8:
                return jsonify({"error": "Emotion vector must contain exactly 8 values"}), 400
        except ValueError:
            return jsonify({"error": "Emotion vector must contain valid float numbers separated by commas"}), 400

    # Handle boolean parameters
    try:
        use_emo_text_bool = use_emo_text.lower() in ['true', '1', 'yes', 'on']
        use_random_bool = use_random.lower() in ['true', '1', 'yes', 'on']
        emo_alpha_float = float(emo_alpha)
    except ValueError:
        return jsonify({"error": "Invalid value for emo_alpha, use_emo_text, or use_random"}), 400

    # Handle interval_silence parameter
    try:
        interval_silence_int = int(interval_silence)
    except ValueError:
        return jsonify({"error": "Invalid value for interval_silence, must be an integer"}), 400

    output_path = None

    # Acquire lock to ensure only one TTS request is processed at a time
    with tts_lock:
        try:
            # 1. Create temporary file and get path
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                output_path = tmp_file.name

            # 2. Execute TTS inference
            tts.infer(
                spk_audio_prompt=voice_path,
                text=text,
                output_path=output_path,
                emo_audio_prompt=emo_audio_path,
                emo_alpha=emo_alpha_float,
                emo_vector=emo_vector_list,
                use_emo_text=use_emo_text_bool,
                emo_text=emo_text if use_emo_text_bool else None,
                use_random=use_random_bool,
                interval_silence=interval_silence_int
            )

            # 3. Read file content into memory
            with open(output_path, 'rb') as f:
                # Use BytesIO to store audio data
                audio_data = io.BytesIO(f.read())

            # 4. File content is in memory, safely delete disk file immediately
            os.remove(output_path)
            # Clear output_path to prevent finally block from trying to delete already deleted file
            output_path = None

            # 5. Send response from memory data stream
            # mimetype set to audio/wav
            response = send_file(
                audio_data,
                mimetype=f'audio/{output_format}',
                as_attachment=True,
                download_name=f"output.{output_format}"
            )

            # Calculate total time
            total_time = time.time() - start_time
            ref_info = ref_voice if ref_voice else speaker
            print(f"TTS2 request completed - Reference audio: {ref_info}, Total time: {total_time:.2f}s")

            return response

        except Exception as e:
            # Return 500 on error
            total_time = time.time() - start_time
            print(f"TTS2 generation failed - Error: {str(e)}, Total time: {total_time:.2f}s")
            return jsonify({"error": f"TTS2 generation failed: {str(e)}"}), 500

        finally:
            # 6. Ensure temp file is cleaned up even if read/delete fails
            if output_path and os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except Exception as e:
                    # Print error, usually occurs when inference fails or permission issues
                    print(f"Failed to cleanup failed temp file {output_path}: {e}")


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "device": device,
        "model": "IndexTTS2"
    }), 200


if __name__ == '__main__':
    print("Starting IndexTTS2 API server...")
    print(f"Model loaded on device: {device}")
    # Keep debug=False, threaded=True, but note that threaded=True with tts_lock
    # means Flask can receive requests in parallel, but the inference core is serial.
    app.run(host='0.0.0.0', port=9880, debug=False, threaded=True)