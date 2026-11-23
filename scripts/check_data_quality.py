#!/usr/bin/env python3
"""Evidências de qualidade de dados do dataset oficial (entrega do César, v0.4.0).

Somente leitura: importa o XLSX com o mesmo importador do sistema, confere schema e relações,
levanta as evidências de cada pendência de dados do relatório v0.4.0 e roda o motor de regras para
medir impacto. Nada é escrito no arquivo de origem.

Uso:
    python scripts/check_data_quality.py [caminho.xlsx] [--out arquivo.json]
    python scripts/check_data_quality.py --corrected-copy destino.xlsx   # gera a cópia de TESTE com AI07 corrigida

Sem caminho usa tests/data/PD_Bank_Analyzer_Dataset_Completo_Alunos_1.xlsx.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from pdbank.importer import import_file  # noqa: E402
from pdbank.rules import analyze_full  # noqa: E402
from pdbank.schema import (FIELD_ALIASES, INFORMATIONAL_FIELDS, OFFICIAL_SHEETS,  # noqa: E402
                           CLASSIFICATION_ORDER)
from pdbank.values import normalize, parse_bool, parse_date  # noqa: E402

DEFAULT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tests", "data",
                       "PD_Bank_Analyzer_Dataset_Completo_Alunos_1.xlsx")

ACTION_LEVELS = {"recomendar", "executar"}
IMPACT_LEVELS = {"baixo", "medio", "alto", "critico"}
# Ordem das colunas de casos_uso_ia no dataset oficial (usada para reconstruir linhas deslocadas).
AI_COLUMNS = ("ai_use_case_id", "name", "application_id", "business_area", "purpose", "action_level",
              "impact_level", "owner_id", "status")
_KNOWN_FIELDS = {n for names in FIELD_ALIASES.values() for n in names} | set(INFORMATIONAL_FIELDS)


def _n(v) -> str:
    return normalize(v) if v is not None else ""


def _ids(rows, field):
    return {_n(r.get(field)) for r in rows if r.get(field) not in (None, "")}


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def load(path: str) -> dict:
    with open(path, "rb") as fh:
        return import_file(os.path.basename(path), fh.read()).tables


# P1 ---------------------------------------------------------------------------------------------
def check_schema(t: dict) -> dict:
    sheets = {}
    for name in OFFICIAL_SHEETS:
        rows = t.get(name, [])
        headers = sorted({k for r in rows for k in r if not k.startswith("__")})
        sheets[name] = {"linhas": len(rows), "cabecalhos": headers,
                        "sem_tratamento": [h for h in headers if h not in _KNOWN_FIELDS]}
    return {"abas_esperadas": len(OFFICIAL_SHEETS), "abas_presentes": sum(1 for s in OFFICIAL_SHEETS if s in t),
            "abas_extras": sorted(set(t) - set(OFFICIAL_SHEETS)),
            "registros": sum(len(v) for v in t.values()), "abas": sheets,
            "cabecalhos_sem_tratamento": sum(len(s["sem_tratamento"]) for s in sheets.values())}


# P2 ---------------------------------------------------------------------------------------------
def check_relations(t: dict) -> dict:
    users, roles = _ids(t["usuarios"], "user_id"), _ids(t["catalogo_papeis"], "role_id")
    apps, res = _ids(t["aplicacoes"], "application_id"), _ids(t["recursos"], "resource_id")
    assets, cases = _ids(t["ativos_dados"], "data_asset_id"), _ids(t["casos_uso_ia"], "ai_use_case_id")
    principals = users | apps

    def orphans(sheet, field, valid, id_field=None):
        bad = [r for r in t[sheet] if r.get(field) not in (None, "") and _n(r.get(field)) not in valid]
        return {"relacao": f"{sheet}.{field}", "linhas": len(t[sheet]), "orfaos": len(bad),
                "exemplos": sorted({str(r.get(field)) for r in bad})[:10]}

    rel = [
        orphans("usuarios", "papel_primario_id", roles),
        orphans("usuarios", "manager_id", users),
        orphans("atribuicoes_papeis", "user_id", users),
        orphans("atribuicoes_papeis", "role_id", roles),
        orphans("rbac_baseline", "role_id", roles),
        orphans("rbac_baseline", "resource_id", res),
        orphans("permissoes_atuais", "principal_id", principals),
        orphans("permissoes_atuais", "resource_id", res),
        orphans("revisoes_acesso", "principal_id", principals),
        orphans("revisoes_acesso", "resource_id", res),
        orphans("revisoes_acesso", "reviewer_id", users),
        orphans("recursos", "application_id", apps),
        orphans("aplicacoes", "owner_id", users),
        orphans("ativos_dados", "resource_id", res),
        orphans("ativos_dados", "owner_id", users),
        orphans("campos_dados", "data_asset_id", assets),
        orphans("eventos_compartilhamento", "data_asset_id", assets),
        orphans("eventos_compartilhamento", "requested_by", users),
        orphans("politicas_retencao", "data_asset_id", assets),
        orphans("casos_uso_ia", "application_id", apps),
        orphans("casos_uso_ia", "owner_id", users),
        orphans("fontes_dados_ia", "ai_use_case_id", cases),
        orphans("fontes_dados_ia", "data_asset_id", assets),
        orphans("controles_ia", "ai_use_case_id", cases),
        orphans("excecoes", "subject_id", principals | assets | cases),
        orphans("excecoes", "approved_by", users),
    ]
    status = {_n(u["user_id"]): _n(u.get("status")) for u in t["usuarios"]}
    self_mgr = sorted(u["user_id"] for u in t["usuarios"] if _n(u.get("manager_id")) == _n(u["user_id"]))
    share_by_off = sorted(f"{s['sharing_id']}({s['requested_by']})" for s in t["eventos_compartilhamento"]
                          if status.get(_n(s.get("requested_by"))) == "desligado")
    without_ctrl = sorted(c for c in cases if c not in _ids(t["controles_ia"], "ai_use_case_id"))
    without_ret = sorted(a for a in assets if a not in _ids(t["politicas_retencao"], "data_asset_id"))
    return {"relacoes": rel, "usuarios_gestor_de_si_mesmo": self_mgr,
            "compartilhamentos_pedidos_por_desligado": share_by_off,
            "casos_ia_sem_controles": without_ctrl, "ativos_sem_politica_retencao": without_ret}


# P3 ---------------------------------------------------------------------------------------------
def check_application_principals(t: dict) -> dict:
    res_crit = {_n(r["resource_id"]): _n(r.get("criticality")) for r in t["recursos"]}
    owners = {_n(a["application_id"]): a.get("owner_id") for a in t["aplicacoes"]}
    status = {_n(u["user_id"]): u.get("status") for u in t["usuarios"]}
    perms = [p for p in t["permissoes_atuais"] if _n(p.get("principal_type")) == "aplicacao"]
    admin_crit = [p for p in perms if _n(p.get("permission")) == "admin" and res_crit.get(_n(p["resource_id"])) == "critica"]
    owner_not_active = sorted({f"{p['principal_id']}(dono {owners.get(_n(p['principal_id']))}: "
                               f"{status.get(_n(owners.get(_n(p['principal_id']))))})"
                               for p in perms if _n(status.get(_n(owners.get(_n(p["principal_id"]))))) != "ativo"})
    return {"total": len(perms), "aplicacoes": len({_n(p["principal_id"]) for p in perms}),
            "por_permissao": dict(Counter(p.get("permission") for p in perms)),
            "por_criticidade_recurso": dict(Counter(res_crit.get(_n(p["resource_id"]), "?") for p in perms)),
            "admin_em_recurso_critico": sorted(f"{p['permission_id']}:{p['principal_id']}->{p['resource_id']}" for p in admin_crit),
            "modos": dict(Counter(p.get("access_mode") for p in perms)),
            "justificativas": dict(Counter(p.get("business_justification") for p in perms)),
            "aplicacoes_com_dono_nao_ativo": owner_not_active}


# P4 ---------------------------------------------------------------------------------------------
def check_leave_users(t: dict, ref) -> dict:
    out = []
    for u in t["usuarios"]:
        if _n(u.get("status")) != "licenca":
            continue
        perms = [p for p in t["permissoes_atuais"] if _n(p.get("principal_id")) == _n(u["user_id"])]
        recent = [p for p in perms if (d := parse_date(p.get("last_used_date"))) and ref and (ref - d).days <= 30]
        out.append({"user_id": u["user_id"], "papel": u.get("papel_primario"), "permissoes": len(perms),
                    "niveis": dict(Counter(p.get("permission") for p in perms)),
                    "uso_ultimos_30_dias": sorted(f"{p['resource_id']}:{p['permission']}@{p['last_used_date']}" for p in recent)})
    return {"usuarios": out, "status_usuarios": dict(Counter(u.get("status") for u in t["usuarios"])),
            "data_inicio_licenca_disponivel": any("licenca" in k for r in t["usuarios"] for k in r)}


# P5 ---------------------------------------------------------------------------------------------
def reconstruct_shifted_ai_row(row: dict) -> dict | None:
    """Detecta deslocamento de 1 coluna à esquerda a partir de business_area e devolve a linha reconstruída.

    Só reconstrói quando o padrão é inequívoco: purpose é um nível de ação, action_level é um nível de
    impacto e impact_level parece um user_id. business_area original é perdido e fica None (não inventado)."""
    if _n(row.get("action_level")) in ACTION_LEVELS and _n(row.get("impact_level")) in IMPACT_LEVELS:
        return None
    if not (_n(row.get("purpose")) in ACTION_LEVELS and _n(row.get("action_level")) in IMPACT_LEVELS
            and str(row.get("impact_level") or "").upper().startswith("U")):
        return None
    fixed = dict(row)
    fixed.update(business_area=None, purpose=row.get("business_area"), action_level=row.get("purpose"),
                 impact_level=row.get("action_level"), owner_id=row.get("impact_level"), status=row.get("owner_id"))
    return fixed


def check_ai_rows(t: dict) -> dict:
    bad = []
    for r in t["casos_uso_ia"]:
        if _n(r.get("action_level")) in ACTION_LEVELS and _n(r.get("impact_level")) in IMPACT_LEVELS:
            continue
        fixed = reconstruct_shifted_ai_row(r)
        bad.append({"linha": r.get("__row"), "ai_use_case_id": r.get("ai_use_case_id"),
                    "original": {c: r.get(c) for c in AI_COLUMNS},
                    "reconstruida": {c: fixed.get(c) for c in AI_COLUMNS} if fixed else None})
    return {"linhas_inconsistentes": bad}


# P6 ---------------------------------------------------------------------------------------------
def check_reviews(t: dict, ref) -> dict:
    buckets = Counter()
    for rv in t["revisoes_acesso"]:
        nxt = parse_date(rv.get("next_review_date"))
        if _n(rv.get("decision")) == "manter" and nxt and ref and nxt < ref:
            days = (ref - nxt).days
            buckets["ate_30" if days <= 30 else "31_90" if days <= 90 else "91_180" if days <= 180 else "mais_180"] += 1
    pending_not_due = sum(1 for rv in t["revisoes_acesso"] if _n(rv.get("decision")) == "pendente"
                          and (n := parse_date(rv.get("next_review_date"))) and ref and n >= ref)
    return {"decisoes": dict(Counter(rv.get("decision") for rv in t["revisoes_acesso"])),
            "recertificacao_vencida_total": sum(buckets.values()),
            "recertificacao_vencida_por_atraso_dias": dict(buckets),
            "pendentes_ainda_nao_vencidas": pending_not_due}


# P7 ---------------------------------------------------------------------------------------------
def check_exceptions(t: dict, findings: list) -> dict:
    out = []
    for e in t["excecoes"]:
        sid = _n(e.get("subject_id"))
        target = _n(e.get("resource_or_asset_id"))
        hits = [f for f in findings if _n(f.get("subject_id")) == sid and (not target or _n(f.get("related_id")) == target)]
        out.append({"exception_id": e.get("exception_id"), "subject_id": e.get("subject_id"),
                    "resource_or_asset_id": e.get("resource_or_asset_id"), "reason": e.get("reason"),
                    "expiration_date": e.get("expiration_date"), "status": e.get("status"),
                    "achados_cobertos": sorted(f"{f['rule_id']}:{f['finding_type']}" for f in hits)})
    tc15 = next((c for c in t["casos_teste_publicos"] if _n(c.get("test_case_id")) == "tc15"), None)
    ai03 = {"caso": next((c for c in t["casos_uso_ia"] if _n(c.get("ai_use_case_id")) == "ai03"), None),
            "controles": [c for c in t["controles_ia"] if _n(c.get("ai_use_case_id")) == "ai03"],
            "fontes": [s for s in t["fontes_dados_ia"] if _n(s.get("ai_use_case_id")) == "ai03"]}
    ret_da11 = [r for r in t["politicas_retencao"] if _n(r.get("data_asset_id")) == "da11"]
    strip = lambda rows: [{k: v for k, v in r.items() if not k.startswith("__")} for r in rows]  # noqa: E731
    return {"excecoes": out, "tc15": strip([tc15])[0] if tc15 else None,
            "ai03": {"caso": strip([ai03["caso"]])[0] if ai03["caso"] else None,
                     "controles": strip(ai03["controles"]), "fontes": strip(ai03["fontes"])},
            "retencao_da11": strip(ret_da11)}


# P8 ---------------------------------------------------------------------------------------------
def check_data_fields(t: dict) -> dict:
    assets = {_n(a["data_asset_id"]): a for a in t["ativos_dados"]}
    by_asset = {}
    for f in t["campos_dados"]:
        by_asset.setdefault(_n(f.get("data_asset_id")), []).append(f)
    personal_mismatch, ident_low_class, fin_mismatch = [], [], []
    for aid, fields in by_asset.items():
        a = assets.get(aid)
        if not a:
            continue
        has_personal = any(_n(f.get("data_category")) == "pessoal" for f in fields)
        has_fin = any(_n(f.get("data_category")) == "financeiro" for f in fields)
        has_ident = any(parse_bool(f.get("direct_identifier")) for f in fields)
        if has_personal and parse_bool(a.get("contains_personal_data")) is False:
            personal_mismatch.append(a["data_asset_id"])
        if has_fin and parse_bool(a.get("contains_financial_data")) is False:
            fin_mismatch.append(a["data_asset_id"])
        if has_ident and CLASSIFICATION_ORDER.get(_n(a.get("classification")), -1) < CLASSIFICATION_ORDER["confidencial"]:
            ident_low_class.append(f"{a['data_asset_id']}({a.get('classification')})")
    ident_assets = {aid for aid, fs in by_asset.items() if any(parse_bool(f.get("direct_identifier")) for f in fs)}
    min_share_ident = sorted(s["sharing_id"] for s in t["eventos_compartilhamento"]
                             if _n(s.get("data_asset_id")) in ident_assets and parse_bool(s.get("minimum_data_only")))
    return {"campos": len(t["campos_dados"]), "ativos_com_campos": len(by_asset),
            "ativos_sem_campos": sorted(a["data_asset_id"] for k, a in assets.items() if k not in by_asset),
            "sensivel_x_identificador": {f"{k[0]}/{k[1]}": v for k, v in Counter(
                (f.get("sensitive"), f.get("direct_identifier")) for f in t["campos_dados"]).items()},
            "categorias": dict(Counter(f.get("data_category") for f in t["campos_dados"])),
            "campo_pessoal_mas_ativo_sem_dado_pessoal": sorted(personal_mismatch),
            "campo_financeiro_mas_ativo_sem_dado_financeiro": sorted(fin_mismatch),
            "identificador_direto_em_ativo_abaixo_de_confidencial": sorted(ident_low_class),
            "compartilhamentos_minimos_de_ativo_com_identificador_direto": min_share_ident}


# ------------------------------------------------------------------------------------------------
def summarize_findings(findings: list) -> dict:
    return {"total": len(findings), "por_regra": dict(sorted(Counter(f["rule_id"] for f in findings).items())),
            "por_tipo": {f"{r}:{ty}": n for (r, ty), n in sorted(Counter((f["rule_id"], f["finding_type"]) for f in findings).items())}}


def build_report(path: str) -> dict:
    t = load(path)
    out = analyze_full(t)
    ref = parse_date(out.reference_date)
    return {"arquivo": os.path.basename(path), "sha256": sha256(path), "data_referencia": out.reference_date,
            "P1_schema": check_schema(t), "P2_relacoes": check_relations(t),
            "P3_principals_aplicacao": check_application_principals(t), "P4_usuarios_licenca": check_leave_users(t, ref),
            "P5_linhas_ia_deslocadas": check_ai_rows(t), "P6_revisoes": check_reviews(t, ref),
            "P7_excecoes": check_exceptions(t, out.findings), "P8_campos_dados": check_data_fields(t),
            "achados": summarize_findings(out.findings)}


def write_corrected_copy(src: str, dst: str) -> list:
    """Cópia de TESTE com linhas de casos_uso_ia deslocadas reconstruídas. O arquivo de origem não é tocado."""
    import openpyxl
    if os.path.abspath(src) == os.path.abspath(dst):
        raise ValueError("o destino não pode ser o arquivo oficial")
    wb = openpyxl.load_workbook(src)
    ws = wb["casos_uso_ia"]
    header = [normalize(c.value) for c in ws[1]]
    fixed_ids = []
    for cells in ws.iter_rows(min_row=2):
        row = {header[i]: c.value for i, c in enumerate(cells)}
        fixed = reconstruct_shifted_ai_row(row)
        if fixed:
            for i, c in enumerate(cells):
                c.value = fixed.get(header[i])
            fixed_ids.append(row.get("ai_use_case_id"))
    wb.save(dst)
    return fixed_ids


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("xlsx", nargs="?", default=DEFAULT)
    ap.add_argument("--out", help="grava o relatório JSON completo")
    ap.add_argument("--corrected-copy", help="gera a cópia de teste corrigida neste caminho e compara os achados")
    a = ap.parse_args(argv)
    rep = build_report(a.xlsx)
    if a.corrected_copy:
        rep["copia_corrigida"] = {"arquivo": os.path.basename(a.corrected_copy),
                                  "linhas_corrigidas": write_corrected_copy(a.xlsx, a.corrected_copy)}
        rep["copia_corrigida"]["achados"] = summarize_findings(analyze_full(load(a.corrected_copy)).findings)
        before = rep["achados"]["por_tipo"]
        after = rep["copia_corrigida"]["achados"]["por_tipo"]
        rep["copia_corrigida"]["delta_por_tipo"] = {k: after.get(k, 0) - before.get(k, 0)
                                                    for k in sorted(set(before) | set(after)) if after.get(k, 0) != before.get(k, 0)}
        rep["sha256_original_apos_copia"] = sha256(a.xlsx)
    text = json.dumps(rep, ensure_ascii=False, indent=2, default=str)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
