import unittest

from pdbank.repository import MemoryRepository
from tests.contract import RepositoryContract


class MemoryRepositoryTests(RepositoryContract, unittest.TestCase):
    def make_repo(self):
        return MemoryRepository()


if __name__ == "__main__":
    unittest.main()
