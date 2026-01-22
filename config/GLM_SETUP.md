# GLM-4.5V Vision Configuration Guide

## Overview

This project uses **Z.AI's GLM-4.5V** multimodal vision model for evaluating Blender 3D scene screenshots.

**GLM-4.5V Specs**:
- **106B parameters** (12B active via Mixture-of-Experts)
- **64K token context** window
- **SOTA performance** on vision benchmarks (August 2025)
- **Deep reasoning mode** for sophisticated analysis
- **Spatial understanding** perfect for 3D scene evaluation

## API Configuration

### Endpoint

**Vision Analysis Endpoint** (for screenshot evaluation):
```
https://api.z.ai/api/paas/v4/chat/completions
```

**Authorization**:
```
Header: Authorization: Bearer YOUR_API_KEY
```

### Environment Variables

Set your Z.AI API key:

```bash
# Option 1: PowerShell
setx ZAI_API_KEY "your-api-key-here"

# Option 2: Bash
export ZAI_API_KEY="your-api-key-here"

# Option 3: .env file
echo "ZAI_API_KEY=your-api-key-here" > .env
```

### API Key

Get your API key from: https://platform.z.ai/

Your key is stored securely in your Obsidian vault:
- **Location**: `E:/Obsidian Vault/LLM/API Key Repository.md`
- **Active Key**: `2c21c2eed1fa44e7834a6113aeb832a5.i0i3LQY4p00w19xe`

### Models Available

**Vision Analysis** (recommended for Blender evaluation):
- `glm-4.5v` - Latest multimodal vision model with deep reasoning
- `glm-4v-plus` - Alternative vision model

**Text/Coding** (for comparison):
- `glm-4.6` - Latest text generation model
- `glm-4-air` - Efficient text model

## Testing the Connection

### Quick Test with Python

```python
import asyncio
from colossus_blender.glm_vision import GLMVisionClient

async def test():
    client = GLMVisionClient()
    result = await client.analyze_scene(
        screenshot_base64="your-base64-image-here",
        user_intent="Test scene",
        iteration=0
    )
    print(f"Score: {result['overall_score']:.1%}")

asyncio.run(test())
```

### Test with curl

```bash
curl -X POST https://api.z.ai/api/paas/v4/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "model": "glm-4.5v",
    "messages": [{
      "role": "user",
      "content": [{
        "type": "text",
        "text": "Describe this image"
      }, {
        "type": "image_url",
        "image_url": {
          "url": "data:image/png;base64,iVBORw0KG..."
        }
      }]
    }]
  }'
```

## Integration with Colossus

The Evaluator Agent automatically uses GLM-4.5V:

```python
from colossus_blender import (
    ColossusD5Orchestrator,
    WorkflowState
)
from colossus_blender.glm_vision import GLMVisionClient

# Initialize
glm_vision = GLMVisionClient()
orchestrator = ColossusD5Orchestrator(
    claude_llm=your_claude_client,
    vision_llm=glm_vision,  # Uses GLM-4.5V
    blender_mcp_client=blender_client,
    system_prompt=system_prompt
)

# Run workflow
state = WorkflowState(user_intent="...")
final_state = await orchestrator.run(state)
```

## Features

### Vision Analysis

GLM-4.5V analyzes Blender screenshots for:

1. **Composition** (0-10)
   - Object placement and arrangement
   - Scene balance and visual flow
   - Adherence to design principles

2. **Lighting** (0-10)
   - Light quality and intensity
   - Shadow realism
   - Mood and atmosphere

3. **Materials** (0-10)
   - Material realism
   - Color accuracy
   - Texture mapping quality

4. **Camera** (0-10)
   - Framing and angle
   - Field of view
   - Focus and composition

5. **Goal Match** (0-10)
   - Alignment with user intent
   - Element completeness
   - Style accuracy

### Deep Reasoning

When enabled, GLM-4.5V uses "thinking mode" for:
- Step-by-step scene analysis
- Spatial relationship understanding
- Detailed improvement suggestions
- Context-aware feedback

## Pricing

**GLM-4.5V Vision API Pricing**:
- **Input**: ~0.5 CNY per 1M tokens
- **Output**: ~1.0 CNY per 1M tokens
- **Typical cost**: ~0.01-0.02 USD per screenshot evaluation

**For reference**:
- 3 iterations per scene × 100 scenes = ~$0.30-0.60/day
- Highly cost-effective compared to alternatives

## Comparison with Alternatives

| Feature | GLM-4.5V | Claude 3.5 Sonnet | Gemini 2.5 Pro |
|---------|----------|------------------|----------------|
| Vision Quality | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Cost | 💰 Lowest | 💰💰 Medium | 💰💰 Medium |
| Reasoning | Deep | Good | Excellent |
| Context Window | 64K | 200K | 1M |
| Chinese Support | Excellent | Good | Good |
| Speed | Fast | Fast | Fast |
| 3D Understanding | Excellent | Excellent | Good |

## Troubleshooting

### Issue: "1113 Insufficient balance"
**Solution**: Add credits to your Z.AI account at https://platform.z.ai/

### Issue: "401 Unauthorized"
**Solution**: Check API key is correct
```bash
echo "ZAI_API_KEY=${ZAI_API_KEY:0:10}..."
```

### Issue: "Model not found"
**Solution**: Use correct model name `glm-4.5v` (lowercase)

### Issue: "Image too large"
**Solution**: Resize to < 1024x1024 pixels (automatically done by Blender MCP)

## Documentation

- **Official API Docs**: https://docs.z.ai/guides/vlm/glm-4-5v
- **GitHub**: https://github.com/zai-org/GLM-V
- **HuggingFace**: https://huggingface.co/zai-org/GLM-4.5V
- **Research Paper**: https://arxiv.org/abs/2507.01006

## API Reference

### /chat/completions

**Endpoint**: `POST https://api.z.ai/api/paas/v4/chat/completions`

**Request**:
```json
{
  "model": "glm-4.5v",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Your prompt here"
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "data:image/png;base64,..."
          }
        }
      ]
    }
  ],
  "temperature": 0.7,
  "max_tokens": 2048,
  "reasoning": {
    "enabled": true
  }
}
```

**Response**:
```json
{
  "id": "chatcmpl-xxx",
  "model": "glm-4.5v",
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "Response text here"
      }
    }
  ],
  "usage": {
    "prompt_tokens": 123,
    "completion_tokens": 45
  }
}
```

## Next Steps

1. **Set API Key**: `setx ZAI_API_KEY "your-key"`
2. **Test Connection**: `python test_glm_vision.ps1` (PowerShell)
3. **Run Examples**: `cd examples && python basic_usage.py`
4. **Monitor Costs**: Check Z.AI dashboard for usage

---

**Status**: ✅ Tested and Verified
**Last Updated**: November 2025
**GLM-4.5V Endpoint**: Confirmed Working
