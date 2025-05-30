# IndexTTS-API (OpenAI TTS API Format TTS Service)

[中文](https://github.com/opanterao/index-tts-api/blob/main/README(cn-zh).md)

This project implements a high-performance Text-to-Speech (TTS) API service based on the `index-tts` library. It is compatible with the OpenAI TTS API interface specification and defaults to using the `index-tts` `infer_fast` (fast/batch inference) mode to improve inference efficiency for long texts. All voices (e.g., `alloy`, `echo`, etc.) uniformly use the `voices/audio.wav` file as the reference audio for zero-shot voice cloning.

## ✨ Features

* **OpenAI API Compatible**: Provides a `/v1/audio/speech` endpoint, which can directly replace or integrate with applications supporting the OpenAI TTS API (such as Open WebUI).
* **Fast Inference by Default**: Defaults to using the `index-tts` `infer_fast` method, optimizing synthesis performance for long sentences.
* **Unified Reference Voice**: All standard OpenAI voices (`alloy`, `echo`, `fable`, `onyx`, `nova`, `shimmer`) use `voices/audio.wav` as the reference audio.

## 🚀 Environment Requirements

* `index-tts`: Please refer to the [official index-tts library](https://github.com/index-tts/index-tts) for installation and its dependencies.
* For other dependencies, please see the `requirements.txt` file.

## 🛠️ Installation and Deployment

1.  **Clone this project**:
    ```bash
    git clone https://github.com/opanterao/index-tts-api.git
    cd index-tts-api
    ```

2.  **Create and activate a virtual environment** (recommended):
    ```bash
    # Using Conda
    conda create -n index-tts-api python=3.10
    conda activate index-tts-api
    # Or using venv
    # python -m venv venv
    # source venv/bin/activate  # Linux/macOS
    # venv\Scripts\activate    # Windows
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Model Preparation**:
    * Download model files from the following links:
        * [index-tts (ModelScope)](https://modelscope.cn/models/IndexTeam/Index-TTS)
        * [index-tts-1.5 (ModelScope)](https://modelscope.cn/models/IndexTeam/IndexTTS-1.5)
    * Place the downloaded **complete model folder** (e.g., the entire folder containing `.pth` files, `config.yaml`, `bpe.model`, etc.) into the `checkpoints/` directory in the project root.
        Your directory structure should look like this (using the `index-tts-1.5` model as an example):
        ```
        [Project Root]/
        ├── checkpoints/
        │   └── index-tts-1.5/  <--- Place the complete downloaded model folder here
        │       ├── config.yaml
        │       ├── gpt.pth
        │       └── ... (other model files)
        ├── TTS_API.py
        └── ...other files...
        ```
    * **Important**: Ensure the `MODEL_DIR` constant in your `TTS_API.py` file points to the specific model folder name under `checkpoints/`, for example, `checkpoints/index-tts-1.5`.

5.  **Prepare Reference Audio**:
    * Create a folder named `voices` in the project root directory.
    * Place your reference sound file `audio.wav` into the `voices` folder. The API service will load the reference audio from this path.
        ```
        [Project Root]/
        ├── TTS_API.py
        ├── voices/
        │   └── audio.wav  <--- Ensure this file exists
        └── ...other files...
        ```

6.  **Start the API Service**:
    * Ensure your API script is correctly named (if your filename is `TTS_API.py.py`, please correct it to `TTS_API.py` or use the correct name in the command). Assuming the filename is `TTS_API.py`:
    ```bash
    python TTS_API.py
    ```
    The service starts on `http://0.0.0.0:5000` by default. You can modify the host and port in the `app.run()` call at the bottom of the `TTS_API.py` file.

## 📡 API Usage

Once the service is running, you can send POST requests to the following endpoint:

* **Endpoint**: `http://<your_server_ip_or_localhost>:5000/v1/audio/speech`
* **Method**: `POST`
* **Headers**:
    * `Authorization: Bearer <your_API_KEY>` (The `API_KEY` configured in `TTS_API.py`)
    * `Content-Type: application/json`
* **Body (JSON)**:
    ```json
    {
        "model": "tts-1",
        "input": "Hello, world! This is a fast inference speech synthesis service provided by IndexTTS.",
        "voice": "alloy",
        "response_format": "wav"
    }
    ```
    * `model`: Options are `"tts-1"` or `"tts-1-hd"`.
    * `voice`: Options are `alloy`, `echo`, `fable`, `onyx`, `nova`, `shimmer` (all use the timbre from `voices/audio.wav`).
    * `response_format`: The API currently primarily outputs in WAV format; requests for other formats are noted for logging purposes.

### Request Example (`curl`)

```bash
curl -X POST http://localhost:5000/v1/audio/speech \
-H "Authorization: Bearer sk-test-api-key-1234567890" \ # Replace with your API Key
-H "Content-Type: application/json" \
-d '{
    "model": "tts-1",
    "input": "Integrating with Open WebUI via API is very convenient.",
    "voice": "nova"
}' \
--output speech_output.wav # Audio will be streamed and saved to this file
