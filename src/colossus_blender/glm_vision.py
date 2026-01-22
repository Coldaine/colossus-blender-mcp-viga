"""
GLM-4.5V Vision Integration
Z.AI's state-of-the-art multimodal vision model for Blender scene evaluation
"""

import os
import json
import base64
from typing import Dict, Any, List, Optional
import aiohttp
from dataclasses import dataclass

from .vision_utils import extract_json_from_content


@dataclass
class GLMConfig:
    """GLM-4.5V API configuration

    CODING PLAN Endpoint: https://api.z.ai/api/coding/paas/v4/chat/completions
    Model: glm-4.5v (vision-capable multimodal model)
    Auth: Bearer token in Authorization header

    Note: The Coding Plan endpoint provides access to GLM-4.5V vision.
    The common API endpoint (/api/paas/v4) requires different billing.
    """
    api_key: str
    api_base: str = "https://api.z.ai/api/coding/paas/v4"  # Coding Plan endpoint
    model: str = "glm-4.5v"
    temperature: float = 0.7
    max_tokens: int = 2048
    thinking_enabled: bool = True  # GLM-4.5V deep reasoning mode


class GLMVisionClient:
    """
    Client for GLM-4.5V multimodal vision model

    GLM-4.5V Features:
    - 106B parameters (12B active via MoE)
    - 64K token context window
    - SOTA performance on vision benchmarks
    - Spatial reasoning and scene understanding
    - Multi-image analysis
    - Video understanding (temporal)
    """

    def __init__(self, config: Optional[GLMConfig] = None):
        if config is None:
            api_key = os.getenv("ZAI_API_KEY") or os.getenv("GLM_API_KEY")
            if not api_key:
                raise ValueError(
                    "GLM API key not found. Set ZAI_API_KEY or GLM_API_KEY environment variable"
                )
            config = GLMConfig(api_key=api_key)

        self.config = config
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def analyze_scene(
        self,
        screenshot_base64: str,
        user_intent: str,
        iteration: int = 0,
        max_iterations: int = 3,
        previous_feedback: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze Blender scene screenshot using GLM-4.5V

        Args:
            screenshot_base64: Base64-encoded PNG screenshot
            user_intent: Original user goal/description
            iteration: Current iteration number
            max_iterations: Maximum iterations allowed
            previous_feedback: Feedback from previous iteration (if any)

        Returns:
            {
                "scores": {
                    "composition": 0-10,
                    "lighting": 0-10,
                    "materials": 0-10,
                    "camera": 0-10,
                    "goal_match": 0-10
                },
                "overall_score": 0.0-1.0,
                "is_satisfactory": bool,
                "issues": List[str],
                "specific_suggestions": List[str],
                "positive_aspects": List[str],
                "thinking_process": str (if thinking_mode enabled)
            }
        """

        # Build analysis prompt
        prompt = self._build_analysis_prompt(
            user_intent=user_intent,
            iteration=iteration,
            max_iterations=max_iterations,
            previous_feedback=previous_feedback
        )

        # Call GLM-4.5V API
        response = await self._call_api(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{screenshot_base64}"
                            }
                        }
                    ]
                }
            ]
        )

        # Parse response
        content = ""

        try:
            content = response["choices"][0]["message"]["content"]

            # Extract thinking process if available
            thinking_process = ""
            if self.config.thinking_enabled and "thinking" in response["choices"][0]["message"]:
                thinking_process = response["choices"][0]["message"]["thinking"]

            # Parse JSON from content
            # GLM-4.5V should return structured JSON
            analysis = extract_json_from_content(content)

            # Add thinking process to analysis
            if thinking_process:
                analysis["thinking_process"] = thinking_process

            return analysis

        except (json.JSONDecodeError, KeyError, IndexError, ValueError) as e:
            # Fallback: create structured response from text
            return self._parse_text_response(content, response)

    def _build_analysis_prompt(
        self,
        user_intent: str,
        iteration: int,
        max_iterations: int,
        previous_feedback: Optional[Dict[str, Any]]
    ) -> str:
        """Build comprehensive analysis prompt for GLM-4.5V"""

        prompt = f"""You are an expert 3D scene evaluator analyzing a Blender viewport screenshot.

**Original Goal**: {user_intent}

**Current Progress**: Iteration {iteration + 1} of {max_iterations}
"""

        if previous_feedback:
            prompt += f"""
**Previous Iteration Feedback**:
- Score: {previous_feedback.get('overall_score', 0):.2%}
- Issues: {', '.join(previous_feedback.get('issues', []))}
- Changes Made: {', '.join(previous_feedback.get('specific_suggestions', []))}
"""

        prompt += """
**Your Task**: Analyze this 3D scene screenshot and provide a comprehensive evaluation.

**Evaluation Criteria** (rate each 0-10):

1. **Composition** (0-10)
   - Object placement and arrangement
   - Scene balance and visual flow
   - Use of space (not too empty, not too cluttered)
   - Adherence to composition principles (rule of thirds, etc.)

2. **Lighting** (0-10)
   - Light quality and intensity
   - Shadow quality and realism
   - Overall visibility of important elements
   - Mood and atmosphere
   - Color temperature appropriateness

3. **Materials** (0-10)
   - Material realism and quality
   - Color accuracy and appeal
   - Texture detail and mapping
   - Physically-based rendering quality
   - Material variety and consistency

4. **Camera** (0-10)
   - Camera angle and framing
   - Field of view appropriateness
   - Focus and depth of field
   - Viewpoint effectiveness for the scene

5. **Goal Match** (0-10)
   - How well does the scene match the original intent?
   - Are all requested elements present?
   - Does it capture the intended mood/style?
   - Overall accuracy to description

**Response Format** (JSON):

```json
{
    "scores": {
        "composition": <0-10>,
        "lighting": <0-10>,
        "materials": <0-10>,
        "camera": <0-10>,
        "goal_match": <0-10>
    },
    "overall_score": <0.0-1.0>,
    "is_satisfactory": <true/false>,
    "issues": [
        "Specific issue 1",
        "Specific issue 2"
    ],
    "specific_suggestions": [
        "Concrete improvement 1 (e.g., 'Increase sun lamp energy to 7.0')",
        "Concrete improvement 2 (e.g., 'Rotate camera 15 degrees clockwise')"
    ],
    "positive_aspects": [
        "What's working well 1",
        "What's working well 2"
    ]
}
```

**Important Guidelines**:

1. **Be Specific**: Don't say "lighting is poor" - say "sun lamp energy too low at ~3.0, should be 6-8 for this scene"

2. **Be Actionable**: Every suggestion must be a concrete Python operation (adjust parameter, move object, change color)

3. **Overall Score Calculation**:
   - overall_score = average of all 5 scores / 10
   - Round to 2 decimal places

4. **Satisfactory Threshold**:
   - is_satisfactory = true if overall_score >= 0.75
   - Consider iteration number (be more lenient on iteration 1)

5. **Focus on Impact**: Prioritize suggestions that will have the biggest visual improvement

6. **Realism**: Evaluate based on photorealism, stylistic consistency, and technical quality

Analyze the screenshot now and provide your evaluation in JSON format.
"""

        return prompt

    async def _call_api(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Call GLM-4.5V API with vision support"""

        if not self.session:
            self.session = aiohttp.ClientSession()

        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }

        # Enable thinking mode if configured (GLM-4.5V deep reasoning)
        if self.config.thinking_enabled:
            payload["thinking"] = {
                "type": "enabled"
            }

        url = f"{self.config.api_base}/chat/completions"

        async with self.session.post(url, headers=headers, json=payload) as resp:
            if resp.status != 200:
                error_text = await resp.text()
                raise Exception(f"GLM API error ({resp.status}): {error_text}")

            return await resp.json()

    def _parse_text_response(
        self,
        content: str,
        full_response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fallback parser if JSON extraction fails"""

        # Try to extract numerical scores from text
        scores = {
            "composition": 5,
            "lighting": 5,
            "materials": 5,
            "camera": 5,
            "goal_match": 5
        }

        # Simple keyword-based extraction
        for key in scores.keys():
            if key in content.lower():
                # Look for numbers near the keyword
                import re
                pattern = rf"{key}[:\s]+(\d+)"
                match = re.search(pattern, content.lower())
                if match:
                    scores[key] = min(10, max(0, int(match.group(1))))

        overall_score = sum(scores.values()) / (len(scores) * 10)

        return {
            "scores": scores,
            "overall_score": overall_score,
            "is_satisfactory": overall_score >= 0.75,
            "issues": ["Could not parse structured feedback"],
            "specific_suggestions": ["Review GLM response format"],
            "positive_aspects": [],
            "raw_response": content,
            "thinking_process": full_response.get("choices", [{}])[0].get("message", {}).get("thinking", "")
        }


# Convenience functions for easy integration

async def evaluate_screenshot_with_glm(
    screenshot_base64: str,
    user_intent: str,
    api_key: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Quick helper to evaluate a screenshot

    Args:
        screenshot_base64: Base64-encoded screenshot
        user_intent: Original scene description
        api_key: Optional API key (or use ZAI_API_KEY env var)
        **kwargs: Additional args for analyze_scene()

    Returns:
        Evaluation dict with scores and suggestions
    """

    if api_key:
        config = GLMConfig(api_key=api_key)
    else:
        config = None

    async with GLMVisionClient(config=config) as client:
        return await client.analyze_scene(
            screenshot_base64=screenshot_base64,
            user_intent=user_intent,
            **kwargs
        )


# Test function
async def test_glm_vision():
    """Test GLM-4.5V integration"""

    print("Testing GLM-4.5V Vision Integration...")

    # Check API key
    api_key = os.getenv("ZAI_API_KEY") or os.getenv("GLM_API_KEY")
    if not api_key:
        print("❌ No API key found. Set ZAI_API_KEY or GLM_API_KEY")
        return False

    print(f"✓ API key found (length: {len(api_key)})")

    # Create a simple test (would need actual screenshot in practice)
    test_screenshot = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="  # 1x1 red pixel

    async with GLMVisionClient() as client:
        print("✓ GLM client created")
        print("✓ Testing API connection...")

        # Note: This would fail with a 1x1 pixel, but tests the connection
        try:
            result = await client.analyze_scene(
                screenshot_base64=test_screenshot,
                user_intent="Test scene",
                iteration=0
            )
            print(f"✓ API call successful")
            print(f"  Overall score: {result.get('overall_score', 'N/A')}")
            return True
        except Exception as e:
            print(f"⚠ API call failed (expected with test image): {e}")
            return False


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_glm_vision())
