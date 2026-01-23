# Colossus Blender MCP - Setup Guide (Jan 2026)

This is a personal tooling repo for experimenting with agentic Blender workflows. The repository is currently in a rebuild phase: legacy code and outdated docs have been moved into `docs/archive/` and `src/archive/`.

## Prerequisites

- **Blender 4.4+**: Installed at standard location (e.g., `C:\Program Files\Blender Foundation\Blender 4.4`).
- **NVIDIA GPU**: RTX 3090, 4090, or 5090 (24GB+ VRAM recommended for 30B model).
- **Python**: Prefer **Python 3.12** for broad package compatibility. Python 3.13 can work, but some native wheels (notably OpenCV) may lag.
- **Environment manager**: `uv` (recommended) or standard `venv`.

## 1. Environment Setup

### Recommended: uv + venv

Create and use a local virtual environment:

```powershell
uv venv --python 3.12
uv pip install -r requirements.txt
```

If you prefer standard tooling:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### Blender bridge

The Blender-side bridge is being rebuilt. If you need the legacy addon for reference, it is archived under `src/archive/config/`.

## 2. Model Configuration (Qwen3-VL)

Models can be local (e.g. GGUF served by `llama.cpp`) or cloud. For this personal repo, API keys are expected to come from your **user-level environment variables** (Windows Environment Variables, PowerShell profile, etc.).

### Local GGUF deployment

Model binaries live under `models/`. Server launch scripts may be reintroduced later; legacy scripts are currently archived under `src/archive/scripts/`.

### Environment variables (preferred)

Recommended: set these in your OS user environment (not committed):

- `ANTHROPIC_API_KEY` (optional)
- `GOOGLE_AI_API_KEY` (optional)
- `ZAI_API_KEY` (optional)
- `QWEN3_VL_ENDPOINT` (optional, if running a local server)

Optional: you may use a local `.env` file for convenience. Never commit it. See `.env.example` for the variable names.

## 3. Verifying the Setup

The automated test suite is being rebuilt (legacy tests are archived under `tests/archive/`). Verification steps will be added as Phase I implementation lands.

## 4. Troubleshooting

- **Blender Connection Refused**: Ensure the MCP addon is enabled and Blender is not frozen.
- **CUDA Out of Memory**: If using 30B model on a 24GB card, ensure no other heavy processes are running, or switch to the 8B model.
- **Python 3.13 install issues**: If dependency installs fail, switch to Python 3.12 for now.

---
*Version: 0.4.0 | Date: January 2026*
