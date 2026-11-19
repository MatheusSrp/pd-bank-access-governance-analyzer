#!/usr/bin/env python3
"""Importa o XLSX oficial, roda a análise completa e imprime/grava o resultado real.

Uso:  python scripts/analyze_official_dataset.py [caminho.xlsx] [--out docs/resultado_dataset_oficial.json]
Sem argumentos usa tests/data/PD_Bank_Analyzer_Dataset_Completo_Alunos_1.xlsx. Nada é simulado:
tudo vem de import_file -> validate_data -> analyze_full -> compare_public_cases.
"""
import argparse
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from pdbank.importer import import_file  # noqa: E402
from pdbank.public_cases import compare_public_cases  # noqa: E402
from pdbank.rules import RULE_IDS, RULE_TITLES, analyze_full  # noqa: E402
from pdbank.summary import summarize  # noqa: E402
from pdbank.validation import validate_data  # noqa: E402

DEFAULT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tests", "data",
                       "PD_Bank_Analyzer_Dataset_Completo_Alunos_1.xlsx")


def build_report(path: str) -> dict:
    with open(path, "rb") as fh:
        imp = import_file(os.path.basename(path), fh.read())
    val = validate_data(imp.tables, imp.warnings)
    out = analyze_full(imp.tables)
    cases = compare_public_cases(imp.tables, out.findings)
    by_type = Counter((f["rule_id"], f["finding_type"]) for f in out.findings)
    return {
        "arquivo": os.path.basename(path),
        "importacao": {"abas_lidas": len(imp.tables), "abas_reconhecidas": len(val["recognized_sheets"]),
                       "abas_desconhecidas": val["unknown_sheets"], "registros": val["records_total"],
                       "linhas_por_aba": val["tables"], "avisos": val["warnings"], "valido": val["valid"]},
        "data_referencia": out.reference_date, "fonte_data_referencia": out.reference_source,
        "resumo": summarize(out.findings),
        "achados_por_regra_e_tipo": [{"regra": r, "tipo": t, "qtd": n} for (r, t), n in sorted(by_type.items())],
        "cobertura": {r: out.coverage[r] for r in (*RULE_IDS, "EXCEPTIONS", "META")},
        "casos_publicos": cases,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("xlsx", nargs="?", default=DEFAULT)
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    rep = build_report(a.xlsx)
    print(f"Arquivo: {rep['arquivo']} | referência: {rep['data_referencia']} ({rep['fonte_data_referencia']})")
    im = rep["importacao"]
    print(f"Importação: {im['abas_lidas']} abas lidas, {im['abas_reconhecidas']} reconhecidas, {im['registros']} registros, válido={im['valido']}, avisos={len(im['avisos'])}")
    print("\nAchados por regra:")
    for r in RULE_IDS:
        cov = rep["cobertura"][r]
        print(f"  {r} {RULE_TITLES[r]:<55} achados={rep['resumo']['by_rule'][r]:>4}  avaliada={cov['evaluated']}  registros={cov['records_checked']}")
    print(f"  TOTAL {rep['resumo']['total']}  severidade={rep['resumo']['by_severity']}  status={rep['resumo']['by_status']}")
    print("\nCasos públicos:", rep["casos_publicos"]["summary"])
    for c in rep["casos_publicos"]["cases"]:
        print(f"  {c['test_case_id']} [{c['verdict']:<9}] {c['expected']['category']:<28} {c['explanation'][:110]}")
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            json.dump(rep, fh, ensure_ascii=False, indent=2)
        print(f"\nRelatório gravado em {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
