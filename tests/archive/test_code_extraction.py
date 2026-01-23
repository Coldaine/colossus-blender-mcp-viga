# Tests for code extraction utility
import pytest

def extract_code_from_response(response: str) -> str:
    """Extract Python code from LLM response with triple backticks."""
    if "```python" in response:
        # Find first occurrence
        start = response.find("```python") + len("```python")
        end = response.find("```", start)
        if end > start:
            return response[start:end].strip()
    elif "```" in response:
        # Generic code block
        start = response.find("```") + 3
        end = response.find("```", start)
        if end > start:
            return response[start:end].strip()
    # No code block found, return as-is
    return response.strip()

class TestCodeExtraction:
    def test_extract_python_block(self):
        response = """Here is the code:
```python
import bpy
bpy.ops.mesh.primitive_cube_add()
```
Done."""
        code = extract_code_from_response(response)
        assert "import bpy" in code
        assert "primitive_cube" in code
        assert "```" not in code

    def test_extract_generic_block(self):
        response = """```
print("hello")
```"""
        code = extract_code_from_response(response)
        assert code == 'print("hello")'

    def test_no_code_block(self):
        response = "Just some text without code"
        code = extract_code_from_response(response)
        assert code == response

    def test_multiple_blocks_takes_first(self):
        response = """```python
first_block()
```
And then:
```python
second_block()
```"""
        code = extract_code_from_response(response)
        assert "first_block" in code
        assert "second_block" not in code

    def test_handles_newlines(self):
        response = """```python

import bpy

bpy.ops.mesh.primitive_cube_add()

```"""
        code = extract_code_from_response(response)
        assert code.startswith("import bpy")
