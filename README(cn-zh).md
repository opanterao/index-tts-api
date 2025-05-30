# index-tts-api

index-tts to OpenAI API server

# IndexTTS-API (OpenAI TTS API格式)



本项目基于 `index-tts` 库实现了一个高性能的文本转语音 (TTS) API 服务。它兼容 OpenAI 的 TTS API 接口规范，并默认采用 `index-tts` 的 `infer_fast`（快速/批次推理）模式以提高长文本的推理效率。所有语音（如 `alloy`, `echo` 等）统一使用 `参考音频文件 audio.wav` 作为参考音频进行零样本语音克隆。



## ✨ 功能特性



* **OpenAI API 兼容**：提供 `/v1/audio/speech` 端点，可直接替换或接入支持 OpenAI TTS API 的应用（如 Open WebUI）。

* **快速推理默认**：默认使用 `index-tts` 的 `infer_fast` 方法，优化长句子的合成性能。

* **统一参考音色**：所有 OpenAI 标准语音（`alloy`, `echo`, `fable`, `onyx`, `nova`, `shimmer`）均使用 `voices/audio.wav` 作为参考音频。



## 🚀 环境要求



* `index-tts` 参考 [index-tts官方库](https://github.com/index-tts/index-tts) 及其依赖

* 其他依赖请见 `requirements.txt`



## 🛠️ 安装与部署



1.  **克隆本项目**：

    ```bash

    https://github.com/opanterao/index-tts-api.git

    cd index-tts-api

    ```



2.  **创建并激活虚拟环境** (推荐)：

    ```bash

    conda create -n index-tts-api python=3.10

    conda activate index-tts-api

    ```



3.  **安装依赖**：

    ```bash

    pip install -r requirements.txt

    ```



4.  **模型准备**：



    模型文件下载：

    [index-tts](https://modelscope.cn/models/IndexTeam/Index-TTS)

    [index-tts-1.5](https://modelscope.cn/models/IndexTeam/IndexTTS-1.5)



    将下载的完整模型文件夹放入/checkpoints/



6.  **准备参考音频**：

    * 在项目根目录下创建一个名为 `voices` 的文件夹。

    * 将你的 参考声音文件 `audio.wav` 文件放入 `voices` 文件夹中。API 服务会从此路径加载参考音频。

        ```

        [项目根目录]/

        ├── TTS_API.py

        ├── voices/

        │   └── audio.wav  <--- 确保此文件存在

        └── ...其他文件...

        ```



7.  **启动 API 服务**：

    ```bash

    python tts_api.py.py

    ```

    服务默认启动在 `http://0.0.0.0:5000`。你可以在 `tts_api.py.py` 文件底部的 `app.run()` 中修改主机和端口。



## 📡 API 使用



服务启动后，你可以向以下端点发送 POST 请求：



* **Endpoint**: `http://<你的服务器IP或localhost>:5000/v1/audio/speech`

* **Method**: `POST`

* **Headers**:

    * `Authorization: Bearer <你的API_KEY>` (在 `tts_api.py` 中配置的 `API_KEY`)

    * `Content-Type: application/json`

* **Body (JSON)**:

    ```json

    {

        "model": "tts-1", // 或 "tts-1-hd"

        "input": "你好，世界！这是 IndexTTS 提供的快速推理语音合成服务。",

        "voice": "alloy", // alloy, echo, fable, onyx, nova, shimmer (均使用 audio.wav 音色)

        "response_format": "wav" // API目前主要输出WAV格式，其他格式请求仅作记录

    }

    ```



### 请求示例 (`curl`)



```bash

curl -X POST http://localhost:5000/v1/audio/speech \

-H "Authorization: Bearer sk-test-api-key-1234567890" \ # 替换为你的 API Key

-H "Content-Type: application/json" \

-d '{

    "model": "tts-1",

    "input": "通过API接入到Open WebUI非常方便。",

    "voice": "nova"

}' \

--output speech_output.wav # 音频将流式保存到此文件
