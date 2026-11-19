import io
import json
import unittest

from pdbank.api import create_app
from pdbank.config import Settings
from pdbank.repository import MemoryRepository
from tests.helpers import make_xlsx, make_zip

BASELINE = "role_id,resource_id,allowed_permission,expected_access_mode\nR01,RES01,Read,Permanente\n"
ROLES = "user_id,role_id,assignment_type,start_date,end_date\nU001,R01,Primario,2024-01-01,\n"
PERM_HEADER = ("permission_id,principal_id,principal_type,resource_id,permission,assignment_source,access_mode,grant_date,"
               "expiration_date,last_used_date,business_justification\n")
GRANTS = PERM_HEADER + "P1,U001,Usuario,RES01,Read,Via_Papel,Permanente,2024-01-01,,,\nP2,U001,Usuario,RES01,Write,Direta,Permanente,2024-01-01,,,\n"
REVIEWS = ("review_id,principal_id,resource_id,review_date,decision,reviewer_id,next_review_date,review_comment\n"
           "AR1,U001,RES01,2026-01-01,Pendente,U002,2026-06-01,c\n")


def upload(client, name, data, **kw):
    return client.post("/api/datasets/import", data={"file": (io.BytesIO(data), name)}, content_type="multipart/form-data", **kw)


class ApiBase(unittest.TestCase):
    settings = Settings(database_url="memory")

    def setUp(self):
        self.repo = MemoryRepository()
        self.app = create_app(self.repo, self.settings)
        self.c = self.app.test_client()

    def dataset_with_finding(self):
        z = make_zip({"rbac_baseline.csv": BASELINE, "atribuicoes_papeis.csv": ROLES, "permissoes_atuais.csv": GRANTS,
                      "revisoes_acesso.csv": REVIEWS})
        r = upload(self.c, "d.zip", z)
        self.assertEqual(r.status_code, 201, r.json)
        return r.json["dataset"]["id"]


class HealthDocsTests(ApiBase):
    def test_health_rules_openapi_docs(self):
        self.assertEqual(self.c.get("/api/health").json["status"], "ok")
        self.assertEqual(len(self.c.get("/api/rules").json), 9)
        spec = self.c.get("/openapi.json").json
        for p in ("/api/findings", "/api/datasets/import", "/api/analyses/{id}/export", "/api/datasets/{id}"):
            self.assertIn(p, spec["paths"])
        self.assertIn("Finding", spec["components"]["schemas"])
        self.assertEqual(self.c.get("/docs").status_code, 200)

    def test_degraded_health_returns_503(self):
        self.repo.ping = lambda: False
        r = self.c.get("/api/health")
        self.assertEqual((r.status_code, r.json["status"]), (503, "degraded"))

    def test_unknown_route_and_wrong_method_are_json(self):
        r = self.c.get("/api/nao-existe")
        self.assertEqual((r.status_code, r.is_json), (404, True))
        r = self.c.delete("/api/analyses")
        self.assertEqual((r.status_code, r.is_json), (405, True))


class ImportTests(ApiBase):
    def test_import_csv_xlsx_zip(self):
        r = upload(self.c, "usuarios.csv", b"user_id;status\nu1;ativo\n")
        self.assertEqual((r.status_code, r.json["dataset"]["table_counts"]), (201, {"usuarios": 1}))
        r = upload(self.c, "w.xlsx", make_xlsx({"Usuarios": [["user_id"], ["u1"]], "Aba Estranha": [["a"], [1]]}))
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json["validation"]["unknown_sheets"], ["aba_estranha"])
        self.assertEqual(r.json["import"]["sources"][0]["rows"], 1)
        self.assertEqual(upload(self.c, "d.zip", make_zip({"usuarios.csv": "user_id\nu1\n"})).status_code, 201)

    def test_invalid_uploads_are_400_json(self):
        cases = [("a.txt", b"x"), ("a.xlsx", b"nao eh xlsx"), ("a.zip", b"PK\x03\x04lixo"), ("a.csv", b""),
                 ("a.zip", make_zip({"../x.csv": "a\n1\n"})), ("a.csv", b"\x00\x01bin")]
        for name, data in cases:
            r = upload(self.c, name, data)
            self.assertEqual(r.status_code, 400, name)
            self.assertIn("error", r.json)
        self.assertEqual(self.c.post("/api/datasets/import").status_code, 400)
        self.assertEqual(self.c.get("/api/datasets").json, [])  # nada persistiu

    def test_filename_is_sanitized_and_path_stripped(self):
        r = upload(self.c, "../../etc/usuarios.csv", b"user_id\nu1\n")
        self.assertEqual(r.json["dataset"]["name"], "usuarios.csv")

    def test_upload_too_large_is_413_json(self):
        app = create_app(MemoryRepository(), Settings(database_url="memory", max_upload_mb=1))
        r = upload(app.test_client(), "a.csv", b"a\n" + b"1\n" * (600 * 1024))
        self.assertEqual((r.status_code, r.is_json), (413, True))

    def test_datasets_list_and_detail(self):
        did = self.dataset_with_finding()
        self.assertEqual(self.c.get("/api/datasets").json[0]["id"], did)
        d = self.c.get(f"/api/datasets/{did}").json
        self.assertTrue(d["validation"]["valid"])
        self.assertNotIn("tables", d["dataset"])
        self.assertEqual(self.c.get("/api/datasets/999").status_code, 404)

    def test_validate_endpoint(self):
        self.assertEqual(self.c.post("/api/datasets/validate", json={"tables": {"usuarios": "x"}}).json["valid"], False)
        self.assertEqual(self.c.post("/api/datasets/validate", json={"tables": {"usuarios": [{"user_id": 1}]}}).json["valid"], True)
        for body in ({}, {"tables": []}, []):
            self.assertEqual(self.c.post("/api/datasets/validate", json=body).status_code, 400)
        self.assertEqual(self.c.post("/api/datasets/validate", data="{ruim", content_type="application/json").status_code, 400)


