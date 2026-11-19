import io
import zipfile
from datetime import date, timedelta

TODAY = date(2026, 11, 19)
PAST = (TODAY - timedelta(days=10)).isoformat()
FUTURE = (TODAY + timedelta(days=10)).isoformat()


def make_xlsx(sheets: dict) -> bytes:
    from openpyxl import Workbook
    wb = Workbook()
    wb.remove(wb.active)
    for title, rows in sheets.items():
        ws = wb.create_sheet(title)
        for r in rows:
            ws.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def make_zip(files: dict) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, content in files.items():
            z.writestr(name, content)
    return buf.getvalue()


# ---------------------------------------------------------------------------------------------
# Dataset mínimo com os CABEÇALHOS OFICIAIS (mesmas colunas do dataset oficial v2.0), já no formato
# que o importador produz (chaves normalizadas). Cada teste parte dele e altera só o necessário.
# ---------------------------------------------------------------------------------------------
import copy

REF = date(2026, 11, 5)


def _perm(pid, user, res, perm, src="Via_Papel", mode="Permanente", exp=None, ptype="Usuario"):
    return {"permission_id": pid, "principal_id": user, "principal_type": ptype, "resource_id": res, "permission": perm,
            "assignment_source": src, "access_mode": mode, "grant_date": "2025-01-01", "expiration_date": exp,
            "last_used_date": "2026-10-01", "business_justification": "x"}


def mini_dataset() -> dict:
    d = {
        "usuarios": [{"user_id": "U1", "status": "Ativo"}, {"user_id": "U2", "status": "Desligado"}, {"user_id": "U3", "status": "Ativo"}],
        "recursos": [{"resource_id": "RES1", "criticality": "Alta", "classification": "Confidencial"},
                     {"resource_id": "RES2", "criticality": "Critica", "classification": "Restrito"}],
        "atribuicoes_papeis": [
            {"user_id": "U1", "role_id": "R01", "assignment_type": "Primario", "start_date": "2024-01-01", "end_date": None},
            {"user_id": "U2", "role_id": "R01", "assignment_type": "Primario", "start_date": "2024-01-01", "end_date": None},
            {"user_id": "U3", "role_id": "R10", "assignment_type": "Primario", "start_date": "2024-01-01", "end_date": None}],
        "rbac_baseline": [
            {"role_id": "R01", "resource_id": "RES1", "allowed_permission": "Read", "expected_access_mode": "Permanente"},
            {"role_id": "R10", "resource_id": "RES2", "allowed_permission": "Approve", "expected_access_mode": "Permanente"},
            {"role_id": "R11", "resource_id": "RES2", "allowed_permission": "Create", "expected_access_mode": "Permanente"}],
        "permissoes_atuais": [_perm("P1", "U1", "RES1", "Read"), _perm("P2", "U3", "RES2", "Approve")],
        "regras_sod": [{"rule_id": "SOD01", "role_a": "R10", "role_b": "R11", "severity": "Critico", "rationale": "x"}],
        "revisoes_acesso": [], "ativos_dados": [], "eventos_compartilhamento": [], "politicas_retencao": [],
        "casos_uso_ia": [], "fontes_dados_ia": [], "controles_ia": [], "excecoes": [],
    }
    for t, rows in d.items():
        for i, r in enumerate(rows, 2):
            r["__row"] = i
    return d


def mini(**changes) -> dict:
    """mini_dataset() com tabelas substituídas/acrescentadas: mini(permissoes_atuais=[...])."""
    d = copy.deepcopy(mini_dataset())
    for t, rows in changes.items():
        d[t] = rows
    for t, rows in d.items():
        for i, r in enumerate(rows, 2):
            r.setdefault("__row", i)
    return d


def perm(*a, **k):
    return _perm(*a, **k)
