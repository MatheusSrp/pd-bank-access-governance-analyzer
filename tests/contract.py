"""Contrato que TODA implementação de Repository precisa cumprir (memória e SQL)."""
FINDING = dict(rule_id="R01", category="Identidade e acesso", severity="high", object_ref="u1", evidence="e", description="d",
               impact="i", recommendation="r", status="non_compliant", exception_status="none", source_sheet="s", source_row=3)


class RepositoryContract:
    def make_repo(self):  # pragma: no cover
        raise NotImplementedError

    def setUp(self):
        self.repo = self.make_repo()
        self.repo.init()

    def test_ping(self):
        self.assertTrue(self.repo.ping())

    def test_dataset_roundtrip_and_list_order(self):
        a = self.repo.add_dataset("a.csv", {"usuarios": [{"user_id": "u1", "__row": 2}]})
        b = self.repo.add_dataset("b.csv", {"x": []})
        self.assertEqual(a["table_counts"], {"usuarios": 1})
        self.assertEqual([d["id"] for d in self.repo.list_datasets()], [b["id"], a["id"]])
        got = self.repo.get_dataset(a["id"])
        self.assertEqual(got["tables"]["usuarios"][0]["user_id"], "u1")
        self.assertIsNone(self.repo.get_dataset(999))

    def test_long_name_is_truncated(self):
        self.assertLessEqual(len(self.repo.add_dataset("n" * 400, {"t": []})["name"]), 255)

    def test_analysis_with_findings_and_filters(self):
        ds = self.repo.add_dataset("a", {"t": []})
        f2 = {**FINDING, "rule_id": "R02", "severity": "medium", "object_ref": "Maria"}
        a = self.repo.add_analysis(ds["id"], "2026-11-19", {"R01": {"evaluated": True}}, {"total": 2}, [FINDING, f2])
        self.assertEqual(len(a["findings"]), 2)
        got = self.repo.get_analysis(a["id"])
        self.assertEqual((got["reference_date"], got["coverage"], got["summary"]), ("2026-11-19", {"R01": {"evaluated": True}}, {"total": 2}))
        self.assertEqual(got["findings"][0]["domain"], "Identidade e acesso")
        self.assertEqual(got["findings"][0]["source_row"], 3)
        items, total = self.repo.list_findings({"rule_id": "R02"}, 10, 0)
        self.assertEqual((total, items[0]["object_ref"]), (1, "Maria"))
        self.assertEqual(self.repo.list_findings({"analysis_id": a["id"]}, 1, 1)[0][0]["rule_id"], "R02")
        self.assertEqual(self.repo.list_findings({}, 10, 0, q="mari")[1], 1)
        self.assertEqual(self.repo.list_findings({"domain": "Identidade e acesso", "severity": "high"}, 10, 0)[1], 1)
        self.assertEqual(self.repo.list_findings({"rule_id": "R09"}, 10, 0), ([], 0))

    def test_history_order_and_missing_ids(self):
        ds = self.repo.add_dataset("a", {"t": []})
        a1 = self.repo.add_analysis(ds["id"], "2026-01-01", {}, {}, [])
        a2 = self.repo.add_analysis(ds["id"], "2026-01-02", {}, {}, [])
        self.assertEqual([a["id"] for a in self.repo.list_analyses()], [a2["id"], a1["id"]])
        self.assertNotIn("findings", self.repo.list_analyses()[0])
        self.assertIsNone(self.repo.get_analysis(999))
        self.assertIsNone(self.repo.get_finding(999))

    def test_overlong_object_ref_does_not_break(self):
        ds = self.repo.add_dataset("a", {"t": []})
        a = self.repo.add_analysis(ds["id"], "2026-01-01", {}, {}, [{**FINDING, "object_ref": "x" * 600}])
        self.assertLessEqual(len(self.repo.get_analysis(a["id"])["findings"][0]["object_ref"]), 600)
