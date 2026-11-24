#!/usr/bin/env python3
"""Confere o Excel oficial por HTTP; cria um dataset e uma análise no servidor alvo."""
import argparse
import csv
import hashlib
import io
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from uuid import uuid4


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://localhost:8080")
    parser.add_argument("--origin", default="http://localhost:5173")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    source = Path(__file__).resolve().parents[1] / "tests/data/PD_Bank_Analyzer_Dataset_Completo_Alunos_1.xlsx"
    checks = []

    def check(condition, label):
        if not condition:
            raise AssertionError(label)
        checks.append(label)

    def request(path, *, method="GET", data=None, headers=None, status=200):
        sent = {"Origin": args.origin, **(headers or {})}
        if os.environ.get("API_KEY"):
            sent["X-API-Key"] = os.environ["API_KEY"]
        req = Request(args.base_url.rstrip("/") + path, data=data, headers=sent, method=method)
        with urlopen(req, timeout=120) as response:
            check(response.status == status, f"{method} {path}: HTTP {status}")
            check(response.headers.get("Access-Control-Allow-Origin") in (args.origin, "*"),
                  f"{method} {path}: CORS permitido")
            return response.read(), response.headers

    body, _ = request("/api/health")
    health = json.loads(body)
    check(health["status"] == "ok" and health["database"] == "ok", "API e banco saudáveis")
    _, headers = request("/api/analyses", method="OPTIONS", headers={
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type,x-api-key",
    })
    check("POST" in headers["Access-Control-Allow-Methods"], "Preflight aceita POST")
    check("x-api-key" in headers["Access-Control-Allow-Headers"].lower(), "Preflight aceita X-API-Key")

    boundary = uuid4().hex
    content = source.read_bytes()
    multipart = (f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{source.name}"\r\n'
                 'Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet\r\n\r\n').encode()
    multipart += content + f"\r\n--{boundary}--\r\n".encode()
    body, _ = request("/api/datasets/import", method="POST", data=multipart,
                      headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}, status=201)
    imported = json.loads(body)
    validation = imported["validation"]
    check(validation["valid"] and len(validation["recognized_sheets"]) == 20
          and validation["records_total"] == 1890, "Excel oficial: 20 abas, 1890 registros válidos")
    dataset_id = imported["dataset"]["id"]
    body, _ = request("/api/analyses", method="POST", data=json.dumps({"dataset_id": dataset_id}).encode(),
                      headers={"Content-Type": "application/json"}, status=201)
    analysis = json.loads(body)
    analysis_id = analysis["id"]
    check(analysis["summary"]["total"] == 431 and analysis["reference_date"] == "2026-11-05",
          "Snapshot v0.4.0: 431 achados, referência 2026-11-05")
    body, headers = request(f"/api/findings?analysis_id={analysis_id}&limit=20&offset=0")
    findings = json.loads(body)
    check(len(findings) == 20 and headers["X-Total-Count"] == "431", "Paginação: 20 itens de 431")
    check("X-Total-Count" in headers["Access-Control-Expose-Headers"], "Contagem exposta ao frontend")
    request(f"/api/findings/{findings[0]['id']}")
    body, _ = request(f"/api/analyses/{analysis_id}")
    persisted = json.loads(body)
    check(persisted["findings"] == analysis["findings"] and persisted["summary"] == analysis["summary"],
          "Achados e resumo preservados após leitura do banco")
    body, headers = request(f"/api/analyses/{analysis_id}/export?format=json")
    check(json.loads(body) == persisted, "Exportação JSON igual à análise persistida")
    check("attachment" in headers["Content-Disposition"], "JSON disponível para download")
    body, headers = request(f"/api/analyses/{analysis_id}/export?format=csv")
    rows = list(csv.DictReader(io.StringIO(body.decode("utf-8-sig"))))
    check(len(rows) == 431 and {"source_sheet", "source_row", "rule_id"} <= rows[0].keys(),
          "CSV: 431 linhas com rastreabilidade")
    check("Content-Disposition" in headers["Access-Control-Expose-Headers"], "Nome do download exposto ao frontend")
    report = {
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "base_url": args.base_url, "origin": args.origin, "version": health["version"],
        "dataset_sha256": hashlib.sha256(content).hexdigest(),
        "dataset_id": dataset_id, "analysis_id": analysis_id,
        "summary": analysis["summary"], "checks": checks,
    }
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"OK: {len(checks)} verificações; dataset={dataset_id}; análise={analysis_id}; achados=431")


if __name__ == "__main__":
    main()