class AnalysisTests(ApiBase):
    def test_full_flow_history_filters_detail_export(self):
        did = self.dataset_with_finding()
        r = self.c.post("/api/analyses", json={"dataset_id": did, "reference_date": "2026-11-19"})
        self.assertEqual(r.status_code, 201, r.json)
        a = r.json
        self.assertEqual((a["id"], a["analysis_id"], a["reference_date"]), (1, 1, "2026-11-19"))
        self.assertEqual(a["summary"]["total"], 2)
        self.assertEqual(a["summary"]["by_rule"]["R01"], 1)
        self.assertTrue(a["coverage"]["R01"]["evaluated"])
        self.assertFalse(a["coverage"]["R02"]["evaluated"])
        self.assertEqual(self.c.get("/api/analyses").json[0]["summary"]["total"], 2)
        self.assertNotIn("findings", self.c.get("/api/analyses").json[0])
        self.assertEqual(len(self.c.get("/api/analyses/1").json["findings"]), 2)
        r = self.c.get("/api/findings?rule_id=r09&severity=medium&analysis_id=1")
        self.assertEqual((len(r.json), r.headers["X-Total-Count"], r.json[0]["rule_id"]), (1, "1", "R09"))
        self.assertEqual(len(self.c.get("/api/findings?q=u001").json), 2)
        self.assertEqual(r.json[0]["finding_type"], "Revisao_Vencida")
        self.assertEqual(self.c.get("/api/findings?limit=1&offset=1").headers["X-Total-Count"], "2")
        fid = r.json[0]["id"]
        self.assertEqual(self.c.get(f"/api/findings/{fid}").json["source_sheet"], "revisoes_acesso")
        ind = self.c.get("/api/indicators").json
        self.assertEqual((ind["analyses_count"], ind["latest"]["total"]), (1, 2))

    def test_reanalysis_keeps_history(self):
        did = self.dataset_with_finding()
        self.c.post("/api/analyses", json={"dataset_id": did})
        self.c.post("/api/analyses", json={"dataset_id": did})
        self.assertEqual([x["id"] for x in self.c.get("/api/analyses").json], [2, 1])

    def test_reference_date_changes_exception_outcome(self):
        tables = {"rbac_baseline": [{"role_id": "R01", "resource_id": "RES01", "allowed_permission": "Read"}],
                  "atribuicoes_papeis": [{"user_id": "U001", "role_id": "R01", "start_date": "2024-01-01", "end_date": None}],
                  "permissoes_atuais": [{"principal_id": "U001", "principal_type": "Usuario", "resource_id": "RES01", "permission": "Write"}],
                  "excecoes": [{"subject_id": "U001", "resource_or_asset_id": "RES01", "approved_by": "U002", "status": "Ativa",
                                "expiration_date": "2026-06-30"}]}
        did = self.repo.add_dataset("x", tables)["id"]
        before = self.c.post("/api/analyses", json={"dataset_id": did, "reference_date": "2026-06-01"}).json
        after = self.c.post("/api/analyses", json={"dataset_id": did, "reference_date": "2026-07-01"}).json
        self.assertEqual((before["findings"][0]["status"], after["findings"][0]["exception_status"]), ("valid_exception", "expired"))

    def test_bad_inputs(self):
        for body, code in (({}, 400), ({"dataset_id": "1"}, 400), ({"dataset_id": True}, 400), ({"dataset_id": 0}, 400),
                           ({"dataset_id": [1]}, 400), ({"dataset_id": 999}, 404), ({"dataset_id": 1, "reference_date": "ontem"}, 400)):
            self.assertEqual(self.c.post("/api/analyses", json=body).status_code, code, body)
        self.assertEqual(self.c.post("/api/analyses", json=[1]).status_code, 400)
        self.assertEqual(self.c.post("/api/analyses", data="x", content_type="text/plain").status_code, 400)
        self.assertEqual(self.c.get("/api/analyses/999").status_code, 404)
        self.assertEqual(self.c.get("/api/analyses/999/export").status_code, 404)
        self.assertEqual(self.c.get("/api/findings/999").status_code, 404)

    def test_structurally_invalid_dataset_is_422(self):
        did = self.repo.add_dataset("bad", {"usuarios": "nao-lista"})["id"]
        r = self.c.post("/api/analyses", json={"dataset_id": did})
        self.assertEqual(r.status_code, 422)
        self.assertFalse(r.json["validation"]["valid"])

    def test_invalid_filters_are_400(self):
        for q in ("analysis_id=abc", "analysis_id=0", "rule_id=R99", "severity=bad", "status=x", "exception_status=y", "limit=0", "limit=5000", "offset=-1"):
            self.assertEqual(self.c.get(f"/api/findings?{q}").status_code, 400, q)

    def test_indicators_empty_has_stable_shape(self):
        ind = self.c.get("/api/indicators").json
        self.assertEqual((ind["analyses_count"], ind["latest_analysis_id"], ind["latest"]["total"]), (0, None, 0))
        self.assertIn("by_status", ind["latest"])


