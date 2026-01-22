# Colossus Blender MCP - Project Summary (Jan 2026)

## Overview

Colossus is a state-of-the-art 3D scene creation system that integrates Blender with the **VIGA** (Vision-as-Inverse-Graphics Analysis-by-Synthesis) framework. It leverages the **Qwen3-VL** family of models to provide a closed-loop creation and verification pipeline.

## Core Implementation Status

### 1. VIGA Framework
**File**: `src/colossus_blender/viga/agent.py`

Unlike traditional task decomposition, VIGA uses an Analysis-by-Synthesis approach:
- **Generator**: Synthesizes Python code directly for the Blender environment.
- **Verifier**: Conducts active exploration (viewpoint changes) and visual reasoning to identify discrepancies between the current scene and the user intent.
- **Convergence**: The loop continues until the Verifier signals completion or reaches the iteration limit.

### 2. Qwen3-VL Integration
**File**: `src/colossus_blender/viga/modern_models.py`

The system is optimized for the **Qwen3-VL** model (released Jan 2026), featuring:
- **8B and 30B variants**: Native support for local GGUF serving via `llama.cpp`.
- **Multimodal Reasoning**: Interleaved image-text tokens for high-fidelity visual feedback.
- **Robust Fallback**: Automatic failover to text-only reasoning if vision processing fails.

### 3. Blender MCP Bridge
**File**: `src/colossus_blender/mcp_client.py`

A robust implementation of the Model Context Protocol for Blender:
- Secure execution of LLM-generated Python code.
- High-speed viewport screenshot capture (1024px).
- Metadata-rich scene telemetry (objects, lights, shaders).

## Technical Milestones (Jan 2026)

- [x] **Phase 1: Foundation**: Blender 4.4 compatibility and MCP addon implementation.
- [x] **Phase 2: VIGA Core**: Implementation of Generator, Verifier, and Memory systems.
- [x] **Phase 3: Qwen3-VL Support**: Local serving via `llama.cpp` and specialized prompt engineering.
- [x] **Phase 4: Game Asset Pipeline**: Specialized profiles for War Thunder, Unity, and Unreal.
- [ ] **Phase 5: Remote Infrastructure**: (In Planning) Deployment of vLLM clusters for 30B/72B models.

## Repository Structure

```
colossus_blender_mcp/
├── src/colossus_blender/
│   ├── viga/                # Core VIGA agents (Generator/Verifier)
│   ├── mcp_client.py        # Blender communication layer
│   ├── gpu_config.py        # NVIDIA RTX 3090/4090/5090 optimizations
│   └── vision_utils.py      # Screenshot and code extraction utilities
├── config/
│   ├── addon.py             # Blender-side MCP server
│   └── *.ps1/sh             # Deployment and launch scripts
├── prompts/                 # Expert system prompts for Qwen3-VL
└── a/docs/                  # VIGA documentation and research guides
```

## Hardware Requirements

- **GPU**: NVIDIA RTX 3090 (24GB) minimum for local 30B GGUF.
- **OS**: Windows 11 (Native) or Linux (vLLM).
- **Blender**: 4.4.x (Optimized for EEVEE-Next and Cycles).

---
*Status: Active Development | Version: 0.4.0 | Date: January 2026*
