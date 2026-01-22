"""Modern model interfaces for VIGA.

This module provides a minimal abstraction (`FoundationModel`) and concrete
implementations that talk to OpenAI-compatible endpoints.

Qwen3-VL runs against a local server exposing `/v1/chat/completions`.
Image support depends on the backend; if images are rejected, it retries
text-only so the loop can keep making progress.
"""

from abc import ABC, abstractmethod
import os
from typing import List

import aiohttp

from ..vision_utils import normalize_vision_endpoint

class FoundationModel(ABC):
    @abstractmethod
    async def generate_text(self, system_prompt: str, user_prompt: str, images: List[str] = []) -> str:
        """Generate text with optional image inputs"""
        pass

class Qwen3VL(FoundationModel):
    """
    Qwen 3 VL (released Jan 2026) wrapper.
    State of the art open weights model.
    """
    def __init__(self, size: str = "30B"):
        normalized_size = str(size).upper()
        self.model_name = f"Qwen/Qwen3-VL-{normalized_size}-Instruct"
        self.endpoint = normalize_vision_endpoint(
            os.getenv("QWEN3_VL_ENDPOINT", os.getenv("VISION_MODEL_ENDPOINT", "http://localhost:8000/v1"))
        )
        self.timeout_s = float(os.getenv("QWEN3_VL_TIMEOUT", "300"))
        self.temperature = float(os.getenv("QWEN3_VL_TEMPERATURE", "0.3"))
        self.max_tokens = int(os.getenv("QWEN3_VL_MAX_TOKENS", "2048"))
        self.served_model = os.getenv("QWEN3_VL_MODEL", self.model_name)
        
    async def generate_text(self, system_prompt: str, user_prompt: str, images: List[str] = []) -> str:
        messages = [{"role": "system", "content": system_prompt}]

        if images:
            content_parts = [{"type": "text", "text": user_prompt}]
            for img_b64 in images:
                if not img_b64:
                    continue
                content_parts.append(
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{img_b64}"},
                    }
                )
            messages.append({"role": "user", "content": content_parts})
        else:
            messages.append({"role": "user", "content": user_prompt})

        payload = {
            "model": self.served_model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        url = f"{self.endpoint}/chat/completions"
        timeout = aiohttp.ClientTimeout(total=self.timeout_s)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=payload) as resp:
                # If backend rejects multimodal schema, retry as text-only.
                if resp.status == 400 and images:
                    payload["messages"] = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ]
                    async with session.post(url, json=payload) as resp2:
                        if resp2.status != 200:
                            text2 = await resp2.text()
                            raise RuntimeError(f"Qwen3-VL request failed ({resp2.status}): {text2}")
                        data2 = await resp2.json()
                        return data2["choices"][0]["message"]["content"]

                if resp.status != 200:
                    text = await resp.text()
                    raise RuntimeError(f"Qwen3-VL request failed ({resp.status}): {text}")

                data = await resp.json()
                return data["choices"][0]["message"]["content"]

class Gemini3Pro(FoundationModel):
    """
    Google Gemini 3 Pro (released Jan 2026).
    Supports pro, flash, and flash-lite variants.
    Uses Google AI Studio API (generativelanguage.googleapis.com).
    """
    def __init__(self, variant: str = "pro"):
        # variant: pro, flash, flash-lite
        self.variant = variant.lower()
        self.model_name = f"gemini-3.0-{self.variant}"
        self.api_key = os.getenv("GOOGLE_AI_API_KEY", os.getenv("GEMINI_API_KEY", ""))
        self.endpoint = os.getenv(
            "GEMINI_ENDPOINT",
            "https://generativelanguage.googleapis.com/v1beta"
        )
        self.timeout_s = float(os.getenv("GEMINI_TIMEOUT", "120"))
        self.temperature = float(os.getenv("GEMINI_TEMPERATURE", "0.4"))
        self.max_tokens = int(os.getenv("GEMINI_MAX_TOKENS", "2048"))

    async def generate_text(self, system_prompt: str, user_prompt: str, images: List[str] = []) -> str:
        if not self.api_key:
            raise RuntimeError(
                "Gemini API key not configured. Set GOOGLE_AI_API_KEY or GEMINI_API_KEY env var."
            )

        # Build content parts
        parts = []
        
        # Add images first (Gemini prefers images before text)
        for img_b64 in images:
            if not img_b64:
                continue
            parts.append({
                "inline_data": {
                    "mime_type": "image/png",
                    "data": img_b64
                }
            })
        
        # Add text prompt
        parts.append({"text": user_prompt})

        payload = {
            "contents": [{"parts": parts}],
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": self.max_tokens,
            }
        }

        url = f"{self.endpoint}/models/{self.model_name}:generateContent?key={self.api_key}"
        timeout = aiohttp.ClientTimeout(total=self.timeout_s)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=payload) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise RuntimeError(f"Gemini request failed ({resp.status}): {text}")
                
                data = await resp.json()
                
                # Extract text from response
                try:
                    candidates = data.get("candidates", [])
                    if not candidates:
                        raise RuntimeError(f"Gemini returned no candidates: {data}")
                    content = candidates[0].get("content", {})
                    parts = content.get("parts", [])
                    if not parts:
                        raise RuntimeError(f"Gemini returned no parts: {data}")
                    return parts[0].get("text", "")
                except (KeyError, IndexError) as e:
                    raise RuntimeError(f"Failed to parse Gemini response: {e}, data={data}")

class MockModel(FoundationModel):
    """Temporary mock for testing logic flow"""
    async def generate_text(self, system_prompt: str, user_prompt: str, images: List[str] = []) -> str:
        if "plan" in user_prompt.lower():
            return """```json
{
    "subtasks": [{"id": "1", "description": "Create base mesh"}]
}
```"""
        return """```python
import bpy
# Mock generation
bpy.ops.mesh.primitive_cube_add()
```"""

def get_model(name: str) -> FoundationModel:
    lower = name.lower()
    if "qwen" in lower:
        if "30" in lower:
            return Qwen3VL(size="30B")
        if "8" in lower:
            return Qwen3VL(size="8B")
        return Qwen3VL(size=os.getenv("QWEN3_VL_SIZE", "30B"))

    if "gemini" in lower:
        return Gemini3Pro()
    return MockModel()

