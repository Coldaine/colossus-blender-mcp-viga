"""Smoke-test an OpenAI-compatible chat endpoint.

Usage:
  python scripts/test_openai_chat_endpoint.py http://127.0.0.1:8000/v1 MODEL_ID

If MODEL_ID is omitted, it will try to infer one from /models.
"""

from __future__ import annotations

import json
import sys
from typing import Any, Dict, List, Optional

import requests


def normalize(endpoint: str) -> str:
    endpoint = endpoint.rstrip("/")
    return endpoint if endpoint.endswith("/v1") else endpoint + "/v1"


def get_models(endpoint: str) -> List[str]:
    r = requests.get(f"{endpoint}/models", timeout=15)
    if r.status_code != 200:
        return []
    payload = r.json()
    data = payload.get("data") or payload.get("models") or []
    ids = []
    for item in data:
        mid = item.get("id")
        if mid:
            ids.append(mid)
    return ids


def chat(endpoint: str, model: str) -> Dict[str, Any]:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say OK."},
        ],
        "temperature": 0.0,
        "max_tokens": 16,
    }
    r = requests.post(f"{endpoint}/chat/completions", json=payload, timeout=60)
    return {"status": r.status_code, "body": r.text}


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_openai_chat_endpoint.py ENDPOINT [/v1] [MODEL_ID]")
        return 2

    endpoint = normalize(sys.argv[1])
    model = sys.argv[2] if len(sys.argv) >= 3 else None

    models = get_models(endpoint)
    if not model:
        model = models[0] if models else None

    print(json.dumps({"endpoint": endpoint, "models": models, "selected_model": model}, indent=2))

    if not model:
        print("No model ID available; /models missing or empty.")
        return 3

    res = chat(endpoint, model)
    print(json.dumps(res, indent=2))
    return 0 if res["status"] == 200 else 1


if __name__ == "__main__":
    raise SystemExit(main())
