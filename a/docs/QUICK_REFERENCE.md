# Colossus Blender MCP - Quick Reference

## Essential Information

### API Endpoint (CORRECT)
```
https://api.z.ai/api/coding/paas/v4/chat/completions
```

### API Key Location
```
File: .env
Variable: ZAI_API_KEY
```

### Models Available
- **GLM-4.5V**: Vision + text (use for screenshot analysis)
- **GLM-4.6**: Text only (use for code generation)

---

## Quick Setup

```bash
# 1. Set environment
cp .env.example .env
# (Already has your API key)

# 2. Install dependencies
pip install -r requirements.txt

# 3. Test endpoint
python test_glm_working.py

# 4. Install Blender addon
# Open Blender → Preferences → Add-ons → Install → config/addon.py

# 5. Run example
cd examples
python basic_usage.py
```

---

## Testing Commands

### Test GLM-4.5V Vision
```bash
python test_glm_working.py
```

### Test Blender Connection
```bash
python test_connection.py
```

### Test with curl
```bash
# Load API key
source .env  # or: set -a; source .env; set +a

# Test GLM-4.5V
curl -X POST https://api.z.ai/api/coding/paas/v4/chat/completions \
  -H "Authorization: Bearer $ZAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"glm-4.5v","messages":[{"role":"user","content":"Test"}]}'
```

---

## File Structure

```
colossus_blender_mcp/
├── .env                          # API keys (DO NOT COMMIT)
├── src/colossus_blender/
│   ├── glm_vision.py            # GLM-4.5V integration
│   ├── orchestrator.py          # Multi-agent system
│   ├── mcp_client.py            # Blender communication
│   └── gpu_config.py            # GPU optimization
├── examples/
│   ├── basic_usage.py           # Simple scene creation
│   └── advanced_workflow.py     # Multi-scene examples
├── config/
│   ├── addon.py                 # Blender MCP addon
│   └── claude_desktop_config.json
└── test_glm_working.py          # Endpoint verification
```

---

## Common Tasks

### Create a Scene
```python
from colossus_blender import ColossusD5Orchestrator, WorkflowState
from colossus_blender.glm_vision import GLMVisionClient
from dotenv import load_dotenv
import os

load_dotenv()

# Configure
glm_vision = GLMVisionClient()
state = WorkflowState(
    user_intent="Create a cyberpunk scene",
    max_iterations=3,
    satisfaction_threshold=0.75
)

# Run
final_state = await orchestrator.run(state)
```

### Test Vision Analysis
```python
from colossus_blender.glm_vision import evaluate_screenshot_with_glm

result = await evaluate_screenshot_with_glm(
    screenshot_base64="...",
    user_intent="Test scene"
)
print(f"Quality: {result['overall_score']}")
```

---

## Key Configuration

### GLM Vision Client
```python
from colossus_blender.glm_vision import GLMConfig

config = GLMConfig(
    api_key=os.getenv("ZAI_API_KEY"),
    api_base="https://api.z.ai/api/coding/paas/v4",
    model="glm-4.5v",
    thinking_enabled=True
)
```

### Blender MCP Client
```python
from colossus_blender import create_blender_client

blender = await create_blender_client(
    mode="socket",
    host="localhost",
    port=9876
)
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "API key not found" | Check `.env` file exists and is loaded |
| "Connection refused" | Start Blender with MCP addon enabled |
| "Model not found" | Use lowercase: `glm-4.5v` or `glm-4.6` |
| "1113 error" | Wrong endpoint - use `/api/coding/paas/v4/` |

---

## Documentation Files

- **QUICKSTART.md** - 15-minute setup guide
- **ENDPOINT_CONFIGURATION.md** - API endpoint details
- **VERIFIED_WORKING.md** - Test results
- **SETUP_GUIDE.md** - Detailed installation
- **README.md** - Full documentation

---

## Status

✅ Endpoint verified: `/api/coding/paas/v4/chat/completions`
✅ GLM-4.5V vision: Working
✅ GLM-4.6 coding: Working
✅ API key: Active
✅ Code: Ready
✅ Tests: Passing

**Ready for production use!**
