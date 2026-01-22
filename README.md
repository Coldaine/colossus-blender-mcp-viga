# Colossus Blender MCP - VIGA Framework

A high-fidelity 3D generation and verification system for Blender, powered by the **VIGA (Vision-as-Inverse-Graphics Analysis-by-Synthesis)** algorithm.

This project integrates state-of-the-art vision models (Qwen3-VL 8B/30B) with Blender via a Model Context Protocol (MCP) server, enabling a closed-loop "Analysis-by-Synthesis" workflow where an AI agent plans, executes, and visually verifies 3D scene construction.

## 🚀 Quick Start

1.  **Clone the Repo**:
    ```bash
    git clone https://github.com/Coldaine/colossus-blender-mcp-viga.git
    cd colossus-blender-mcp-viga
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure Environment**:
    Copy `.env.example` to `.env` and add your Hugging Face token and API keys.

4.  **Download Models**:
    ```powershell
    ./scripts/download_qwen3_vl_gguf.ps1 -Size 8B
    ```

5.  **Run VIGA Loop**:
    ```bash
    python -m src.colossus_blender.viga.agent --task "Create a medieval castle gate with realistic lighting"
    ```

## 🏗️ Architecture

The system is built on two primary loops:
- **VIGA Loop (Algorithm 1)**: The core Analysis-by-Synthesis process where a **Generator** synthesizes 3D code and a **Verifier** inspects the rendered viewport.
- **D5 Orchestrator (Legacy)**: A multi-agent decomposition pattern (Planner, Designer, Executor, Evaluator, Refiner).

## 📚 Documentation

Detailed documentation can be found in the [a/docs](a/docs) folder:
- [VIGA Algorithm](a/docs/VIGA_ALGORITHM.md): Deep dive into the Analysis-by-Synthesis loop.
- [Agent Design](a/docs/AGENT_DESIGN.md): Detailed roles of the Generator and Verifier agents.
- [Model Support](a/docs/MODEL_SUPPORT.md): Qwen3-VL setup, quantization, and serving (vLLM/SGLang).
- [Remote Serving Plans](a/docs/plans/remote_infrastructure.md): Architecture for distributed compute.

## 🛠️ Tech Stack
- **Blender**: Core 3D engine.
- **MCP (Model Context Protocol)**: Communication bridge between AI and Blender.
- **Qwen3-VL (8B/30B)**: Primary vision-language backbone.
- **Claude 3.5 Sonnet**: High-level planning and reasoning.

---
*Based on the research paper: VIGA: Vision-as-Inverse-Graphics Analysis-by-Synthesis (arXiv:2601.11109v1)*
