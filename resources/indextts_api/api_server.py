from flask import Flask, request, send_file, jsonify
from indextts.infer_v2 import IndexTTS2
import torch
import os
import tempfile
import threading
import io # 导入 io 模块
from datetime import datetime
import time

app = Flask(__name__)

# 初始化TTS模型
# 注意：确保 'checkpoints' 目录和 'checkpoints/2.0/config.yaml' 文件存在
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

# 使用IndexTTS2模型，支持更多参数
tts = IndexTTS2(cfg_path="checkpoints/2.0/config.yaml", model_dir="checkpoints/2.0", use_fp16=True, use_cuda_kernel=True, use_deepspeed=False)

# 添加线程锁（保留，确保 CUDA 推理按顺序串行处理）
tts_lock = threading.Lock()

# 移除 cleanup_file 和 cleanup_temp_files 函数及相关全局变量

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
    # 支持GET请求参数获取 (URL查询参数)
    text = request.args.get('text', '')
    speaker = request.args.get('speaker', 'voice_01.wav')
    ref_voice = request.args.get('ref_voice', '')
    output_format = request.args.get('output_format', 'wav')

    # IndexTTS2特有参数
    emo_audio_prompt = request.args.get('emo_audio_prompt', '')
    emo_alpha = request.args.get('emo_alpha', '1.0')
    emo_vector = request.args.get('emo_vector', '')
    use_emo_text = request.args.get('use_emo_text', 'false')
    emo_text = request.args.get('emo_text', '')
    use_random = request.args.get('use_random', 'false')
    interval_silence = request.args.get('interval_silence', '200')

    # 支持POST请求参数获取 (form或JSON数据)
    if request.method == 'POST':
        if not text:  # 如果GET参数为空，尝试从POST数据获取
            if request.is_json:
                json_data = request.get_json()
                text = json_data.get('text', '') if json_data else ''
                speaker = json_data.get('speaker', 'voice_01.wav') if json_data else 'voice_01.wav'
                ref_voice = json_data.get('ref_voice', '') if json_data else ''
                output_format = json_data.get('output_format', 'wav') if json_data else 'wav'
                
                # IndexTTS2特有参数
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
                
                # IndexTTS2特有参数
                emo_audio_prompt = request.form.get('emo_audio_prompt', '')
                emo_alpha = request.form.get('emo_alpha', '1.0')
                emo_vector = request.form.get('emo_vector', '')
                use_emo_text = request.form.get('use_emo_text', 'false')
                emo_text = request.form.get('emo_text', '')
                use_random = request.form.get('use_random', 'false')
                interval_silence = request.form.get('interval_silence', '200')

    if not text:
        return jsonify({"error": "Text parameter is required"}), 400

    # 记录开始时间
    start_time = time.time()

    # 构建声音文件路径：ref_voice 优先，否则用 speaker
    if ref_voice:
        voice_path = ref_voice
    else:
        voice_path = f"./voices/{speaker}"
        if not voice_path.endswith('.wav'):
            voice_path += ".wav"

    # 检查声音文件是否存在
    if not os.path.exists(voice_path):
        return jsonify({"error": f"Speaker file does not exist: {voice_path}"}), 400

    # 处理情绪音频路径
    emo_audio_path = None
    if emo_audio_prompt:
        emo_audio_path = f"./voices/{emo_audio_prompt}"
        if not emo_audio_path.endswith('.wav'):
            emo_audio_path += ".wav"
        if not os.path.exists(emo_audio_path):
            return jsonify({"error": f"Emotion audio file does not exist: {emo_audio_path}"}), 400

    # 处理情绪向量
    emo_vector_list = None
    if emo_vector:
        try:
            emo_vector_list = [float(x.strip()) for x in emo_vector.split(',')]
            if len(emo_vector_list) != 8:
                return jsonify({"error": "Emotion vector must contain exactly 8 values"}), 400
        except ValueError:
            return jsonify({"error": "Emotion vector must contain valid float numbers separated by commas"}), 400

    # 处理布尔参数
    try:
        use_emo_text_bool = use_emo_text.lower() in ['true', '1', 'yes', 'on']
        use_random_bool = use_random.lower() in ['true', '1', 'yes', 'on']
        emo_alpha_float = float(emo_alpha)
    except ValueError:
        return jsonify({"error": "Invalid value for emo_alpha, use_emo_text, or use_random"}), 400

    # 处理interval_silence参数
    try:
        interval_silence_int = int(interval_silence)
    except ValueError:
        return jsonify({"error": "Invalid value for interval_silence, must be an integer"}), 400

    output_path = None

    # 加锁确保同一时间只有一个TTS请求在处理
    with tts_lock:
        try:
            # 1. 创建临时文件并获取路径
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                output_path = tmp_file.name

            # 2. 执行 TTS 推理
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

            # 3. 读取文件内容到内存
            with open(output_path, 'rb') as f:
                # 使用 BytesIO 存储音频数据
                audio_data = io.BytesIO(f.read())

            # 4. 文件内容已在内存，立即安全删除磁盘文件
            os.remove(output_path)
            # 清空 output_path，防止 finally 块尝试删除已删除的文件
            output_path = None

            # 5. 从内存数据流发送响应
            # mimetype 设置为 audio/wav
            response = send_file(
                audio_data,
                mimetype=f'audio/{output_format}',
                as_attachment=True,
                download_name=f"output.{output_format}"
            )

            # 计算总耗时
            total_time = time.time() - start_time
            ref_info = ref_voice if ref_voice else speaker
            print(f"TTS2请求处理完成 - 参考音频: {ref_info}, 总耗时: {total_time:.2f}秒")

            return response

        except Exception as e:
            # 发生错误时返回 500
            total_time = time.time() - start_time
            print(f"TTS2生成失败 - 错误: {str(e)}, 总耗时: {total_time:.2f}秒")
            return jsonify({"error": f"TTS2 generation failed: {str(e)}"}), 500

        finally:
            # 6. 确保即使在读取/删除前失败，临时文件也被清理
            if output_path and os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except Exception as e:
                    # 打印错误，通常发生在推理失败或权限问题时
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
    # 保持 debug=False, threaded=True，但请注意，threaded=True 配合 tts_lock
    # 意味着 Flask 可以并行接收请求，但推理核心是串行的。
    app.run(host='0.0.0.0', port=9880, debug=False, threaded=True)