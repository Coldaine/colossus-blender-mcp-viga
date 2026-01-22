# Colossus Blender MCP - Quick Start Guide

## Implementation Status: Phase 2 Complete ✅

**What's been implemented:**
- ✅ Local vision model integration (Qwen2.5-VL-72B)
- ✅ Game asset pipeline (LODs, UVs, PBR, FBX export)
- ✅ War Thunder, World of Warships, Unity, Unreal profiles
- ✅ Comprehensive Blender prompt with game asset instructions
- ✅ Test suites and example workflows

---

## Quick Setup (30 minutes)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
pip install opencv-python numpy
```

### 2. Install Blender 4.4+
- Download: https://www.blender.org/download/
- Install MCP addon from `config/addon.py`
- Enable in Preferences > Add-ons > "Blender MCP"

### 3. Deploy Vision Model (Optional)
```powershell
# Windows (experimental - WSL2 recommended)
.\config\deploy_vision_model.ps1

# Linux/WSL2 (recommended for ROCm)
bash config/deploy_vision_model.sh
```

**Note:** Vision model requires ~145GB download + 14-18GB VRAM

### 4. Configure Environment
Edit `.env`:
```env
VISION_MODEL_ENDPOINT=http://localhost:8000/v1
BLENDER_HOST=localhost
BLENDER_PORT=9876
GAME_ASSET_OUTPUT_DIR=./outputs/game_assets
HUGGINGFACE_TOKEN=hf_************Vfy
```

**Hugging Face token:** The real token is stored in Bitwarden Secrets (BWS) under the key `HUGGINGFACE_TOKEN`. For security this document shows the token masked. To populate your local `.env` with the real token, either copy it from BWS or run:

```bash
# get the secret value and append to .env (requires bws and jq)
echo "HUGGINGFACE_TOKEN=$(bws secret get --key HUGGINGFACE_TOKEN -o json | jq -r '.value')" >> .env
```

Do not commit `.env` to source control — `.gitignore` already excludes it.

---

## Quick Test

```bash
# Test Blender connection
python test_connection.py

# Test vision model (if deployed)
python test_vision_model.py

# Run example workflow
python examples/game_asset_workflow.py
```

---

## Usage Example

```python
from pathlib import Path
from src.colossus_blender.game_asset_agent import process_battleship_mesh
from src.colossus_blender import create_blender_client

# Connect to Blender
blender = await create_blender_client(mode="socket")

# Process battleship into game asset
metadata = await process_battleship_mesh(
    mesh_path=Path("./inputs/uss_iowa.obj"),
    profile_name="war_thunder",  # or "world_of_warships", "unity", "unreal"
    blender_mcp_client=blender
)

print(f"Quality: {metadata.overall_quality:.1%}")
print(f"FBX: {metadata.fbx_path}")
```

---

## Game Asset Profiles

| Profile | LOD0 Tris | Use Case |
|---------|-----------|----------|
| `war_thunder` | 80,000 | Gaijin Entertainment |
| `world_of_warships` | 50,000 | Wargaming.net |
| `unity` | 50,000 | Unity Asset Store |
| `unreal` | 80,000 | Unreal Engine 5+ |

---

## Next Steps

### Phase 3: Testing
- [ ] Acquire test battleship OBJ files
- [ ] Run basic pipeline test
- [ ] Verify FBX exports in game engine

### Phase 4: ProjectBroadsideStudio Integration (Future)
- File-based OBJ handoff
- Reference image comparison
- Batch processing workflow

---

## Files Created

**Core System:**
- `src/colossus_blender/vision_evaluator.py` - Local Qwen2.5-VL client
- `src/colossus_blender/game_asset_agent.py` - Game asset pipeline
- `src/colossus_blender/game_asset_config.py` - Profile configurations

**Deployment:**
- `config/deploy_vision_model.sh` - Linux deployment
- `config/deploy_vision_model.ps1` - Windows deployment
- `test_vision_model.py` - Vision model tests

**Examples:**
- `examples/game_asset_workflow.py` - Complete workflow examples

**Documentation:**
- `prompts/blender_mcp_system_prompt.md` - Updated with game asset section
- `SETUP_GUIDE.md` - This file

---

**Version:** 0.3.0 | **Status:** Ready for Testing
