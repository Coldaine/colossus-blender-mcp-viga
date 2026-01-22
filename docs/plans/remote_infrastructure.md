# Infrastructure Plan: Remote Model Serving & Distributed Rendering

This document outlines the architecture for offloading high-compute tasks (Qwen3-VL serving and Blender cycles rendering) to dedicated Linux-based nodes or cloud GPUs while maintaining a local development environment.

## 1. Remote Model Serving (vLLM / SGLang)

Given the architectural challenges of running `qwen3vl` natively on Windows/llama.cpp, we recommend a Linux host (Physical or WSL2) running `vLLM`.

### Hardware Requirements
- **Qwen3-VL-8B**: 24GB VRAM (Single RTX 3090/4090).
- **Qwen3-VL-30B**: 2x 40GB or 1x 80GB VRAM (A100/H100 or dual 3090/4090 with AWQ/GPTQ).

### LAN/VPN Configuration
1.  **Tailscale/ZeroTier**: Create a virtual private network for secure access if the server is off-site.
2.  **Firewall**: Open port `8000` (vLLM) and `8001` (SGLang) on the host.
3.  **Client Update**: Point `src/colossus_blender/viga/modern_models.py` to the remote IP.

## 2. Distributed Rendering (Cycles/Eevee)

To speed up the VIGA verification loop, render tasks can be dispatched to a GPU worker.

### Setup
- **Blender Network Render**: Use a custom MCP tool to dispatch `.blend` files to a worker node.
- **Shared Storage**: Use a NAS or SMB share (mapped to `Z:` on Windows and `/mnt/render` on Linux) so both the Agent and the Renderer see the same file paths.

## 3. Deployment Phases
- **Phase 1**: Local WSL2 serving (current workaround).
- **Phase 2**: Dedicated Ubuntu Server with NVIDIA Docker.
- **Phase 3**: Global access via VPN for remote collaborative testing.
