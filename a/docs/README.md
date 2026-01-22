# Colossus Blender MCP Integration

**Multi-agent vision-based 3D scene creation with Blender via Model Context Protocol (MCP)**

This project implements the ColossusD5 multi-agent orchestration system for creating high-quality 3D scenes in Blender with iterative vision-based feedback loops.

## Architecture

```
User Intent → Planner → Designer → Executor → Evaluator → Refiner
                                      ↓            ↓
                                  Screenshot   Quality Score
                                                   ↓
                                            Loop or Exit
```

### 5 Specialized Agents

1. **Planner**: Decomposes user intent into executable subtasks
2. **Designer**: Generates GPU-optimized Blender Python code
3. **Executor**: Runs code via Blender MCP with error handling
4. **Evaluator**: Analyzes viewport screenshots using vision LLM
5. **Refiner**: Generates targeted improvements based on feedback

## Features

- ✅ **Vision Feedback Loop**: Iterative refinement based on visual analysis
- ✅ **GPU Optimization**: Pre-configured settings for RTX 3090 and 5090
- ✅ **Multi-Agent System**: Research Agent D5 decomposition pattern
- ✅ **Quality Thresholding**: Automatic termination when goals met
- ✅ **Error Handling**: Robust execution with fallback strategies
- ✅ **Production Ready**: Complete system with examples and documentation

## Requirements

### Software
- **Blender 4.4+** (installed at: `C:\Program Files\Blender Foundation\Blender 4.4`)
- **Python 3.10+**
- **UV package manager**
- **NVIDIA GPU** (RTX 3090 or 5090 recommended)

### API Keys
- `ANTHROPIC_API_KEY` - For Claude 3.5 Sonnet (code generation)
- `GOOGLE_API_KEY` - For Gemini 2.5 Pro (vision evaluation)

## Installation

### 1. Install UV Package Manager

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Add to PATH:
```powershell
set Path=C:\Users\[username]\.local\bin;%Path%
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Install Blender MCP Addon

Download the addon:
```bash
cd colossus_blender_mcp/config
curl -o addon.py https://raw.githubusercontent.com/ahujasid/blender-mcp/main/addon.py
```

Install in Blender:
1. Open Blender 4.4
2. Edit > Preferences > Add-ons > Install
3. Select `addon.py`
4. Enable "Interface: Blender MCP" checkbox

The addon will start a TCP server on `localhost:9876`.

### 4. Configure Claude Desktop MCP

Edit Claude Desktop config (`%APPDATA%\Claude\claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "blender": {
      "command": "uvx",
      "args": ["blender-mcp"]
    }
  }
}
```

Restart Claude Desktop.

## Usage

### Basic Example

```python
import asyncio
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from colossus_blender import ColossusD5Orchestrator, WorkflowState, create_blender_client

async def main():
    # Initialize LLMs
    claude = ChatAnthropic(model="claude-3-5-sonnet-20241022")
    gemini = ChatGoogleGenerativeAI(model="gemini-2.5-pro")

    # Connect to Blender
    blender = await create_blender_client(mode="socket", host="localhost", port=9876)

    # Load system prompt
    with open("prompts/blender_mcp_system_prompt.md", "r") as f:
        system_prompt = f.read()

    # Create orchestrator
    orchestrator = ColossusD5Orchestrator(
        claude_llm=claude,
        vision_llm=gemini,
        blender_mcp_client=blender,
        system_prompt=system_prompt,
        gpu_mode="3090"
    )

    # Define scene
    state = WorkflowState(
        user_intent="Create a cyberpunk street scene with neon lights and rain",
        max_iterations=3,
        satisfaction_threshold=0.75
    )

    # Run workflow
    final_state = await orchestrator.run(state)

    print(f"Quality: {final_state.quality_score:.1%}")
    print(f"Satisfied: {final_state.is_satisfied}")

    await blender.disconnect()

asyncio.run(main())
```

### Run Examples

```bash
# Basic usage
cd examples
python basic_usage.py

