from __future__ import annotations

from collections import Counter

from .rules import RULE_IDS

SEVERITIES = ("critical", "high", "medium", "low")
STATUSES = ("non_compliant", "insufficient_information", "valid_exception", "compliant")


def summarize(findings: list) -> dict:
    return {
        "total": len(findings),
        "by_severity": {k: sum(f["severity"] == k for f in findings) for k in SEVERITIES},
        "by_status": {k: sum(f["status"] == k for f in findings) for k in STATUSES},
        "by_rule": {r: sum(f["rule_id"] == r for f in findings) for r in RULE_IDS},
        "by_type": dict(sorted(Counter(f.get("finding_type") or "n/d" for f in findings).items())),
        "expired_exceptions": sum(f.get("exception_status") == "expired" for f in findings),
    }