class ExportTests(ApiBase):
    def test_json_and_csv_exports_and_formula_injection(self):
        tables = {"ativos_dados": [{"data_asset_id": "=HYPERLINK(\"http://x\")", "__row": 2},
                                   {"data_asset_id": "+cmd", "classification": "Interno", "owner_id": "U1"}]}
        did = self.repo.add_dataset("x", tables)["id"]
        self.c.post("/api/analyses", json={"dataset_id": did})
        j = self.c.get("/api/analyses/1/export?format=json")
        self.assertIn("attachment", j.headers["Content-Disposition"])
        self.assertEqual(len(json.loads(j.data)["findings"]), 2)
        csv_text = self.c.get("/api/analyses/1/export?format=csv").data.decode("utf-8-sig")
        import csv as _csv
        rows = list(_csv.reader(io.StringIO(csv_text)))
        self.assertEqual(rows[0][:3], ["id", "analysis_id", "rule_id"])
        col = rows[0].index("object_ref")
        self.assertTrue(all(not r[col].startswith(("=", "+", "@")) for r in rows[1:]))
        self.assertIn("'=HYPERLINK", csv_text)
        self.assertEqual(self.c.get("/api/analyses/1/export?format=xml").status_code, 400)


class SecurityConfigTests(unittest.TestCase):
    def test_api_key_required_when_configured(self):
        c = create_app(MemoryRepository(), Settings(database_url="m", api_key="segredo")).test_client()
        self.assertEqual(c.get("/api/health").status_code, 200)
        self.assertEqual(c.get("/openapi.json").status_code, 200)
        self.assertEqual(c.get("/api/analyses").status_code, 401)
        self.assertEqual(c.get("/api/analyses", headers={"X-API-Key": "errada"}).status_code, 401)
        self.assertEqual(c.get("/api/analyses", headers={"X-API-Key": "segredo"}).status_code, 200)

    def test_cors_disabled_by_default_and_enabled_for_listed_origin(self):
        off = create_app(MemoryRepository(), Settings(database_url="m")).test_client()
        self.assertNotIn("Access-Control-Allow-Origin", off.get("/api/health", headers={"Origin": "http://localhost:5173"}).headers)
        on = create_app(MemoryRepository(), Settings(database_url="m", cors_origins=("http://localhost:5173",))).test_client()
        r = on.get("/api/health", headers={"Origin": "http://localhost:5173"})
        self.assertEqual(r.headers["Access-Control-Allow-Origin"], "http://localhost:5173")
        self.assertNotIn("Access-Control-Allow-Origin", on.get("/api/health", headers={"Origin": "http://evil.example"}).headers)
        pre = on.open("/api/analyses", method="OPTIONS", headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"})
        self.assertIn("POST", pre.headers["Access-Control-Allow-Methods"])

    def test_unexpected_error_is_json_without_leaking_details(self):
        repo = MemoryRepository()
        app = create_app(repo, Settings(database_url="m"))
        repo.list_datasets = lambda: (_ for _ in ()).throw(RuntimeError("segredo interno"))
        app.config["PROPAGATE_EXCEPTIONS"] = False
        with self.assertLogs("pdbank", level="ERROR"):
            r = app.test_client().get("/api/datasets")
        self.assertEqual((r.status_code, r.json), (500, {"error": "Erro interno do servidor."}))


if __name__ == "__main__":
    unittest.main()
