# Colossus Blender MCP Documentation

Welcome to the official documentation for the **Colossus Blender MCP** integration. This project implements a high-fidelity 3D scene creation pipeline using the **VIGA** (Vision-as-Inverse-Graphics Analysis-by-Synthesis) framework.

## Core Framework: VIGA

VIGA is a closed-loop multi-agent system that treats 3D modeling as an iterative search problem. By combining high-level planning with active visual verification, it achieves human-level precision in complex Blender environments.

### Key Components
- **Generator**: Synthesizes Python scripts for Blender based on task intent and historical feedback.
- **Verifier**: Uses active viewport exploration and computer vision to analyze renders and provide corrective feedback.
- **Blender MCP Interface**: A robust bridge allowing LLMs to execute code directly within Blender 4.4+.

---

## Documentation Index

### 🚀 Getting Started
- [**Setup Guide**](SETUP_GUIDE.md): Installation, environment configuration, and model deployment (Qwen3-VL).
- [**Development Guide**](DEVELOPMENT_GUIDE.md): Standards for contributing to the Colossus codebase.

### 🧠 Architecture & Design
- [**Agent Design**](AGENT_DESIGN.md): Detailed breakdown of the **Generator** and **Verifier** roles.
- [**VIGA Algorithm**](VIGA_ALGORITHM.md): Mathematics and logic behind the Analysis-by-Synthesis loop.
- [**Model Support**](MODEL_SUPPORT.md): Information on Qwen3-VL (8B/30B) and Gemini 3 Pro integration.

### 📊 Status & References
- [**Project Summary**](PROJECT_SUMMARY.md): Current implementation state and milestone tracking.
- [**Verified Working**](VERIFIED_WORKING.md): List of tested hardware configurations and Blender versions.

---

## Performance Targets (Jan 2026)
- **Primary Model**: Qwen3-VL-30B (Local GGUF via llama.cpp).
- **Secondary Model**: Qwen3-VL-8B (Optimized for 8GB-12GB VRAM).
- **Blender Version**: 4.4.x (Active Development).
- **GPU Optimization**: Native profiles for NVIDIA RTX 3090/4090/5090.

---
*Version: 0.4.0 | Last Updated: January 2026*
