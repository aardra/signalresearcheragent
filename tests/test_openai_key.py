"""Smoke tests for OpenAI API key configuration."""

from __future__ import annotations

import os

import pytest
from dotenv import load_dotenv
from openai import OpenAI

PLACEHOLDER_VALUES = {
    "sk-your-key-here",
    "your-serper-key-here",
    "sk-ant-your-key-here",
}


def _get_openai_api_key() -> str | None:
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY", "").strip().strip('"').strip("'")
    if not api_key or api_key in PLACEHOLDER_VALUES:
        return None
    return api_key


@pytest.mark.integration
def test_openai_api_key_is_valid() -> None:
    """Verify OPENAI_API_KEY authenticates against the OpenAI API."""
    api_key = _get_openai_api_key()
    if api_key is None:
        pytest.skip("OPENAI_API_KEY not configured")

    client = OpenAI(api_key=api_key)
    models = client.models.list()
    assert models.data, "Expected at least one model from OpenAI API"
