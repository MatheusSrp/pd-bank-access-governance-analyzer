"""Contrato de persistência + implementação em memória (testes/desenvolvimento).

A API só fala com ``Repository`` e com dicts simples; o SQLAlchemy fica isolado em
``sql_repository.py``. Ambas as implementações passam pelo mesmo teste de contrato.
"""
from __future__ import annotations

import copy
import threading
from datetime import datetime, timezone

FINDING_FILTERS = ("analysis_id", "domain", "rule_id", "severity", "status", "exception_status")


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class Repository:  # interface documental
    def init(self) -> None: ...
    def ping(self) -> bool: ...
    def add_dataset(self, name: str, tables: dict) -> dict: ...
    def list_datasets(self) -> list: ...
    def get_dataset(self, dataset_id: int) -> dict | None: ...          # inclui "tables"
    def add_analysis(self, dataset_id: int, reference_date: str, coverage: dict, summary: dict, findings: list) -> dict: ...
    def list_analyses(self) -> list: ...                                # sem findings
    def get_analysis(self, analysis_id: int) -> dict | None: ...        # com findings
    def list_findings(self, filters: dict, limit: int, offset: int, q: str | None = None) -> tuple: ...
    def get_finding(self, finding_id: int) -> dict | None: ...


class MemoryRepository(Repository):
    def __init__(self):
        self._lock = threading.Lock()
        self._datasets, self._analyses, self._findings = {}, {}, {}
        self._seq = {"d": 0, "a": 0, "f": 0}

    def init(self): pass
    def ping(self): return True

    def _next(self, k):
        self._seq[k] += 1
        return self._seq[k]

    def add_dataset(self, name, tables):
        with self._lock:
            i = self._next("d")
            self._datasets[i] = {"id": i, "name": name[:255], "created_at": utcnow_iso(), "tables": copy.deepcopy(tables)}
            return self._public_dataset(self._datasets[i])

    @staticmethod
    def _public_dataset(d):
        return {"id": d["id"], "name": d["name"], "created_at": d["created_at"],
                "table_counts": {k: len(v) if isinstance(v, list) else None for k, v in d["tables"].items()}}

    def list_datasets(self):
        return [self._public_dataset(d) for d in sorted(self._datasets.values(), key=lambda x: -x["id"])]

    def get_dataset(self, dataset_id):
        d = self._datasets.get(dataset_id)
        return None if d is None else {**self._public_dataset(d), "tables": copy.deepcopy(d["tables"])}

    def add_analysis(self, dataset_id, reference_date, coverage, summary, findings):
        with self._lock:
            i = self._next("a")
            a = {"id": i, "dataset_id": dataset_id, "created_at": utcnow_iso(), "status": "completed",
                 "reference_date": reference_date, "coverage": copy.deepcopy(coverage), "summary": copy.deepcopy(summary),
                 "finding_ids": []}
            for f in findings:
                fid = self._next("f")
                self._findings[fid] = {**copy.deepcopy(f), "id": fid, "analysis_id": i, "domain": f["category"], "reviewer": None}
                a["finding_ids"].append(fid)
            self._analyses[i] = a
            return self._public_analysis(a, with_findings=True)

    def _public_analysis(self, a, with_findings):
        out = {k: copy.deepcopy(v) for k, v in a.items() if k != "finding_ids"}
        if with_findings:
            out["findings"] = [copy.deepcopy(self._findings[i]) for i in a["finding_ids"]]
        return out

    def list_analyses(self):
        return [self._public_analysis(a, False) for a in sorted(self._analyses.values(), key=lambda x: -x["id"])]

    def get_analysis(self, analysis_id):
        a = self._analyses.get(analysis_id)
        return None if a is None else self._public_analysis(a, True)

    def list_findings(self, filters, limit, offset, q=None):
        items = sorted(self._findings.values(), key=lambda f: f["id"])
        for key, value in filters.items():
            if value is not None:
                items = [f for f in items if f.get(key) == value]
        if q:
            items = [f for f in items if q.lower() in str(f["object_ref"]).lower()]
        return [copy.deepcopy(f) for f in items[offset: offset + limit]], len(items)

    def get_finding(self, finding_id):
        f = self._findings.get(finding_id)
        return None if f is None else copy.deepcopy(f)
