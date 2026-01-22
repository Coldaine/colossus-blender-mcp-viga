# Staged PR Strategy

The transition to a public repository will be handled in staged Pull Requests to allow for incremental review and safety checks.

## PR 1: Core Framework Initialization
- **Goal**: Establish the base MCP client and Blender integration.
- **Includes**: `src/colossus_blender/mcp_client.py`, `src/colossus_blender/orchestrator.py`.
- **Status**: Stable.

## PR 2: VIGA Implementation (Algorithm 1)
- **Goal**: Merge the Analysis-by-Synthesis agent.
- **Includes**: `src/colossus_blender/viga/agent.py`, `src/colossus_blender/viga/modern_models.py`.
- **Dependencies**: Qwen3-VL supporting infrastructure.

## PR 3: Model Downloader & Utilities
- **Goal**: Add the GGUF search and download scripts.
- **Includes**: `scripts/hf_find_qwen3_vl_gguf.py`, `scripts/download_qwen3_vl_gguf.ps1`.

## PR 4: Security & Infrastructure Docs
- **Goal**: Merge the `a/docs` folder and deployment plans.
- **Includes**: `a/docs/plans/remote_infrastructure.md`.
