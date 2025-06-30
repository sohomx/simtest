import pytest
from simtest.verdict.judge import LLMJudge, Judgement

def test_judge_returns_explanation(monkeypatch):
    def fake_eval(self, node_id, tool_name, task, output):
        return Judgement(verdict="FAIL", explanation="Tool missed key detail.")

    monkeypatch.setattr(LLMJudge, "evaluate", fake_eval)

    judge = LLMJudge()
    j = judge.evaluate("analyze", "AnalyzeTool", "summarize X", {"summary": "..."})

    assert j.verdict == "FAIL"
    assert j.explanation == "Tool missed key detail."
