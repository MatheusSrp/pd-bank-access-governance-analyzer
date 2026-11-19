import io
import unittest
import zipfile

from pdbank.importer import ImportFailure, Limits, check_zip_entry, import_file
from tests.helpers import make_xlsx, make_zip


class CsvTests(unittest.TestCase):
    def test_semicolon_cp1252_and_header_normalization(self):
        raw = "Usuário ID;Permissão\nu1;write\nu2;read\n".encode("cp1252")
        t = import_file("acessos.csv", raw).tables["acessos"]
        self.assertEqual([r["usuario_id"] for r in t], ["u1", "u2"])
        self.assertEqual(t[0]["permissao"], "write")
        self.assertEqual([r["__row"] for r in t], [2, 3])

    def test_utf8_bom_comma_and_blank_cells_become_none(self):
        raw = "\ufeffuser_id,status\nu1,\n".encode("utf-8")
        row = import_file("usuarios.csv", raw).tables["usuarios"][0]
        self.assertIsNone(row["status"])

    def test_binary_and_empty_rejected(self):
        with self.assertRaises(ImportFailure):
            import_file("x.csv", b"\x00\x01\x02binary")
        with self.assertRaises(ImportFailure):
            import_file("x.csv", b"")

    def test_duplicate_headers_warn_and_keep_data(self):
        r = import_file("t.csv", b"id,id\n1,2\n")
        self.assertEqual(r.tables["t"][0]["id"], 1 if False else "1")
        self.assertEqual(r.tables["t"][0]["id_2"], "2")
        self.assertTrue(any("duplicado" in w for w in r.warnings))

    def test_unsupported_formats(self):
        for name in ("a.txt", "a.xls", "a.xlsm", "semextensao"):
            with self.assertRaises(ImportFailure, msg=name):
                import_file(name, b"abc")

    def test_row_limit(self):
        with self.assertRaises(ImportFailure):
            import_file("t.csv", b"a\n1\n2\n3\n", Limits(max_rows_per_sheet=2))


class XlsxTests(unittest.TestCase):
    def test_valid_xlsx_rows_headers_and_row_numbers(self):
        data = make_xlsx({"Ativos de Dados": [["ID do Ativo", "Classificação"], ["db1", "restricted"], [None, None], ["db2", None]]})
        t = import_file("w.xlsx", data).tables["ativos_de_dados"]
        self.assertEqual([r["id_do_ativo"] for r in t], ["db1", "db2"])
        self.assertEqual([r["__row"] for r in t], [2, 4])   # linha em branco preservou a numeração
        self.assertIsNone(t[1]["classificacao"])

    def test_dates_become_iso_strings(self):
        from datetime import datetime
        data = make_xlsx({"s": [["d"], [datetime(2026, 5, 1)]]})
        self.assertEqual(import_file("w.xlsx", data).tables["s"][0]["d"], "2026-05-01")

    def test_not_a_zip_or_fake_xlsx_rejected(self):
        for payload in (b"isto nao e xlsx", b"user_id,x\n1,2\n", make_zip({"a.txt": "x"})):
            with self.assertRaises(ImportFailure):
                import_file("fake.xlsx", payload)

    def test_truncated_xlsx_rejected(self):
        data = make_xlsx({"s": [["a"], [1]]})
        with self.assertRaises(ImportFailure):
            import_file("w.xlsx", data[: len(data) // 2])

    def test_sheet_count_limit(self):
        data = make_xlsx({f"s{i}": [["a"], [1]] for i in range(4)})
        with self.assertRaises(ImportFailure):
            import_file("w.xlsx", data, Limits(max_sheets=2))


class ZipTests(unittest.TestCase):
    def test_valid_zip_with_csv_and_xlsx(self):
        z = make_zip({"usuarios.csv": "user_id,status\nu1,ativo\n", "pasta/x.xlsx": make_xlsx({"Aplicacoes": [["id"], ["a1"]]}),
                      "__MACOSX/._usuarios.csv": "lixo", "leia-me.txt": "oi"})
        r = import_file("d.zip", z)
        self.assertEqual(set(r.tables), {"usuarios", "aplicacoes"})
        self.assertTrue(any("leia-me.txt" in w for w in r.warnings))

    def test_path_traversal_rejected(self):
        for name in ("../evil.csv", "/abs.csv", "a/../../b.csv", "C:/x.csv"):
            with self.assertRaises(ImportFailure, msg=name):
                import_file("d.zip", make_zip({name: "a\n1\n"}))

    def test_zip_bomb_by_declared_ratio_and_real_size(self):
        bomb = make_zip({"big.csv": "a\n" + "0" * (3 * 1024 * 1024)})  # comprime >200:1
        with self.assertRaises(ImportFailure):
            import_file("d.zip", bomb)
        with self.assertRaises(ImportFailure):
            import_file("d.zip", make_zip({"a.csv": "a\n" + "1" * 500}), Limits(max_entry_bytes=100))

    def test_too_many_entries_and_empty_zip(self):
        with self.assertRaises(ImportFailure):
            import_file("d.zip", make_zip({f"{i}.csv": "a\n1\n" for i in range(5)}), Limits(max_zip_entries=3))
        with self.assertRaises(ImportFailure):
            import_file("d.zip", make_zip({"leia.txt": "x"}))

    def test_corrupt_zip_rejected(self):
        with self.assertRaises(ImportFailure):
            import_file("d.zip", b"PK\x03\x04garbage")

    def test_duplicate_sheet_names_do_not_overwrite(self):
        z = make_zip({"a/x.csv": "id\n1\n", "b/x.csv": "id\n2\n"})
        r = import_file("d.zip", z)
        self.assertEqual(set(r.tables), {"x", "x__2"})
        self.assertTrue(any("duplicado" in w for w in r.warnings))

    def test_encrypted_and_symlink_entries(self):
        enc = zipfile.ZipInfo("a.csv"); enc.flag_bits = 0x1
        with self.assertRaises(ImportFailure):
            check_zip_entry(enc, Limits())
        link = zipfile.ZipInfo("l.csv"); link.external_attr = (0o120777 << 16)
        self.assertEqual(check_zip_entry(link, Limits()), "link simbólico")


if __name__ == "__main__":
    unittest.main()
