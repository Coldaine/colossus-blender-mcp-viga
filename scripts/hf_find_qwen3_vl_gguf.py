"""Find suitable Qwen3-VL GGUF repos/files on Hugging Face.

This script uses the public Hugging Face REST API and (optionally) an auth token
from .env to avoid rate limits.

It prints a recommended repo and GGUF filename for each target size.
"""

from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

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
    )

    if not token:
        token = _read_dotenv_token(Path(__file__).resolve().parents[1] / ".env")

    if not token:
        return {}

    return {"Authorization": f"Bearer {token}"}


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
    payload = r.json()

    candidates: List[Candidate] = []
    for item in payload:
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

    # Prefer higher downloads then likes
    candidates.sort(key=lambda c: (c.downloads, c.likes), reverse=True)
    return candidates


def get_repo_files(repo_id: str) -> List[str]:
    url = f"{HF_API_BASE}/models/{repo_id}"
    r = requests.get(url, headers=_auth_headers(), timeout=30)
    r.raise_for_status()
    payload = r.json()

    siblings = payload.get("siblings") or []
    files = []
    for s in siblings:
        name = s.get("rfilename")
        if name:
            files.append(name)
    return files


def pick_gguf_file(files: List[str], preferred_quant: str) -> Optional[str]:
    ggufs = [f for f in files if f.lower().endswith(".gguf")]
    if not ggufs:
        return None

    # Prefer exact quant match first, then partial match.
    preferred_quant_norm = preferred_quant.lower()
    exact = [f for f in ggufs if preferred_quant_norm in f.lower()]
    if exact:
        # prefer smaller shard count / shorter name
        exact.sort(key=lambda x: (x.count("-"), len(x)))
        return exact[0]

    # Heuristic fallback: prefer Q4_K_M if available
    q4km = [f for f in ggufs if "q4_k_m" in f.lower()]
    if q4km:
        q4km.sort(key=lambda x: (x.count("-"), len(x)))
        return q4km[0]

    # Otherwise take the first gguf
    ggufs.sort(key=lambda x: (x.count("-"), len(x)))
    return ggufs[0]


def find_best_repo(size: str) -> Tuple[Optional[str], Optional[str]]:
    # Try multiple searches because naming isn’t consistent.
    search_terms = [
        f"Qwen3-VL-{size} GGUF",
        f"Qwen3 VL {size} GGUF",
        f"Qwen3-VL-{size}-Instruct GGUF",
    ]

    candidates: List[Candidate] = []
    seen = set()
    for term in search_terms:
        for c in search_models(term, limit=30):
            if c.repo_id in seen:
                continue
            seen.add(c.repo_id)
            # Filter to plausible repos
            if "gguf" not in c.repo_id.lower():
                continue
            if f"vl-{size}".lower() not in c.repo_id.lower() and f"{size}" not in c.repo_id.lower():
                continue
            candidates.append(c)

    candidates.sort(key=lambda c: (c.downloads, c.likes), reverse=True)
    if not candidates:
        return None, None

    preferred_quant = os.getenv("QWEN3_GGUF_QUANT", "Q4_K_M")

    for c in candidates[:10]:
        try:
            files = get_repo_files(c.repo_id)
        except Exception:
            continue

        chosen = pick_gguf_file(files, preferred_quant=preferred_quant)
        if chosen:
            return c.repo_id, chosen

    return candidates[0].repo_id, None


def main() -> int:
    sizes = ["8B", "30B"]

    print("Hugging Face Qwen3-VL GGUF finder")
    print("- Uses token from env or .env (if present)")
    print("- Set QWEN3_GGUF_QUANT to override (default: Q4_K_M)")
    print("")

    for size in sizes:
        repo, gguf = find_best_repo(size)
        print(f"Target: Qwen3-VL-{size}")
        if not repo:
            print("  Repo: <not found>")
            print("  GGUF: <not found>")
            print("")
            continue

        print(f"  Repo: {repo}")
        print(f"  GGUF: {gguf or '<no .gguf detected via API>'}")
        if gguf:
            print("  Download (PowerShell):")
            print(f"    huggingface-cli download {repo} --include \"{gguf}\" --local-dir .\\models\\{repo.split('/')[-1]} --local-dir-use-symlinks False")
        print("")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
