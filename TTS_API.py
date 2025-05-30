# API.py
from flask import Flask, request, Response, stream_with_context
import os
import tempfile
import logging
from indextts.infer import IndexTTS

# --- 配置项 (用户需要根据实际情况修改) ---
# IndexTTS 模型路径配置
MODEL_DIR = "checkpoints/indextts-1.5"  # <--- 修改这里为你实际的模型文件夹名 (例如 "checkpoints")
CONFIG_PATH = os.path.join(MODEL_DIR, "config.yaml")

# 参考语音文件存放的子目录名 (相对于此 API.py 文件的位置)
VOICES_SUBDIR = "voices"
# 固定的参考音频文件名
REFERENCE_AUDIO_FILENAME = "audio.wav" # <--- 所有语音都将使用此文件

# API 密钥 (用于演示，生产环境应使用更安全的管理方式)
API_KEY = "sk-test-api-key-1234567890" # <--- 你可以修改为自己的API Key

app = Flask(__name__)

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 初始化 IndexTTS
tts_instance = None
try:
    if not os.path.isdir(MODEL_DIR):
        logger.error(f"错误：模型目录 '{MODEL_DIR}' 不存在。请检查 MODEL_DIR 配置。")
    elif not os.path.exists(CONFIG_PATH):
        logger.error(f"错误：配置文件 '{CONFIG_PATH}' 不存在。请检查 MODEL_DIR 或 CONFIG_PATH。")
    else:
        logger.info(f"正在从目录 '{MODEL_DIR}' 初始化 IndexTTS...")
        # 根据 webui.py 的主 tts 初始化，它没有显式传递 is_fp16 或 use_cuda_kernel
        # 如果你需要这些参数以获得特定行为/性能，可以添加它们：
        # is_fp16=True, use_cuda_kernel=False (参考 regression_test.py)
        tts_instance = IndexTTS(model_dir=MODEL_DIR, cfg_path=CONFIG_PATH)
        logger.info(f"IndexTTS 初始化成功。模型版本: {getattr(tts_instance, 'model_version', 'N/A')}")
except Exception as e:
    logger.error(f"IndexTTS 初始化失败: {e}", exc_info=True)
    tts_instance = None

# 支持的模型和语音 (OpenAI API 标准)
SUPPORTED_MODELS = ["tts-1", "tts-1-hd"]
SUPPORTED_VOICES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
SUPPORTED_FORMATS = ["mp3", "opus", "aac", "flac", "wav"] 

# 获取此脚本所在的目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VOICES_DIR_PATH = os.path.join(BASE_DIR, VOICES_SUBDIR)
D_WAV_PATH = os.path.join(VOICES_DIR_PATH, REFERENCE_AUDIO_FILENAME)

# 所有OpenAI语音统一映射到参考音频文件
VOICE_TO_REFERENCE = {voice: D_WAV_PATH for voice in SUPPORTED_VOICES}

def check_dependencies():
    """检查必要的依赖文件和服务状态"""
    global tts_instance
    dependencies_ok = True
    if tts_instance is None:
        logger.error("TTS 服务未能初始化。API无法工作。")
        dependencies_ok = False

    if not os.path.exists(D_WAV_PATH):
        logger.error(f"错误：核心参考音频 '{D_WAV_PATH}' 未找到。请将其放置在 '{VOICES_DIR_PATH}' 目录下。")
        if not os.path.isdir(VOICES_DIR_PATH):
             logger.info(f"提示：参考语音目录 '{VOICES_DIR_PATH}' 将在服务首次请求时尝试创建（如果不存在）。")
        dependencies_ok = False
    else:
        logger.info(f"核心参考音频 '{D_WAV_PATH}' 已找到。")
    return dependencies_ok