# Advanced workflows
python advanced_workflow.py multi      # Create multiple scenes
python advanced_workflow.py benchmark  # GPU benchmark
python advanced_workflow.py refine     # Iterative refinement demo
```

## GPU Configuration

### RTX 3090 (24GB VRAM)
- Preview: 64 samples, 256 tile size
- Production: 128 samples, 256 tile size
- Final: 256 samples, 256 tile size

### RTX 5090 (32GB VRAM)
- Preview: 128 samples, 512 tile size
- Production: 256 samples, 512 tile size
- Final: 512 samples, 512 tile size

Change GPU mode:
```python
orchestrator = ColossusD5Orchestrator(
    # ...
    gpu_mode="5090"  # or "3090"
)
```

## Project Structure

```
colossus_blender_mcp/
├── src/
│   └── colossus_blender/
│       ├── __init__.py
│       ├── orchestrator.py      # D5 multi-agent system
│       ├── mcp_client.py         # Blender MCP communication
│       └── gpu_config.py         # GPU optimization settings
├── examples/
│   ├── basic_usage.py
│   └── advanced_workflow.py
├── prompts/
│   └── blender_mcp_system_prompt.md  # Expert Blender coding prompt
├── config/
│   ├── addon.py                  # Blender MCP addon (download)
│   └── claude_desktop_config.json
├── requirements.txt
└── README.md
```

## How It Works

### Iteration Loop

1. **Planning Phase** (once at start):
   - Planner decomposes user intent into subtasks
   - Creates dependency graph

2. **Design Phase**:
   - Designer generates Blender Python code
   - Optimizes for target GPU (3090/5090)
   - Includes error handling and metadata

3. **Execution Phase**:
   - Executor runs code in Blender via MCP
   - Captures viewport screenshot (1024px)

4. **Evaluation Phase**:
   - Vision LLM analyzes screenshot
   - Scores quality on 0-1 scale
   - Identifies specific issues

5. **Refinement Phase**:
   - If quality < threshold, Refiner generates improvements
   - Returns to Design phase with feedback
   - Loop continues until satisfied or max iterations

### Quality Scoring

Vision evaluation criteria:
- **Composition** (0-10): Object placement, scene balance
- **Lighting** (0-10): Quality, shadows, visibility
- **Materials** (0-10): Realism, color, texture
- **Camera** (0-10): Angle, framing, focus
- **Goal Match** (0-10): Alignment with user intent

Overall score = average of all criteria / 10

## Troubleshooting

### Blender Connection Failed
- Ensure Blender is running
- Check MCP addon is enabled (should see "MCP Server Started" in Blender console)
- Verify port 9876 is not in use

### Vision Evaluation Errors
- Check `GOOGLE_API_KEY` is set correctly
- Ensure Gemini 2.5 Pro API access is enabled
- Verify screenshot is being captured (check execution logs)

### Code Generation Issues
- Check `ANTHROPIC_API_KEY` is valid
- Review system prompt is loaded correctly
- Increase timeout if code is complex

### GPU Not Detected
- Verify NVIDIA drivers are up to date
- Check Cycles compute device in Blender Preferences
- Ensure CUDA/OptiX is available

## Performance Tips

1. **Start with preview quality** for fast iteration
2. **Use lower satisfaction thresholds** (0.70-0.75) for faster workflows
3. **Limit max iterations** to 3-5 (diminishing returns beyond that)
4. **Clear scene between runs** to prevent memory buildup
5. **Monitor VRAM usage** in Task Manager (stay under 20GB for 3090)

## Research Background

Based on:
- **BlenderAlchemy** (ECCV 2024): Vision-based edit generation
- **Research Agent D5**: Multi-agent decomposition pattern
- **Blender MCP** (ahujasid): Model Context Protocol integration
- **Gemini 2.5 Pro**: Native multimodal reasoning with 1M token context

## Contributing

This is a research/experimental project. Feel free to:
- Report issues
- Suggest improvements
- Share results
- Fork and extend

## License

MIT License - See LICENSE file for details

## Acknowledgments

- **Blender Foundation** - Blender 3D software
- **Anthropic** - Claude LLM and MCP protocol
- **Google** - Gemini vision models
- **ahujasid** - Blender MCP server implementation
- **BlenderAlchemy team** - Vision feedback loop research

---

**Status**: Experimental | **Version**: 0.1.0 | **Last Updated**: November 2025
