# Colossus Blender MCP - Quick Start Guide

## 🚀 Get Running in 15 Minutes

This guide gets you from zero to creating AI-generated 3D scenes in Blender.

## Prerequisites Check

Before starting, verify you have:
- ✅ Blender 4.4 installed
- ✅ Python 3.10+
- ✅ NVIDIA GPU (RTX 3090 detected)
- ✅ UV package manager (installed at `C:\Users\pmacl\.local\bin\uv.exe`)

## Step 1: Install Python Dependencies (2 minutes)

```bash
cd "C:\Users\pmacl\OneDrive\Desktop\BLENDER\colossus_blender_mcp"

# Optional: Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Set API Keys (2 minutes)

```powershell
# Set Anthropic API key (for Claude)
setx ANTHROPIC_API_KEY "your-anthropic-api-key"

# Set Google API key (for Gemini)
setx GOOGLE_API_KEY "your-google-api-key"

# Restart your terminal to load the new variables
```

**Get API keys from**:
- Anthropic: https://console.anthropic.com/
- Google AI: https://makersuite.google.com/app/apikey

## Step 3: Install Blender MCP Addon (3 minutes)

1. **Open Blender 4.4**

2. **Go to**: Edit → Preferences → Add-ons

3. **Click**: Install (top right button)

4. **Navigate to**: `C:\Users\pmacl\OneDrive\Desktop\BLENDER\colossus_blender_mcp\config\addon.py`

5. **Select the file** and click "Install Add-on"

6. **Search** for "Blender MCP" in the add-ons list

7. **Enable it** by checking the checkbox

8. **Verify**: Open Blender console (Window → Toggle System Console)
   - You should see: "MCP Server Started on port 9876"

## Step 4: Configure Claude Desktop (3 minutes)

**Option A: Copy the config file**
```powershell
copy config\claude_desktop_config.json "%APPDATA%\Claude\claude_desktop_config.json"
```

**Option B: Manual configuration**

1. Navigate to: `%APPDATA%\Claude\claude_desktop_config.json`
2. Add this configuration:

```json
{
  "mcpServers": {
    "blender": {
      "command": "uvx",
      "args": ["blender-mcp"],
      "env": {
        "BLENDER_HOST": "localhost",
        "BLENDER_PORT": "9876"
      }
    }
  }
}
```

3. **Restart Claude Desktop**

4. **Verify**: Look for hammer icon (🔨) in Claude Desktop interface

## Step 5: Test Connection (2 minutes)

```bash
python test_connection.py
```

**Expected output**:
```
✓ Successfully connected to Blender on localhost:9876
✓ Scene info retrieved successfully
✓ Code execution successful
✓ Screenshot captured successfully
✓ GPU configuration successful
```

If all tests pass, you're ready!

## Step 6: Create Your First Scene (3 minutes)

```bash
cd examples
python basic_usage.py
```

**What happens**:
1. System connects to Blender
2. Planner analyzes the user intent
3. Designer generates Python code
4. Executor runs code in Blender (you'll see the scene appear!)
5. Evaluator captures screenshot and analyzes quality
6. Refiner suggests improvements
7. Loop repeats until quality threshold met

**Watch**:
- Console output for agent activity
- Blender viewport for scene updates
- Quality scores after each iteration

## Common Issues & Quick Fixes

### "Could not connect to Blender"
**Fix**:
1. Make sure Blender is running
2. Check Blender console shows "MCP Server Started"
3. Verify addon is enabled in Preferences

### "API key not found"
**Fix**:
```powershell
# Restart terminal after setting keys, or set them in current session:
$env:ANTHROPIC_API_KEY="your-key"
$env:GOOGLE_API_KEY="your-key"
```

### "Module not found"
**Fix**:
```bash
pip install -r requirements.txt --force-reinstall
```

## Your First Custom Scene

Edit `examples/basic_usage.py` and change the `user_intent`:

```python
user_intent = """
Create a cozy coffee shop interior with:
- Wooden tables and chairs
- Hanging pendant lights with warm glow
- Plants in the corners
- Coffee machine on the counter
- Large window showing city street
- Warm, inviting atmosphere
"""
```

Run it:
```bash
python basic_usage.py
```

## Advanced Usage

### Multiple Scenes
```bash
python advanced_workflow.py multi
```

### GPU Benchmark
```bash
python advanced_workflow.py benchmark
```

### Iterative Refinement Demo
```bash
python advanced_workflow.py refine
```

## Configuration Options

### Change GPU Mode
```python
orchestrator = ColossusD5Orchestrator(
    # ...
    gpu_mode="5090"  # Switch to 5090 when you upgrade
)
```

### Adjust Quality vs Speed
```python
state = WorkflowState(
    user_intent="Your scene description",
    max_iterations=5,              # More iterations = better quality
    satisfaction_threshold=0.85    # Higher = stricter quality
)
```

### Lower Threshold for Fast Iteration
```python
satisfaction_threshold=0.65  # Faster, lower quality
```

### Higher Threshold for Production
```python
satisfaction_threshold=0.85  # Slower, higher quality
```

## Understanding Quality Scores

- **0.50-0.65**: Basic scene created, significant issues remain
- **0.65-0.75**: Decent quality, minor improvements needed
- **0.75-0.85**: Good quality, ready for most uses
- **0.85-0.95**: Excellent quality, production-ready
- **0.95+**: Outstanding quality (rare, requires many iterations)

## Performance Tips

1. **Start low, iterate up**: Begin with threshold 0.70, increase if needed
2. **Preview quality first**: Use `gpu_mode="3090"` with preview settings
3. **Limit iterations**: 3-5 iterations is usually optimal
4. **Clear scene between runs**: Prevents memory buildup
5. **Monitor VRAM**: Keep under 20GB on RTX 3090

## What's Included

```
colossus_blender_mcp/
├── src/colossus_blender/       # Core system (1,100 lines)
│   ├── orchestrator.py         # 5-agent D5 system
│   ├── mcp_client.py          # Blender communication
│   └── gpu_config.py          # GPU optimization
├── examples/                   # Working examples
│   ├── basic_usage.py
│   └── advanced_workflow.py
├── prompts/                    # Expert system prompt
├── config/                     # Blender addon + configs
├── test_connection.py         # Connection tester
└── Documentation (3 files)    # README, SETUP_GUIDE, PROJECT_SUMMARY
```

## Next Steps

1. ✅ Complete this quickstart
2. 📖 Read `README.md` for full documentation
3. 🔧 Review `SETUP_GUIDE.md` for troubleshooting
4. 📊 Check `PROJECT_SUMMARY.md` for technical details
5. 🎨 Start creating your own scenes!

## Resources

- **Blender MCP**: https://github.com/ahujasid/blender-mcp
- **BlenderAlchemy Paper**: ECCV 2024 (vision feedback loops)
- **Claude API**: https://docs.anthropic.com/
- **Gemini API**: https://ai.google.dev/

## Support

If you get stuck:
1. Run `test_connection.py` to diagnose issues
2. Check Blender console for errors
3. Review `SETUP_GUIDE.md` troubleshooting section
4. Verify all prerequisites are met

## Success Criteria

You'll know it's working when:
- ✅ Test connection script passes all checks
- ✅ Basic example creates a scene in Blender
- ✅ Vision evaluation produces quality scores
- ✅ Iterative refinement improves the scene
- ✅ Final output matches your description

---

**Estimated time**: 15 minutes setup + 3 minutes per scene
**Difficulty**: Beginner-friendly with detailed guides
**Status**: Production-ready ✅

Happy 3D scene generating! 🎨🚀