def _generate_audio_fast(
    text_input: str,
    reference_voice_path: str,
    max_text_tokens_per_sentence: int = 120,
    sentences_bucket_max_size: int = 4,
    do_sample: bool = True,
    temperature: float = 1.0,
    top_p: float = 0.8,
    top_k: int = 30, 
    num_beams: int = 3, 
    repetition_penalty: float = 10.0,
    length_penalty: float = 0.0,
    max_mel_tokens: int = 600,
    verbose_tts: bool = True 
):
    """
    使用 index-tts 的 infer_fast 生成完整的音频文件。
    """
    global tts_instance
    if tts_instance is None:
        raise RuntimeError("TTS service is not available due to initialization failure.")
    if not os.path.exists(reference_voice_path):
        raise FileNotFoundError(f"Reference audio file '{reference_voice_path}' not found for TTS.")

    # index-tts 输出文件格式
    temp_suffix = ".wav"
    actual_mimetype = "audio/wav"

    temp_file_obj = tempfile.NamedTemporaryFile(delete=False, suffix=temp_suffix)
    output_path = temp_file_obj.name
    temp_file_obj.close()

    generation_kwargs = {
        "do_sample": do_sample,
        "top_p": top_p,
        "top_k": int(top_k) if int(top_k) > 0 else None,
        "temperature": temperature,
        "length_penalty": length_penalty,
        "num_beams": int(num_beams),
        "repetition_penalty": repetition_penalty,
        "max_mel_tokens": int(max_mel_tokens),
    }
    if int(num_beams) > 1 and do_sample:
        logger.debug("Adjusting do_sample to False due to num_beams > 1 for infer_fast.")
        generation_kwargs["do_sample"] = False
    
    logger.info(f"Using infer_fast: audio_prompt='{reference_voice_path}', text='{text_input[:30]}...', output='{output_path}'")
    logger.debug(f"infer_fast params: max_text_tokens_per_sentence={max_text_tokens_per_sentence}, "
                 f"sentences_bucket_max_size={sentences_bucket_max_size}, generation_kwargs={generation_kwargs}")
    try:
        tts_instance.infer_fast(
            audio_prompt=reference_voice_path,
            text=text_input,
            output_path=output_path,
            verbose=verbose_tts,
            max_text_tokens_per_sentence=int(max_text_tokens_per_sentence),
            sentences_bucket_max_size=int(sentences_bucket_max_size),
            **generation_kwargs
        )
        logger.info(f"Audio file generated successfully by infer_fast: {output_path}")
    except Exception as e:
        if os.path.exists(output_path):
            try: os.unlink(output_path)
            except Exception as e_unlink: logger.error(f"Error unlinking failed temp file '{output_path}': {e_unlink}")
        logger.error(f"Error during infer_fast: {e}", exc_info=True)
        raise RuntimeError(f"Audio generation with infer_fast failed: {e}")

    return output_path, actual_mimetype


