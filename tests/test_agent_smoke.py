"""Smoke tests for the test-generation agent. No network calls."""

from __future__ import annotations

import pytest

from forgeqa.agents import test_generator

VALID_CODE = '''def test_login(page):
    """User logs in successfully."""
    page.goto("https://example.com")
'''

VALID_FENCED = f"""```python
{VALID_CODE}```"""

INVALID_CODE = """def test_broken(page:
    pass
"""


@pytest.fixture
def mock_complete(monkeypatch):
    def _factory(return_value: str) -> None:
        def _complete(messages: list[dict]) -> str:
            return return_value

        monkeypatch.setattr(test_generator, "complete", _complete)

    return _factory


def test_valid_code_passes_validation(mock_complete) -> None:
    mock_complete(VALID_CODE)
    result = test_generator.generate_test(
        goal="Log in", context="", base_url="https://example.com"
    )
    assert result["is_valid"] is True
    assert result["code"] == VALID_CODE.strip()
    assert result["validation_error"] == ""


def test_fenced_code_strips_markdown(mock_complete) -> None:
    mock_complete(VALID_FENCED)
    result = test_generator.generate_test(goal="Log in")
    assert result["is_valid"] is True
    assert "```" not in result["code"]
    assert "def test_login" in result["code"]


def test_invalid_code_fails_validation(mock_complete) -> None:
    mock_complete(INVALID_CODE)
    result = test_generator.generate_test(goal="Broken test")
    assert result["is_valid"] is False
    assert result["validation_error"]
