from enum import Enum
from typing import Any
from pydantic import BaseModel, ValidationError

class Verdict(str, Enum):
    PASS = "PASS"
    FAIL_SCHEMA = "FAIL_SCHEMA"
    FAIL_EXCEPTION = "FAIL_EXCEPTION"

class AnalyzeOutput(BaseModel):
    summary: str

class StartOutput(BaseModel):
    ack: bool

class EndOutput(BaseModel):
    success: bool

SCHEMA_MAP = {
    "StartTool": StartOutput,
    "AnalyzeTool": AnalyzeOutput,
    "EndTool": EndOutput,
}

class VerdictEngine:
    def validate(self, output: Any, tool_name: str) -> Verdict:
        schema = SCHEMA_MAP.get(tool_name)
        if not schema:
            return Verdict.PASS  # skip schema check for unknown tools
        try:
            schema.model_validate(output)
            return Verdict.PASS
        except ValidationError:
            return Verdict.FAIL_SCHEMA
        except Exception:
            return Verdict.FAIL_EXCEPTION

    def safe_run(self, fn, tool_name: str) -> Verdict:
        try:
            output = fn()
            return self.validate(output, tool_name)
        except Exception:
            return Verdict.FAIL_EXCEPTION
