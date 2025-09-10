from enum import Enum
from typing import Any
from pydantic import BaseModel, ValidationError
from dataclasses import dataclass, asdict

class Verdict(str, Enum):
    PASS = "PASS"
    FAIL_SCHEMA = "FAIL_SCHEMA"
    FAIL_EXCEPTION = "FAIL_EXCEPTION"

@dataclass
class FailureDetails:
    kind: str | None = None  # "schema_mismatch" | "exception"
    schema_expected: dict | None = None
    schema_found: Any | None = None
    error_class: str | None = None
    message: str | None = None

FAIL_KINDS = {"schema_mismatch", "exception"}

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

def _expected_from_model(model_cls: type[BaseModel]) -> dict:
    try:
        # Compact json schema; callers can further canonicalize
        return model_cls.model_json_schema()  # type: ignore[attr-defined]
    except Exception:
        # Fallback: list of fields only
        try:
            return {"title": model_cls.__name__, "fields": list(model_cls.model_fields.keys())}
        except Exception:
            return {"title": model_cls.__name__}


def _found_summary(output: Any) -> Any:
    # Keep found as-is if it is simple JSON-like; else summarize
    try:
        import json
        json.dumps(output)
        return output
    except Exception:
        if isinstance(output, dict):
            return {k: type(v).__name__ for k, v in output.items()}
        return type(output).__name__

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

    def validate_with_details(self, output: Any, tool_name: str) -> tuple[Verdict, FailureDetails]:
        schema = SCHEMA_MAP.get(tool_name)
        if not schema:
            return Verdict.PASS, FailureDetails()
        try:
            schema.model_validate(output)
            return Verdict.PASS, FailureDetails()
        except ValidationError as ve:
            details = FailureDetails(
                kind="schema_mismatch",
                schema_expected=_expected_from_model(schema),
                schema_found=_found_summary(output),
                error_class="ValidationError",
                message=str(ve)[:500],
            )
            return Verdict.FAIL_SCHEMA, details
        except Exception as e:
            details = FailureDetails(
                kind="exception",
                error_class=type(e).__name__,
                message=str(e)[:500],
            )
            return Verdict.FAIL_EXCEPTION, details

    def safe_run_with_details(self, fn, tool_name: str) -> tuple[Verdict, FailureDetails]:
        try:
            output = fn()
        except Exception as e:
            return Verdict.FAIL_EXCEPTION, FailureDetails(kind="exception", error_class=type(e).__name__, message=str(e)[:500])
        return self.validate_with_details(output, tool_name)
