import pytest

from src.colossus_blender.vision_utils import (
    normalize_vision_endpoint,
    extract_json_from_content,
    is_model_available,
    list_available_models,
)


def test_normalize_vision_endpoint_adds_v1():
    assert normalize_vision_endpoint("http://localhost:8000") == "http://localhost:8000/v1"


def test_normalize_vision_endpoint_strips_trailing_slash():
    assert normalize_vision_endpoint("http://localhost:8000/") == "http://localhost:8000/v1"


def test_normalize_vision_endpoint_keeps_v1():
    assert normalize_vision_endpoint("http://localhost:8000/v1") == "http://localhost:8000/v1"


def test_extract_json_from_fenced_block():
    content = """
    Here is the response:
    ```json
    {"foo": "bar", "value": 3}
    ```
    """
    assert extract_json_from_content(content) == {"foo": "bar", "value": 3}


def test_extract_json_from_inline_object():
    content = "Result: {\"ok\": true, \"count\": 2}"
    assert extract_json_from_content(content) == {"ok": True, "count": 2}


def test_is_model_available_from_data_payload():
    payload = {"data": [{"id": "Qwen2.5-VL-72B-Instruct"}, {"id": "other"}]}
    assert is_model_available("Qwen2.5-VL-72B-Instruct", payload) is True
    assert is_model_available("missing", payload) is False


def test_list_available_models_from_models_payload():
    payload = {"models": [{"id": "a"}, {"id": "b"}]}
    assert list_available_models(payload) == ["a", "b"]
