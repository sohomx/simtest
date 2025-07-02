from enum import Enum

class VerdictType(str, Enum):
    PASS = "PASS"
    FAIL_SCHEMA = "FAIL_SCHEMA"
    FAIL_EXCEPTION = "FAIL_EXCEPTION"
    FAIL_POLICY = "FAIL_POLICY"
    FAIL_COST_SPIKE = "FAIL_COST_SPIKE"