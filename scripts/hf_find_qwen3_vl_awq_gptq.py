"""Find Qwen3-VL quantized (AWQ/GPTQ) variants suitable for vLLM/SGLang.

Why: Qwen3-VL GGUF currently fails to load in llama.cpp/llama-cpp-python in this
workspace (unknown architecture 'qwen3vl'). AWQ/GPTQ weights are typically the
most compatible path for vLLM/SGLang.

Prints recommended repos for 8B and 30B.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import requests

HF_API_BASE = "https://huggingface.co/api"


def _read_dotenv_token(dotenv_path: Path) -> Optional[str]:
    if not dotenv_path.exists():
        return None
    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key in {"HUGGINGFACE_TOKEN", "HF_TOKEN", "HUGGINGFACE_HUB_TOKEN"} and value:
            return value
    return None


def _auth_headers() -> Dict[str, str]:
    token = (
        os.getenv("HUGGINGFACE_TOKEN")
        or os.getenv("HF_TOKEN")
        or os.getenv("HUGGINGFACE_HUB_TOKEN")
        or _read_dotenv_token(Path(__file__).resolve().parents[1] / ".env")
    )
    return {"Authorization": f"Bearer {token}"} if token else {}


@dataclass(frozen=True)
class Candidate:
    repo_id: str
    likes: int
    downloads: int


def search_models(query: str, limit: int = 30) -> List[Candidate]:
    url = f"{HF_API_BASE}/models"
    params = {"search": query, "limit": str(limit)}
    r = requests.get(url, params=params, headers=_auth_headers(), timeout=30)
    r.raise_for_status()

    candidates: List[Candidate] = []
    for item in r.json():
        repo_id = item.get("modelId") or item.get("id")
        if not repo_id:
            continue
        candidates.append(
            Candidate(
                repo_id=repo_id,
                likes=int(item.get("likes") or 0),
                downloads=int(item.get("downloads") or 0),
            )
        )

    candidates.sort(key=lambda c: (c.downloads, c.likes), reverse=True)
    return candidates


def pick_best(size: str) -> Dict[str, Optional[str]]:
    # Prefer AWQ for vLLM (fast, widely supported). Fall back to GPTQ.
    queries = [
        f"Qwen3-VL-{size} AWQ",
        f"Qwen3-VL-{size} GPTQ",
        f"Qwen3 VL {size} AWQ",
        f"Qwen3 VL {size} GPTQ",
    ]

    awq: List[Candidate] = []
    gptq: List[Candidate] = []

    for q in queries:
        for c in search_models(q, limit=30):
            rid = c.repo_id.lower()
            if f"vl-{size.lower()}" not in rid and size.lower() not in rid:
                continue
            if "awq" in rid:
                awq.append(c)
            if "gptq" in rid:
                gptq.append(c)

    awq.sort(key=lambda c: (c.downloads, c.likes), reverse=True)
    gptq.sort(key=lambda c: (c.downloads, c.likes), reverse=True)

    return {
        "awq": awq[0].repo_id if awq else None,
        "gptq": gptq[0].repo_id if gptq else None,
    }


def main() -> int:
    print("Hugging Face Qwen3-VL quantized finder (AWQ/GPTQ)")
    print("- Uses token from env or .env (if present)")
    print("")

    for size in ("8B", "30B"):
        picks = pick_best(size)
        print(f"Target: Qwen3-VL-{size}")
        print(f"  AWQ:  {picks['awq'] or '<not found>'}")
        print(f"  GPTQ: {picks['gptq'] or '<not found>'}")
        print("")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
