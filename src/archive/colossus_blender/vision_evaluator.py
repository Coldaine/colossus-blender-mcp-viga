"""
Vision Evaluator for Battleship Model Comparison
Uses local Qwen2.5-VL-72B for image comparison and geometric analysis

This replaces GLM-4.5V with a specialized local vision model optimized for:
- Multi-image comparison (blueprint + render + reference photos)
- Quantitative geometric feedback
- Unlimited refinement iterations (no API costs)
- Domain-specific battleship evaluation
"""

import os
import json
import base64
import cv2
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import aiohttp

from .vision_utils import (
    extract_json_from_content,
    normalize_vision_endpoint,
    is_model_available,
    list_available_models
)


@dataclass
class VisionModelConfig:
    """Local Qwen2.5-VL-72B configuration

    Deployment options:
    - SGLang (recommended): Fast inference, multi-image support
    - vLLM (alternative): Broader compatibility

    Hardware requirements:
    - 128GB unified memory (AMD Ryzen AI MAX+ 395)
    - INT4 quantization: ~14-18GB VRAM
    - Expected inference time: 2-5 minutes per comparison
    """
    endpoint: str = "http://localhost:8000/v1"
    model_name: str = "Qwen2.5-VL-72B-Instruct"
    temperature: float = 0.3  # Lower for more deterministic geometric analysis
    max_tokens: int = 4096
    timeout: int = 300  # 5 minutes for complex comparisons
    validate_model_on_start: bool = True

    def __post_init__(self):
        self.endpoint = normalize_vision_endpoint(self.endpoint)


