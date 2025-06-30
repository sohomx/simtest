import pytest
from simtest.verdict.engine import VerdictEngine, Verdict

def test_valid_output_passes():
    engine = VerdictEngine()
    out = {"summary": "text"}
    assert engine.validate(out, "AnalyzeTool") == Verdict.PASS

def test_schema_fail():
    engine = VerdictEngine()
    out = {"summary": 123}  # not a string
    assert engine.validate(out, "AnalyzeTool") == Verdict.FAIL_SCHEMA

def test_exception_fail():
    engine = VerdictEngine()

    def crash():
        raise RuntimeError("boom")

    assert engine.safe_run(crash, "AnalyzeTool") == Verdict.FAIL_EXCEPTION
