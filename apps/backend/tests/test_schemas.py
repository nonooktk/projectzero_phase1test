"""Pydantic スキーマの最低限の境界テスト。"""
import pytest
from pydantic import ValidationError

from src.domain.schemas import AnalyzeRequest, AxisAnalysis, SearchHit


def test_analyze_request_empty_theme_rejected() -> None:
    with pytest.raises(ValidationError):
        AnalyzeRequest(theme="")


def test_axis_analysis_defaults() -> None:
    a = AxisAnalysis()
    assert a.score == "－"
    assert a.key_points == []


def test_search_hit_source_constraint() -> None:
    SearchHit(id="x", content="c", score=0.5, source="external")
    with pytest.raises(ValidationError):
        SearchHit(id="x", content="c", score=0.5, source="unknown")  # type: ignore[arg-type]
