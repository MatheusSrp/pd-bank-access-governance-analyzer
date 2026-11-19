import unittest
from datetime import date

from pdbank.schema import FIELD_ALIASES, OFFICIAL_SHEETS, SHEET_ALIASES, ALIAS_TO_CANONICAL, canonical_sheet, get, is_known_sheet
from pdbank.values import normalize, parse_bool, parse_date, parse_number


class ValuesTests(unittest.TestCase):
    def test_parse_bool_portuguese_and_excel_values(self):
        for v in ("Aprovado", "aprovada", "SIM", 1, 1.0, True, "1.0", "Implementado", "Vigente"):
            self.assertIs(parse_bool(v), True, v)
        for v in ("Não", "pendente", 0, 0.0, False, "Reprovado", "Bloqueada"):
            self.assertIs(parse_bool(v), False, v)
        for v in (None, "", "N/A", "-", "parcial", "talvez", 2, float("nan")):
            self.assertIsNone(parse_bool(v), v)

    def test_parse_number(self):
        self.assertEqual(parse_number("12,5"), 12.5)
        self.assertEqual(parse_number(30), 30.0)
        for v in ("abc", "30 dias", True, None, "", float("inf"), "1e5"):
            self.assertIsNone(parse_number(v), v)

    def test_parse_date_iso_br_and_objects(self):
        self.assertEqual(parse_date("2026-11-19"), date(2026, 11, 19))
        self.assertEqual(parse_date("19/11/2026"), date(2026, 11, 19))
        self.assertEqual(parse_date("2026-11-19 10:00:00"), date(2026, 11, 19))
        self.assertEqual(parse_date(date(2026, 1, 2)), date(2026, 1, 2))
        for v in ("31/02/2026", "ontem", "", None, "2026-13-01"):
            self.assertIsNone(parse_date(v), v)

    def test_normalize_accents_and_symbols(self):
        self.assertEqual(normalize("Usuário ID"), "usuario_id")
        self.assertEqual(normalize("  Permissão (Atual) "), "permissao_atual")
        self.assertEqual(normalize("Ñandú"), "nandu")


class SchemaTests(unittest.TestCase):
    def test_field_aliases_are_unique_across_groups(self):
        seen = {}
        for group, names in FIELD_ALIASES.items():
            for n in names:
                self.assertNotIn(n, seen, f"{n} em {seen.get(n)} e {group}")
                seen[n] = group

    def test_sheet_aliases_are_unique_across_keys(self):
        flat = [a for aliases in SHEET_ALIASES.values() for a in aliases]
        self.assertEqual(len(flat), len(set(flat)), "alias de aba repetido entre chaves")

    def test_all_20_official_sheets_are_recognized_distinctly(self):
        keys = [canonical_sheet(s) for s in OFFICIAL_SHEETS]
        self.assertTrue(all(is_known_sheet(s) for s in OFFICIAL_SHEETS))
        self.assertEqual(len(set(keys)), 20, "duas abas oficiais caíram na mesma chave interna")

    def test_get_does_not_cross_contaminate_fields(self):
        # regressão: 'user_id' antes devolvia asset_id/use_case_id por colisão de aliases
        row = {"data_asset_id": "A1", "ai_use_case_id": "C1"}
        self.assertIsNone(get(row, "subject_id"))
        self.assertEqual(get(row, "asset_id"), "A1")
        self.assertEqual(get(row, "case_id"), "C1")
        self.assertEqual(get({"usuario": "u9"}, "subject_id"), "u9")
        self.assertEqual(get({"literal_col": 5}, "literal_col"), 5)


    def test_permission_record_id_and_permission_level_are_different_fields(self):
        # regressão v0.3.0: 'permission_id' (id do registro) e 'permission' (nível) colidiam no mesmo grupo
        row = {"permission_id": "P0001", "permission": "Read"}
        self.assertEqual((get(row, "perm_record_id"), get(row, "permission")), ("P0001", "Read"))
        self.assertEqual(get({"allowed_permission": "Write"}, "permission"), "Write")

    def test_principal_and_user_ids_resolve_to_subject(self):
        self.assertEqual(get({"principal_id": "U001"}, "subject_id"), "U001")
        self.assertEqual(get({"user_id": "U001"}, "subject_id"), "U001")


class OfficialHeadersTests(unittest.TestCase):
    """Todo cabeçalho do dataset oficial tem de ser reconhecido (ou estar marcado como apenas descritivo)."""

    def test_every_official_header_is_known_or_informational(self):
        import os
        from pdbank.importer import import_file
        from pdbank.schema import INFORMATIONAL_FIELDS, _FIELD_TO_GROUP
        path = os.path.join(os.path.dirname(__file__), "data", "PD_Bank_Analyzer_Dataset_Completo_Alunos_1.xlsx")
        if not os.path.exists(path):
            self.skipTest("dataset oficial não encontrado em tests/data")
        with open(path, "rb") as fh:
            tables = import_file("d.xlsx", fh.read()).tables
        unknown = {t: [k for k in rows[0] if not k.startswith("__") and k not in _FIELD_TO_GROUP and k not in INFORMATIONAL_FIELDS]
                   for t, rows in tables.items() if rows}
        self.assertEqual({t: v for t, v in unknown.items() if v}, {})


if __name__ == "__main__":
    unittest.main()