class ComparisonVisionClient:
    """
    Local vision model client for battleship model comparison

    Key features:
    - Multi-image reasoning (blueprint + render simultaneously)
    - Quantitative discrepancy detection
    - Actionable refinement suggestions
    - Hybrid VLM + OpenCV measurements
    """

    def __init__(self, config: Optional[VisionModelConfig] = None):
        if config is None:
            endpoint = os.getenv("VISION_MODEL_ENDPOINT", "http://localhost:8000/v1")
            config = VisionModelConfig(endpoint=endpoint)

        self.config = config
        self.session = None
        self._model_checked = False

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def compare_to_reference(
        self,
        rendered_base64: str,
        reference_images: List[Dict[str, str]],
        user_intent: str,
        iteration: int = 0,
        max_iterations: int = 3,
        previous_feedback: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Compare rendered 3D model against reference blueprints/photos

        Args:
            rendered_base64: Base64-encoded render of current 3D model
            reference_images: List of {"type": "blueprint_top|blueprint_side|photo", "data": base64}
            user_intent: Original modeling goal
            iteration: Current refinement iteration
            max_iterations: Maximum iterations allowed
            previous_feedback: Feedback from previous iteration

        Returns:
            {
                "overall_score": 0.0-1.0,
                "is_satisfactory": bool,
                "discrepancies": [
                    {
                        "component": "Main Turret 2",
                        "type": "position|proportion|alignment|shape",
                        "severity": "critical|moderate|minor",
                        "quantitative": "12% too far forward",
                        "suggestion": "Move turret 15 meters aft"
                    }
                ],
                "measurements": {
                    "length_accuracy": 0.95,
                    "beam_accuracy": 0.92,
                    "proportions_match": 0.88
                },
                "positive_aspects": List[str],
                "hybrid_analysis": {
                    "vlm_insights": str,
                    "opencv_measurements": Dict
                }
            }
        """

        # Build comparison prompt
        prompt = self._build_comparison_prompt(
            user_intent=user_intent,
            reference_count=len(reference_images),
            iteration=iteration,
            max_iterations=max_iterations,
            previous_feedback=previous_feedback
        )

        # Prepare multi-image input
        content_parts = [{"type": "text", "text": prompt}]

        # Add reference images first
        for idx, ref_img in enumerate(reference_images):
            img_type = ref_img.get("type", "unknown")
            content_parts.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{ref_img['data']}",
                    "detail": "high"
                }
            })
            content_parts.append({
                "type": "text",
                "text": f"[Reference Image {idx+1}: {img_type}]"
            })

        # Add rendered model last
        content_parts.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{rendered_base64}",
                "detail": "high"
            }
        })
        content_parts.append({
            "type": "text",
            "text": "[Rendered 3D Model - Current State]"
        })

        # Call local vision model
        response = await self._call_vision_api(content_parts)

        # Parse structured response
        try:
            content = response["choices"][0]["message"]["content"]
            analysis = extract_json_from_content(content)

            # Optionally run hybrid analysis (VLM + OpenCV)
            if reference_images:
                opencv_measurements = await self._hybrid_measurement_analysis(
                    rendered_base64=rendered_base64,
                    reference_base64=reference_images[0]['data']  # Use first reference
                )
                analysis["hybrid_analysis"] = {
                    "vlm_insights": content,
                    "opencv_measurements": opencv_measurements
                }

            return analysis

        except (json.JSONDecodeError, KeyError, IndexError, ValueError) as e:
            # Fallback
            return self._create_fallback_response(str(e))

    async def analyze_scene(
        self,
        screenshot_base64: str,
        user_intent: str,
        iteration: int = 0,
        max_iterations: int = 3,
        previous_feedback: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        General scene analysis (compatibility mode with original GLM interface)

        This method maintains compatibility with existing Colossus code
        while using the local vision model.
        """

        # Build general evaluation prompt
        prompt = f"""You are an expert 3D scene evaluator analyzing a Blender viewport screenshot.

**Original Goal**: {user_intent}

**Current Progress**: Iteration {iteration + 1} of {max_iterations}

"""

        if previous_feedback:
            prompt += f"""**Previous Iteration Feedback**:
- Score: {previous_feedback.get('overall_score', 0):.2%}
- Issues: {', '.join(previous_feedback.get('issues', []))}
"""

        prompt += """
**Your Task**: Analyze this 3D scene and provide evaluation scores.

**Evaluation Criteria** (rate each 0-10):
1. **Composition**: Object placement, scene balance
2. **Lighting**: Quality, shadows, visibility
3. **Materials**: Realism, color, texture
4. **Camera**: Angle, framing, focus
5. **Goal Match**: Alignment with user intent

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
    "issues": ["issue 1", "issue 2"],
    "specific_suggestions": ["suggestion 1", "suggestion 2"],
    "positive_aspects": ["positive 1", "positive 2"]
}
```

Calculate overall_score as: (sum of all scores) / (5 * 10)
Set is_satisfactory = true if overall_score >= 0.75

Provide specific, actionable suggestions with parameter values.
"""

        content_parts = [
            {"type": "text", "text": prompt},
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{screenshot_base64}",
                    "detail": "high"
                }
            }
        ]

        response = await self._call_vision_api(content_parts)

        try:
            content = response["choices"][0]["message"]["content"]
            analysis = extract_json_from_content(content)
            return analysis

        except (json.JSONDecodeError, KeyError, IndexError, ValueError) as e:
            return self._create_fallback_response(str(e))

    def _build_comparison_prompt(
        self,
        user_intent: str,
        reference_count: int,
        iteration: int,
        max_iterations: int,
        previous_feedback: Optional[Dict[str, Any]]
    ) -> str:
        """Build specialized prompt for battleship comparison"""

        prompt = f"""You are analyzing a 3D battleship model for geometric accuracy against reference materials.

**Modeling Goal**: {user_intent}

**Progress**: Iteration {iteration + 1} of {max_iterations}

**Reference Materials Provided**: {reference_count} image(s)
- Blueprint views (top, side, etc.)
- Historical photographs (if available)

"""

        if previous_feedback:
            prompt += f"""**Previous Iteration**:
- Score: {previous_feedback.get('overall_score', 0):.2%}
- Discrepancies found: {len(previous_feedback.get('discrepancies', []))}
- Changes attempted: {', '.join([d['suggestion'] for d in previous_feedback.get('discrepancies', [])][:3])}

"""

        prompt += """**Your Task**: Identify specific geometric discrepancies between the reference materials and the rendered 3D model.

**Focus Areas**:
1. **Turret Positions & Spacing**
   - Fore/aft placement along deck
   - Lateral alignment (centerline vs offset)
   - Vertical positioning (deck level, superstructure)
   - Spacing between multiple turrets

2. **Hull Proportions**
   - Length-to-beam ratio
   - Draft (depth below waterline)
   - Bow rake angle
   - Stern configuration
   - Freeboard (height above waterline)

3. **Superstructure**
   - Bridge height and position
   - Funnel placement and dimensions
   - Mast locations
   - Deck levels

4. **Detail Elements**
   - Secondary armament placement
   - Anchor positions
   - Deck features (hatches, boats)

**Response Format** (JSON):
```json
{
    "overall_score": <0.0-1.0>,
    "is_satisfactory": <true/false>,
    "discrepancies": [
        {
            "component": "Main Turret 2",
            "type": "position",
            "severity": "critical",
            "quantitative": "Positioned 12% too far forward relative to blueprint station markers",
            "suggestion": "Move turret aft by approximately 15 meters (0.8 turret diameters)"
        },
        {
            "component": "Hull beam",
            "type": "proportion",
            "severity": "moderate",
            "quantitative": "Beam appears 8% narrower than blueprint specifications",
            "suggestion": "Scale hull width by factor of 1.08"
        }
    ],
    "measurements": {
        "length_accuracy": <0.0-1.0>,
        "beam_accuracy": <0.0-1.0>,
        "proportions_match": <0.0-1.0>
    },
    "positive_aspects": [
        "Bow rake angle matches reference photos accurately",
        "Turret spacing is proportionally correct"
    ]
}
```

**Severity Levels**:
- **critical**: Immediately obvious discrepancy, breaks silhouette
- **moderate**: Noticeable upon closer inspection
- **minor**: Subtle detail that only experts would notice

**Quantitative Requirements**:
- Use percentages for proportion errors (e.g., "8% too narrow")
- Use relative distances for positioning (e.g., "0.5 turret diameters forward")
- Compare to blueprint station markers when visible

**Scoring**:
- overall_score = (length_accuracy + beam_accuracy + proportions_match) / 3
- is_satisfactory = true if overall_score >= 0.85 (stricter for battleships)

Analyze the images now and identify all discrepancies.
"""

        return prompt

    async def _call_vision_api(self, content_parts: List[Dict]) -> Dict[str, Any]:
        """Call local Qwen2.5-VL API (OpenAI-compatible endpoint)"""

        if not self.session:
            self.session = aiohttp.ClientSession()

        if self.config.validate_model_on_start and not self._model_checked:
            await self._ensure_model_loaded()

        headers = {
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.config.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": content_parts
                }
            ],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens
        }

        url = f"{self.config.endpoint}/chat/completions"

        timeout = aiohttp.ClientTimeout(total=self.config.timeout)

        async with self.session.post(url, headers=headers, json=payload, timeout=timeout) as resp:
            if resp.status != 200:
                error_text = await resp.text()
                raise Exception(f"Vision model API error ({resp.status}): {error_text}")

            return await resp.json()

    async def _ensure_model_loaded(self) -> None:
        """Verify the target model is available on the server (best-effort)."""
        if not self.session:
            self.session = aiohttp.ClientSession()

        url = f"{self.config.endpoint}/models"
        timeout = aiohttp.ClientTimeout(total=min(30, self.config.timeout))

        try:
            async with self.session.get(url, timeout=timeout) as resp:
                if resp.status in (404, 405):
                    # /models not supported, skip strict validation
                    self._model_checked = True
                    return
                if resp.status != 200:
                    error_text = await resp.text()
                    raise Exception(f"Model list check failed ({resp.status}): {error_text}")

                models_payload = await resp.json()
        except Exception as e:
            raise Exception(
                "Vision model validation failed. "
                "Ensure the server is running and reachable, then retry. "
                f"Details: {e}"
            )

        if not is_model_available(self.config.model_name, models_payload):
            available = list_available_models(models_payload)
            available_text = ", ".join(available) if available else "<none>"
            raise Exception(
                "Vision model not loaded. "
                f"Requested: {self.config.model_name}. "
                f"Available: {available_text}. "
                "If using SGLang/vLLM, download a quantized model (e.g., GPTQ) "
                "and launch with the matching model name."
            )

        self._model_checked = True

    async def _hybrid_measurement_analysis(
        self,
        rendered_base64: str,
        reference_base64: str
    ) -> Dict[str, Any]:
        """
        Hybrid analysis using OpenCV for quantitative measurements

        Complements VLM analysis with precise measurements:
        - Contour matching
        - Aspect ratio comparison
        - Feature point alignment
        """

        try:
            # Decode images
            rendered_img = self._base64_to_image(rendered_base64)
            reference_img = self._base64_to_image(reference_base64)

            # Resize to same dimensions for comparison
            target_size = (1024, 1024)
            rendered_resized = cv2.resize(rendered_img, target_size)
            reference_resized = cv2.resize(reference_img, target_size)

            # Convert to grayscale
            rendered_gray = cv2.cvtColor(rendered_resized, cv2.COLOR_BGR2GRAY)
            reference_gray = cv2.cvtColor(reference_resized, cv2.COLOR_BGR2GRAY)

            # Edge detection
            rendered_edges = cv2.Canny(rendered_gray, 50, 150)
            reference_edges = cv2.Canny(reference_gray, 50, 150)

            # Contour analysis
            rendered_contours, _ = cv2.findContours(rendered_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            reference_contours, _ = cv2.findContours(reference_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Get bounding boxes of largest contours
            if rendered_contours and reference_contours:
                rendered_hull = max(rendered_contours, key=cv2.contourArea)
                reference_hull = max(reference_contours, key=cv2.contourArea)

                rx, ry, rw, rh = cv2.boundingRect(rendered_hull)
                fx, fy, fw, fh = cv2.boundingRect(reference_hull)

                # Calculate aspect ratios
                rendered_aspect = rw / rh if rh > 0 else 0
                reference_aspect = fw / fh if fh > 0 else 0

                aspect_match = 1.0 - abs(rendered_aspect - reference_aspect) / reference_aspect if reference_aspect > 0 else 0

                # Structural similarity (simple version)
                # This is a placeholder - could use SSIM for better results

                return {
                    "aspect_ratio_match": float(aspect_match),
                    "rendered_aspect_ratio": float(rendered_aspect),
                    "reference_aspect_ratio": float(reference_aspect),
                    "contour_complexity_match": min(len(rendered_hull), len(reference_hull)) / max(len(rendered_hull), len(reference_hull)),
                    "method": "opencv_contour_analysis"
                }
            else:
                return {
                    "error": "Could not detect contours in images",
                    "method": "opencv_contour_analysis"
                }

        except Exception as e:
            return {
                "error": f"Hybrid analysis failed: {str(e)}",
                "method": "opencv_contour_analysis"
            }

    def _base64_to_image(self, base64_str: str) -> np.ndarray:
        """Convert base64 string to OpenCV image"""
        img_data = base64.b64decode(base64_str)
        nparr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return img

    def _create_fallback_response(self, error_msg: str) -> Dict[str, Any]:
        """Create fallback response when parsing fails"""
        return {
            "overall_score": 0.5,
            "is_satisfactory": False,
            "discrepancies": [],
            "measurements": {
                "length_accuracy": 0.5,
                "beam_accuracy": 0.5,
                "proportions_match": 0.5
            },
            "positive_aspects": [],
            "issues": [f"Vision model response parsing failed: {error_msg}"],
            "specific_suggestions": ["Review vision model output format"],
            "error": error_msg
        }


# Convenience function for backward compatibility
async def evaluate_screenshot_with_local_vision(
    screenshot_base64: str,
    user_intent: str,
    endpoint: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Quick helper to evaluate a screenshot with local vision model

    Args:
        screenshot_base64: Base64-encoded screenshot
        user_intent: Original scene description
        endpoint: Optional vision model endpoint
        **kwargs: Additional args for analyze_scene()

    Returns:
        Evaluation dict with scores and suggestions
    """

    if endpoint:
        config = VisionModelConfig(endpoint=endpoint)
    else:
        config = None

    async with ComparisonVisionClient(config=config) as client:
        return await client.analyze_scene(
            screenshot_base64=screenshot_base64,
            user_intent=user_intent,
            **kwargs
        )


# Test function
async def test_local_vision():
    """Test local Qwen2.5-VL integration"""

    print("Testing Local Vision Model Integration...")

    # Check endpoint
    endpoint = os.getenv("VISION_MODEL_ENDPOINT", "http://localhost:8000/v1")
    print(f"✓ Using endpoint: {endpoint}")

    # Create test image (1x1 red pixel)
    test_screenshot = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

    async with ComparisonVisionClient() as client:
        print("✓ Vision client created")
        print("✓ Testing API connection...")

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
            print(f"⚠ API call failed: {e}")
            print(f"  Make sure vision model is running at {endpoint}")
            return False


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_local_vision())