@app.route("/v1/audio/speech", methods=["POST"])
def text_to_speech_api_route():
    global tts_instance
    if tts_instance is None:
        return Response('{"error": {"message": "TTS service is currently unavailable. Please check server logs.", "type": "server_error"}}', status=503, mimetype="application/json")

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return Response('{"error": {"message": "Missing or invalid Authorization header.", "type": "authentication_error"}}', status=401, mimetype="application/json")
    
    provided_key = auth_header.split("Bearer ")[1]
    if provided_key != API_KEY:
        return Response('{"error": {"message": "Invalid API key.", "type": "authentication_error"}}', status=401, mimetype="application/json")

    try:
        data = request.get_json()
    except Exception as e:
        return Response(f'{{"error": {{"message": "Invalid JSON body: {str(e)}", "type": "invalid_request_error"}}}}', status=400, mimetype="application/json")

    if not data:
        return Response('{"error": {"message": "Missing JSON body.", "type": "invalid_request_error"}}', status=400, mimetype="application/json")

    model_id = data.get("model")
    input_text = data.get("input")
    voice_key = data.get("voice")

    # 客户端请求的 response_format 主要用于日志或未来可能的格式转换
    response_format_req = data.get("response_format", "wav") 

    # 参数校验
    if not model_id or model_id not in SUPPORTED_MODELS:
        return Response(f'{{"error": {{"message": "Invalid or missing model. Supported: {SUPPORTED_MODELS}", "type": "invalid_request_error"}}}}', status=400, mimetype="application/json")
    if not input_text:
        return Response('{"error": {"message": "Missing input text.", "type": "invalid_request_error"}}', status=400, mimetype="application/json")
    if not voice_key or voice_key not in SUPPORTED_VOICES:
        return Response(f'{{"error": {{"message": "Invalid or missing voice. Supported: {SUPPORTED_VOICES}", "type": "invalid_request_error"}}}}', status=400, mimetype="application/json")
    if response_format_req not in SUPPORTED_FORMATS:
         logger.warning(f"Client requested unsupported format '{response_format_req}'. Defaulting to WAV for generation.")
         # We will still generate WAV, the mimetype of the response will be audio/wav.

    reference_audio_file_path = VOICE_TO_REFERENCE.get(voice_key) 
    if not reference_audio_file_path or not os.path.exists(reference_audio_file_path):
        logger.error(f"Critical: Reference audio file '{reference_audio_file_path}' for voice '{voice_key}' not found. Using fallback '{D_WAV_PATH}' if different, or this is an error.")
    
        return Response('{"error": {"message": "Server configuration error: reference audio missing.", "type": "server_error"}}', status=500, mimetype="application/json")

    generated_audio_path_local = None
    try:
        # 调用核心函数生成音频 (只使用 infer_fast)
        generated_audio_path_local, actual_mime_type = _generate_audio_fast(
            input_text,
            reference_audio_file_path # This will be D_WAV_PATH
        )
        
        # 定义文件分块读取的生成器
        def stream_file_chunks(file_path_to_stream, chunk_size=8192): # Increased chunk size
            try:
                with open(file_path_to_stream, 'rb') as f:
                    while True:
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        yield chunk
                logger.info(f"File '{file_path_to_stream}' streamed successfully.")
            except Exception as e_stream:
                logger.error(f"Error during file streaming of '{file_path_to_stream}': {e_stream}", exc_info=True)
            finally: # Ensure cleanup
                if os.path.exists(file_path_to_stream):
                    try:
                        os.unlink(file_path_to_stream)
                        logger.info(f"Temporary audio file '{file_path_to_stream}' deleted after streaming.")
                    except Exception as e_cleanup:
                        logger.error(f"Error deleting streamed temp file '{file_path_to_stream}': {e_cleanup}")
        
        return Response(stream_with_context(stream_file_chunks(generated_audio_path_local)), mimetype=actual_mime_type)

    except FileNotFoundError as e_fnf: 
        logger.error(f"File not found error during request processing: {e_fnf}", exc_info=True)
        return Response(f'{{"error": {{"message": "Server configuration error: {str(e_fnf)}", "type": "server_error"}}}}', status=500, mimetype="application/json")
    except ValueError as e_val: 
        logger.error(f"Invalid parameter error: {e_val}", exc_info=True)
        return Response(f'{{"error": {{"message": "Invalid parameter: {str(e_val)}", "type": "invalid_request_error"}}}}', status=400, mimetype="application/json")
    except RuntimeError as e_rt: 
        logger.error(f"TTS generation runtime error: {e_rt}", exc_info=True)
        return Response(f'{{"error": {{"message": "Audio generation failed: {str(e_rt)}", "type": "server_error"}}}}', status=500, mimetype="application/json")
    except Exception as e_general:
        logger.error(f"Unexpected error processing request: {e_general}", exc_info=True)
        if generated_audio_path_local and os.path.exists(generated_audio_path_local): # Final cleanup attempt
            try: os.unlink(generated_audio_path_local)
            except: pass
        return Response('{"error": {"message": "An unexpected server error occurred.", "type": "server_error"}}', status=500, mimetype="application/json")


if __name__ == "__main__":
    logger.info("--- Starting IndexTTS API Server (Fast Inference Only) ---")
    
    # 尝试创建 voices 目录（如果不存在）
    if not os.path.isdir(VOICES_DIR_PATH):
        try:
            os.makedirs(VOICES_DIR_PATH)
            logger.info(f"Created reference voices directory: '{VOICES_DIR_PATH}'.")
            logger.info(f"Please ensure '{REFERENCE_AUDIO_FILENAME}' is placed in this directory.")
        except OSError as e:
            logger.error(f"Could not create voices directory '{VOICES_DIR_PATH}': {e}. Please create it manually.")

    if check_dependencies():
        logger.info(f"API Key for testing: {API_KEY}")
        logger.info(f"All voices will use reference audio: '{D_WAV_PATH}'")
        logger.info(f"Supported 'model' values: {SUPPORTED_MODELS}")
        logger.info(f"Supported 'voice' values: {SUPPORTED_VOICES} (all map to the same reference)")
        logger.info("Backend generates WAV audio; client 'response_format' is noted but doesn't change output format.")
        app.run(host="0.0.0.0", port=5000, debug=False) # 默认端口号5000，若冲突请自行修改
    else:
        logger.critical("Essential dependencies are missing. API server cannot start.")
        logger.critical(f"Please ensure your model is in '{MODEL_DIR}' and '{REFERENCE_AUDIO_FILENAME}' is in '{VOICES_DIR_PATH}'.")