"""
VIGA Context Memory Management
Implements the evolving context memory with sliding window as described in arXiv:2601.11109v1
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import json

@dataclass
class IterationContext:
    """Stores the context for a single iteration (t)"""
    iteration_id: int
    plan: Optional[str] = None          # from make_plan
    code: Optional[str] = None          # from p_t
    code_diff: Optional[str] = None     # diff from p_{t-1}
    execution_result: Optional[str] = None # stdout/stderr
    visual_feedback: Optional[str] = None # c_t (Verifier feedback)
    rendered_image_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "iteration": self.iteration_id,
            "plan": self.plan,
            "code": self.code,
            "visual_feedback": self.visual_feedback
        }

    def to_prompt_str(self) -> str:
        """Format for VLM context consumption"""
        parts = [f"## Iteration {self.iteration_id}"]
        if self.plan:
            parts.append(f"**Plan**: {self.plan}")
        if self.code:
            parts.append(f"**Code Generated**: \n```python\n{self.code}\n```")
        if self.visual_feedback:
            parts.append(f"**Verifier Feedback**: {self.visual_feedback}")
        return "\n".join(parts)


class VIGAMemory:
    """
    Evolving context memory M_t with sliding window Tail_L.
    """
    def __init__(self, window_size: int = 3):
        self.history: List[IterationContext] = []
        self.window_size = window_size
        self.static_context: Dict[str, Any] = {} # Initial task, inputs

    def add_iteration(self, context: IterationContext):
        self.history.append(context)

    def get_context_window(self) -> List[IterationContext]:
        """Returns Tail_L(M_t)"""
        return self.history[-self.window_size:]

    def get_full_prompt(self) -> str:
        """Constructs the prompt from the sliding window memory"""
        window = self.get_context_window()
        prompt = "### Interaction History (Recent)\n\n"
        for ctx in window:
            prompt += ctx.to_prompt_str() + "\n\n"
        return prompt

    def get_latest_code(self) -> str:
        """Retrieve p_{t-1} for diffing or extending"""
        for ctx in reversed(self.history):
            if ctx.code:
                return ctx.code
        return ""

