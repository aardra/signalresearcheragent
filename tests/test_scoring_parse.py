"""Tests for Agent 2 scoring output parsing and retry behaviour."""

from __future__ import annotations

import pytest

from models import ScoringOutput
from scoring_engine import (
    ScoringParseError,
    _extract_last_json_object,
    _parse_scoring_output,
    _safe_json_parse,
)


class _FakeOutput:
    def __init__(self, raw: str) -> None:
        self.raw = raw
        self.pydantic = None
        self.json_dict = None


class _FakeTask:
    def __init__(self, raw: str) -> None:
        self.output = _FakeOutput(raw)


def test_safe_json_parse_extracts_trailing_json_after_prose() -> None:
    text = (
        "Now I have all the context needed.\n\n"
        "**Total: 28 + 8 + 20 + 8 = 64**\n\n"
        '{"regulatory_score": 28, "supporting_score": 8, "icp_fit_score": 20, '
        '"recency_score": 8, "total_score": 64, "scoring_rationale": "Example."}'
    )
    parsed = _safe_json_parse(text)
    assert parsed is not None
    assert parsed["total_score"] == 64


def test_parse_scoring_output_raises_when_unparseable() -> None:
    task = _FakeTask("This is prose only with no JSON block.")
    with pytest.raises(ScoringParseError) as exc:
        _parse_scoring_output(task, "Bank of America")
    assert exc.value.company_name == "Bank of America"


def test_parse_scoring_output_parses_valid_json_task() -> None:
    task = _FakeTask(
        '{"regulatory_score": 10, "supporting_score": 5, "icp_fit_score": 15, '
        '"recency_score": 3, "total_score": 33, "scoring_rationale": "OK"}'
    )
    result = _parse_scoring_output(task, "Stripe")
    assert isinstance(result, ScoringOutput)
    assert result.total_score == 33


def test_extract_last_json_object_ignores_unrelated_braces() -> None:
    text = 'noise {not json} then {"tier": "Tier 2", "reason": "x", '
    text += '"primary_signal_used": "regulatory_action", '
    text += '"confidence_in_tier": "High", "flag_for_review": false}'
    parsed = _extract_last_json_object(text)
    assert parsed is not None
    assert parsed["tier"] == "Tier 2"
