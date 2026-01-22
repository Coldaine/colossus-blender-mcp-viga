# Model Support & Server Configuration

This project is optimized for the **Qwen3-VL** family of vision-language models. It supports both local GGUF serving on Windows and remote high-performance serving via vLLM on Linux.

## Supported Models

### 1. Qwen3-VL-8B
- **Capability**: Excellent for fast iterations, material tweaking, and simple geometry.
- **Hardware**: 24GB VRAM (Single RTX 3090/4090).
- **Format**: GGUF (via llama.cpp) or AWQ/GPTQ (via vLLM).

### 2. Qwen3-VL-30B
- **Capability**: Superior spatial reasoning, complex scene analysis, and specific object placement.
- **Hardware**: 80GB VRAM (or 2x 40GB). Requires quantization (AWQ) for 48GB multi-GPU setups.

## Serving Backends

### Windows: llama-cpp-python (GGUF)
*Note: As of Jan 2026, Qwen3-VL architecture support in llama.cpp is evolving. Use the provided launcher scripts for the latest compatibility.*
- **Setup**:
    ```powershell
    ./scripts/launch_llamacpp_server.ps1 -ModelPath "models/.../qwen3.gguf" -Port 8001
    ```

### Linux/WSL2: vLLM / SGLang (AWQ/GPTQ)
- **Primary Recommendation**: Best throughput and compliance with OpenAI API standards.
- **Setup**:
    ```bash
    vllm serve "Qwen/Qwen3-VL-8B-Instruct-AWQ" --port 8000 --gpu-memory-utilization 0.95
    ```

## Multi-Modal Strategy
The model client in `src/colossus_blender/viga/modern_models.py` uses a **Multimodal Robustness Pattern**:
1.  Attempt to send the image + text to the configured endpoint.
2.  If the endpoint returns a `400` error (e.g., image token limit or unsupported format), the client automatically falls back to **Text-Only Mode**.
3.  In Text-Only mode, it relies on the `scene_info` JSON summary to provide feedback, ensuring the loop never breaks.

## API Keys
Configure the following in `.env`:
- `OPENAI_API_BASE`: URL of your inference server.
- `OPENAI_API_KEY`: Dummy value if using local/vLLM servers.
- `HF_TOKEN`: Required for model downloads.
