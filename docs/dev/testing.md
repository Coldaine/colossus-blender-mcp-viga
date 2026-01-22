# Testing

## What tests exist

- Unit tests for VIGA memory, model adapters (mocked), and code extraction.
- Integration-style tests for the VIGA loop using mocks.

## Running tests

From repo root:
- `python -m pytest tests/ -v`

## Adding tests

- Prefer pytest.
- Keep network calls mocked.
- If a test requires Blender running, mark it clearly and keep it separate from default CI/unit runs.
