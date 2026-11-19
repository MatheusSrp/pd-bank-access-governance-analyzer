from __future__ import annotations

import csv
import io

CSV_FIELDS = ["id", "analysis_id", "rule_id", "domain", "finding_type", "severity", "status", "exception_status", "object_ref", "subject_id", "related_id",
              "source_sheet", "source_row", "description", "evidence", "impact", "recommendation", "reviewer"]


def csv_safe(value):
    """Neutraliza injeção de fórmula (CSV aberto no Excel): prefixa ' em células que começam com = + - @ TAB CR."""
    if isinstance(value, str) and value[:1] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + value
    return value


def findings_to_csv(findings: list) -> bytes:
    out = io.StringIO(newline="")
    writer = csv.DictWriter(out, fieldnames=CSV_FIELDS, extrasaction="ignore")
    writer.writeheader()
    for f in findings:
        writer.writerow({k: csv_safe(f.get(k)) for k in CSV_FIELDS})
    return out.getvalue().encode("utf-8-sig")
