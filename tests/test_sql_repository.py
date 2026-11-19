"""Roda o MESMO contrato contra SQLite real via SQLAlchemy (e, opcionalmente, PostgreSQL).

Pula automaticamente se SQLAlchemy não estiver instalado. PostgreSQL: defina TEST_POSTGRES_URL
(ex.: postgresql+psycopg://pd_bank:senha@localhost:5432/pd_bank_test) — use um banco de teste, as tabelas são criadas.
"""
import importlib.util
import os
import sqlite3
import tempfile
import unittest

from tests.contract import RepositoryContract

HAS_SA = importlib.util.find_spec("sqlalchemy") is not None


@unittest.skipUnless(HAS_SA, "SQLAlchemy não instalado")
class SqliteRepositoryTests(RepositoryContract, unittest.TestCase):
    def make_repo(self):
        from pdbank.sql_repository import SqlRepository
        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)
        return SqlRepository(f"sqlite:///{self._dir.name}/t.db")

    def test_migrates_v02_database_in_place(self):
        """Banco criado pela versão anterior (sem colunas novas) deve ser migrado sem perder dados."""
        from pdbank.sql_repository import SqlRepository
        path = os.path.join(self._dir.name, "old.db")
        con = sqlite3.connect(path)
        con.executescript("""
            CREATE TABLE datasets (id INTEGER PRIMARY KEY, name VARCHAR(255), created_at DATETIME, content TEXT);
            CREATE TABLE analyses (id INTEGER PRIMARY KEY, dataset_id INTEGER, created_at DATETIME, status VARCHAR(40));
            CREATE TABLE findings (id INTEGER PRIMARY KEY, analysis_id INTEGER, rule_id VARCHAR(8), category VARCHAR(80),
              severity VARCHAR(20), object_ref VARCHAR(255), evidence TEXT, description TEXT, impact TEXT,
              recommendation TEXT, status VARCHAR(30));
            INSERT INTO datasets VALUES (1,'velho.csv','2026-01-01 00:00:00','{"t": []}');
            INSERT INTO analyses VALUES (1,1,'2026-01-01 00:00:00','completed');
            INSERT INTO findings VALUES (1,1,'R01','c','high','u1','e','d','i','r','non_compliant');
        """)
        con.commit(); con.close()
        repo = SqlRepository(f"sqlite:///{path}")
        repo.init()
        a = repo.get_analysis(1)
        self.assertEqual(a["findings"][0]["exception_status"], "none")
        self.assertIsNone(a["reference_date"])
        self.assertIsNone(a["findings"][0]["source_row"])
        self.assertEqual(repo.get_dataset(1)["tables"], {"t": []})


@unittest.skipUnless(HAS_SA and os.environ.get("TEST_POSTGRES_URL"), "defina TEST_POSTGRES_URL para testar PostgreSQL")
class PostgresRepositoryTests(RepositoryContract, unittest.TestCase):
    def make_repo(self):
        from pdbank.sql_repository import SqlRepository
        return SqlRepository(os.environ["TEST_POSTGRES_URL"])


if __name__ == "__main__":
    unittest.main()
