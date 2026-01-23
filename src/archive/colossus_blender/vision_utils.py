"""
Shared utilities for vision model integrations.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List


def normalize_vision_endpoint(endpoint: str) -> str:
    """Normalize an OpenAI-compatible base endpoint to include /v1.

    Examples:
        http://localhost:8000   -> http://localhost:8000/v1
        http://localhost:8000/  -> http://localhost:8000/v1
        http://localhost:8000/v1 -> http://localhost:8000/v1
    """
    normalized = endpoint.rstrip("/")
    if normalized.endswith("/v1"):
        return normalized
    return f"{normalized}/v1"


def extract_json_from_content(content: str) -> Dict[str, Any]:
    """Extract JSON object from model response content.

    Supports fenced code blocks and raw JSON payloads.
    """
    if "```json" in content:
        json_content = content.split("```json")[1].split("```")[0].strip()
    elif "{" in content and "}" in content:
        start = content.find("{")
        end = content.rfind("}") + 1
        json_content = content[start:end]
    else:
        json_content = content.strip()

    return json.loads(json_content)


def _iter_model_ids(models_payload: Dict[str, Any]) -> Iterable[str]:
    """Yield model IDs from an OpenAI-compatible /models payload."""
    if not models_payload:
        return []

    if isinstance(models_payload.get("data"), list):
        return [item.get("id", "") for item in models_payload["data"]]

    if isinstance(models_payload.get("models"), list):
        return [item.get("id", "") for item in models_payload["models"]]

    return []


def is_model_available(model_name: str, models_payload: Dict[str, Any]) -> bool:
    """Check if a model name exists in a /models payload."""
    model_ids = [model_id for model_id in _iter_model_ids(models_payload) if model_id]
    return model_name in model_ids


def list_available_models(models_payload: Dict[str, Any]) -> List[str]:
    """Return available model IDs from a /models payload."""
    return [model_id for model_id in _iter_model_ids(models_payload) if model_id]


def extract_code_from_response(response: str) -> str:
    """Extract Python code from LLM response with triple backticks.
    
    Handles:
    - ```python ... ``` blocks
    - Generic ``` ... ``` blocks
    - Raw code (no blocks)
    """
    if "```python" in response:
        start = response.find("```python") + len("```python")
        end = response.find("```", start)
        if end > start:
            return response[start:end].strip()
    elif "```" in response:
        start = response.find("```") + 3
        end = response.find("```", start)
        if end > start:
            return response[start:end].strip()
    return response.strip()
