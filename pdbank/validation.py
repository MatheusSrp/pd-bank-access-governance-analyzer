"""Validação estrutural de datasets (não executa regras)."""
from __future__ import annotations

from .importer import ROW_META
from .schema import REQUIRED_FIELDS, SHEET_ALIASES, canonical_sheet, has_column, is_known_sheet

MAX_TABLES_JSON = 100


def validate_data(data: dict, import_warnings: list | None = None) -> dict:
    errors: list = []
    warnings: list = list(import_warnings or [])
    recognized: list = []
    unknown: list = []
    records = rejected = 0
    if len(data) > MAX_TABLES_JSON:
        errors.append({"table": None, "message": f"Mais de {MAX_TABLES_JSON} tabelas."})
    for name, rows in data.items():
        if is_known_sheet(name):
            recognized.append({"source_name": name, "canonical_name": canonical_sheet(name)})
        else:
            unknown.append(name)
        if not isinstance(rows, list):
            errors.append({"table": name, "row": None, "message": "A tabela precisa ser uma lista de linhas."})
            continue
        records += len(rows)
        for i, row in enumerate(rows, 1):
            if not isinstance(row, dict):
                errors.append({"table": name, "row": i, "message": "Linha não é um objeto."})
                rejected += 1
            elif ROW_META in row and not isinstance(row[ROW_META], int):
                errors.append({"table": name, "row": i, "message": f"{ROW_META} deve ser inteiro."})
                rejected += 1
        if not rows and is_known_sheet(name):
            warnings.append(f"Aba {name} foi reconhecida, mas não contém registros de dados.")
    if unknown:
        warnings.append("Abas não listadas no catálogo foram preservadas sem interpretação: " + ", ".join(map(str, unknown)))
    if not recognized:
        warnings.append("Nenhuma aba conhecida foi reconhecida; nenhuma regra poderá ser avaliada.")
    # Cobertura de campos: avisa quando uma aba reconhecida não tem colunas que as regras esperam.
    by_key: dict = {}
    for name, rows in data.items():
        if isinstance(rows, list) and is_known_sheet(name):
            by_key.setdefault(canonical_sheet(name), []).extend(rows)
    for key, groups in REQUIRED_FIELDS.items():
        rows = by_key.get(key)
        if not rows:
            continue
        for group in groups:
            if not has_column(rows, *group):
                warnings.append(f"Aba '{key}': nenhuma coluna reconhecida para {' ou '.join(group)}; as regras dependentes serão puladas/limitadas.")
    for key, rule in (("baseline", "R01"), ("sod", "R02")):
        if not by_key.get(key):
            warnings.append(f"{rule} requer a aba '{SHEET_ALIASES[key][-1]}'; sem ela a regra será pulada (nenhum achado presumido).")
    return {"valid": not errors, "errors": errors, "warnings": warnings, "recognized_sheets": recognized,
            "unknown_sheets": unknown, "records_total": records, "records_accepted": records - rejected,
            "records_rejected": rejected,
            "tables": {k: (len(v) if isinstance(v, list) else None) for k, v in data.items()}}
