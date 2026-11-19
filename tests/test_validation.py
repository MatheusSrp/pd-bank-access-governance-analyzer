import unittest

from pdbank.validation import validate_data


class ValidationTests(unittest.TestCase):
    def test_recognizes_official_and_unknown_sheets(self):
        v = validate_data({"usuarios": [{"user_id": "u1"}], "abc": [{"x": 1}]})
        self.assertTrue(v["valid"])
        self.assertEqual(v["unknown_sheets"], ["abc"])
        self.assertEqual(v["recognized_sheets"][0]["canonical_name"], "users")

    def test_non_list_and_non_dict_rows_are_errors(self):
        v = validate_data({"usuarios": "x", "recursos": [1, {"a": 1}]})
        self.assertFalse(v["valid"])
        self.assertEqual((v["records_total"], v["records_rejected"], v["records_accepted"]), (2, 1, 1))

    def test_warns_when_no_known_sheet_and_when_columns_unrecognized(self):
        self.assertTrue(any("Nenhuma aba conhecida" in w for w in validate_data({"zzz": [{"a": 1}]})["warnings"]))
        w = validate_data({"permissoes_atuais": [{"coluna_x": 1}]})["warnings"]
        self.assertTrue(any("nenhuma coluna reconhecida para subject_id" in x for x in w))

    def test_import_warnings_are_carried_and_dup_suffix_recognized(self):
        v = validate_data({"usuarios__2": [{"user_id": "1"}]}, ["aviso do import"])
        self.assertIn("aviso do import", v["warnings"])
        self.assertEqual(v["unknown_sheets"], [])

    def test_r01_r02_dependency_warnings(self):
        w = validate_data({"usuarios": [{"user_id": "u"}]})["warnings"]
        self.assertTrue(any("R01" in x for x in w) and any("R02" in x for x in w))


if __name__ == "__main__":
    unittest.main()
