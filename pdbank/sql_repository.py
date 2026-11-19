"""Persistência SQLAlchemy 2.x (SQLite local ou PostgreSQL).

NOTA: este módulo foi escrito sem poder executar SQLAlchemy no ambiente de auditoria
(pacote indisponível/sem rede). Cobertura: ``tests/test_sql_repository.py`` (roda onde
SQLAlchemy está instalado). Execute a suíte antes de usar.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, create_engine, func, inspect, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from .repository import Repository


class Base(DeclarativeBase):
    pass


def _now():
    return datetime.now(timezone.utc)


class DatasetRow(Base):
    __tablename__ = "datasets"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    content: Mapped[str] = mapped_column(Text)


class AnalysisRow(Base):
    __tablename__ = "analyses"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    status: Mapped[str] = mapped_column(String(40), default="completed")
    reference_date: Mapped[str | None] = mapped_column(String(10), nullable=True)
    coverage: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)


class FindingRow(Base):
    __tablename__ = "findings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    analysis_id: Mapped[int] = mapped_column(ForeignKey("analyses.id"), index=True)
    rule_id: Mapped[str] = mapped_column(String(8))
    category: Mapped[str] = mapped_column(String(80))
    severity: Mapped[str] = mapped_column(String(20))
    object_ref: Mapped[str] = mapped_column(String(255))
    evidence: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    impact: Mapped[str] = mapped_column(Text)
    recommendation: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="open")
    exception_status: Mapped[str] = mapped_column(String(20), default="none")
    source_sheet: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_row: Mapped[int | None] = mapped_column(Integer, nullable=True)
    finding_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    subject_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    related_id: Mapped[str | None] = mapped_column(String(255), nullable=True)


# Colunas adicionadas após a v0.2 (migração aditiva em bancos existentes).
_ADDED_COLUMNS = {
    "analyses": {"reference_date": "VARCHAR(10)", "coverage": "TEXT", "summary": "TEXT"},
    "findings": {"exception_status": "VARCHAR(20) NOT NULL DEFAULT 'none'", "source_sheet": "VARCHAR(255)",
                 "source_row": "INTEGER", "finding_type": "VARCHAR(80)", "subject_id": "VARCHAR(255)",
                 "related_id": "VARCHAR(255)"},
}
_FILTER_COLUMNS = {"analysis_id": FindingRow.analysis_id, "domain": FindingRow.category, "rule_id": FindingRow.rule_id,
                   "severity": FindingRow.severity, "status": FindingRow.status,
                   "exception_status": FindingRow.exception_status}


def _finding_dict(f: FindingRow) -> dict:
    d = {k: getattr(f, k) for k in ("id", "analysis_id", "rule_id", "category", "severity", "object_ref", "evidence",
                                     "description", "impact", "recommendation", "status", "exception_status",
                                     "source_sheet", "source_row", "finding_type", "subject_id",
                                     "related_id")}
    d["domain"], d["reviewer"] = f.category, None
    return d


def _analysis_dict(a: AnalysisRow) -> dict:
    return {"id": a.id, "dataset_id": a.dataset_id, "created_at": a.created_at.isoformat(), "status": a.status,
            "reference_date": a.reference_date, "coverage": json.loads(a.coverage) if a.coverage else None,
            "summary": json.loads(a.summary) if a.summary else None}


class SqlRepository(Repository):
    def __init__(self, url: str):
        self.url = url
        kwargs = {"connect_args": {"check_same_thread": False}} if url.startswith("sqlite") else {"pool_pre_ping": True}
        self.engine = create_engine(url, **kwargs)
        self.Session = sessionmaker(self.engine, expire_on_commit=False)

    def init(self):
        Base.metadata.create_all(self.engine)
        insp = inspect(self.engine)
        for table, cols in _ADDED_COLUMNS.items():
            existing = {c["name"] for c in insp.get_columns(table)}
            for name, ddl in cols.items():
                if name not in existing:
                    with self.engine.begin() as conn:
                        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))
        self.engine.dispose()  # evita compartilhar conexões entre workers após fork (gunicorn --preload)

    def ping(self):
        try:
            with self.engine.connect() as c:
                c.execute(text("SELECT 1"))
            return True
        except SQLAlchemyError:
            return False

    @staticmethod
    def _dataset_dict(d: DatasetRow, tables: dict | None = None) -> dict:
        tables = tables if tables is not None else json.loads(d.content)
        out = {"id": d.id, "name": d.name, "created_at": d.created_at.isoformat(),
               "table_counts": {k: len(v) if isinstance(v, list) else None for k, v in tables.items()}}
        return out

    def add_dataset(self, name, tables):
        with self.Session() as s:
            d = DatasetRow(name=name[:255], content=json.dumps(tables, ensure_ascii=False, default=str))
            s.add(d)
            s.commit()
            return self._dataset_dict(d, tables)

    def list_datasets(self):
        with self.Session() as s:
            return [self._dataset_dict(d) for d in s.scalars(select(DatasetRow).order_by(DatasetRow.id.desc()))]

    def get_dataset(self, dataset_id):
        with self.Session() as s:
            d = s.get(DatasetRow, dataset_id)
            if d is None:
                return None
            tables = json.loads(d.content)
            return {**self._dataset_dict(d, tables), "tables": tables}

    def add_analysis(self, dataset_id, reference_date, coverage, summary, findings):
        with self.Session() as s:
            a = AnalysisRow(dataset_id=dataset_id, reference_date=reference_date,
                            coverage=json.dumps(coverage, ensure_ascii=False), summary=json.dumps(summary))
            s.add(a)
            s.flush()
            rows = [FindingRow(analysis_id=a.id, rule_id=f["rule_id"], category=f["category"][:80], severity=f["severity"],
                               object_ref=str(f["object_ref"])[:255], evidence=f["evidence"], description=f["description"],
                               impact=f["impact"], recommendation=f["recommendation"], status=f["status"],
                               exception_status=f["exception_status"], source_sheet=(f.get("source_sheet") or "")[:255] or None,
                               source_row=f.get("source_row"), finding_type=(f.get("finding_type") or "")[:80] or None,
                               subject_id=(str(f["subject_id"])[:255] if f.get("subject_id") is not None else None),
                               related_id=(str(f["related_id"])[:255] if f.get("related_id") is not None else None))
                    for f in findings]
            s.add_all(rows)
            s.commit()
            return {**_analysis_dict(a), "findings": [_finding_dict(r) for r in rows]}

    def list_analyses(self):
        with self.Session() as s:
            return [_analysis_dict(a) for a in s.scalars(select(AnalysisRow).order_by(AnalysisRow.id.desc()))]

    def get_analysis(self, analysis_id):
        with self.Session() as s:
            a = s.get(AnalysisRow, analysis_id)
            if a is None:
                return None
            fs = s.scalars(select(FindingRow).where(FindingRow.analysis_id == a.id).order_by(FindingRow.id)).all()
            return {**_analysis_dict(a), "findings": [_finding_dict(f) for f in fs]}

    def list_findings(self, filters, limit, offset, q=None):
        with self.Session() as s:
            stmt = select(FindingRow)
            for key, value in filters.items():
                if value is not None:
                    stmt = stmt.where(_FILTER_COLUMNS[key] == value)
            if q:
                stmt = stmt.where(func.lower(FindingRow.object_ref).contains(q.lower(), autoescape=True))
            total = s.scalar(select(func.count()).select_from(stmt.subquery()))
            items = s.scalars(stmt.order_by(FindingRow.id).limit(limit).offset(offset)).all()
            return [_finding_dict(f) for f in items], int(total or 0)

    def get_finding(self, finding_id):
        with self.Session() as s:
            f = s.get(FindingRow, finding_id)
            return None if f is None else _finding_dict(f)
