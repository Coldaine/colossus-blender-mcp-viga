# Colossus Blender MCP - Setup Guide (Jan 2026)

This guide provides instructions for setting up the VIGA framework with Qwen3-VL (8B/30B) for vision-guided Blender automation.

## Prerequisites

- **Blender 4.4+**: Installed at standard location (e.g., `C:\Program Files\Blender Foundation\Blender 4.4`).
- **NVIDIA GPU**: RTX 3090, 4090, or 5090 (24GB+ VRAM recommended for 30B model).
- **Python 3.10+**: With `pip` or `uv` package manager.

## 1. Environment Setup

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Install Blender MCP Addon
1. Locate `config/addon.py` in this repository.
2. Open Blender 4.4.
3. Go to **Edit > Preferences > Add-ons > Install**.
4. Select `config/addon.py`.
5. Enable **Interface: Blender MCP**.
6. Check the system console to verify: `MCP Server Started on port 9876`.

## 2. Model Configuration (Qwen3-VL)

The VIGA framework uses **Qwen3-VL** for both code generation (Generator) and visual verification (Verifier).

### Local GGUF Deployment (Recommended)
We use `llama.cpp` to serve Qwen3-VL GGUF files.

1. **Download Model**:
   ```powershell
   pwsh -File scripts/download_qwen3_vl_gguf.ps1 -Size 30B
   ```
2. **Launch Server**:
   ```powershell
   pwsh -File scripts/launch_llamacpp_server.ps1 -ModelPath "models/Qwen3-VL-30B-A3B-Instruct-GGUF/Qwen3-VL-30B-A3B-Instruct-Q4_K_M.gguf" -Port 8000
   ```

### Configuration (.env)
Create or update your `.env` file in the project root:
```env
QWEN3_VL_ENDPOINT=http://localhost:8000/v1
QWEN3_VL_SIZE=30B
BLENDER_HOST=localhost
BLENDER_PORT=9876
```

## 3. Verifying the Setup

Run the following scripts to ensure all components are communicating correctly:

```bash
# Test Blender MCP connection
python -m pytest tests/test_vision_utils.py

# Run a basic VIGA loop test
python -m pytest tests/test_viga_agent.py
```

## 4. Troubleshooting

- **Blender Connection Refused**: Ensure the MCP addon is enabled and Blender is not frozen.
- **CUDA Out of Memory**: If using 30B model on a 24GB card, ensure no other heavy processes are running, or switch to the 8B model.
- **Vision Retries**: If the text output contains "multimodal schema rejected", ensure your `llama.cpp` version supports Qwen3-VL vision tokens.

---
*Version: 0.4.0 | Date: January 2026*
