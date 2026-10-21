import os
import sqlite3
import tempfile
import unittest

from database import BookingDatabase
from participants import create_participant


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "test.db")
        self.db = BookingDatabase(self.path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_new_database_is_empty(self):
        self.assertEqual(self.db.load_all(), [])

    def test_add_then_load_rebuilds_subclass(self):
        self.db.add(create_participant("Ana", "35", "healthcare", "morning", "GP"))
        loaded = self.db.load_all()
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].name, "Ana")
        self.assertEqual(loaded[0].group, "healthcare")
        self.assertEqual(loaded[0].voucher, "GP")
        self.assertEqual(loaded[0].fee_cents(), 1800)

    def test_data_survives_a_new_connection(self):
        self.db.add(create_participant("Ben", "70", "elderly", "afternoon"))
        reopened = BookingDatabase(self.path)
        self.assertEqual([p.name for p in reopened.load_all()], ["Ben"])

    def test_remove(self):
        self.db.add(create_participant("Ana", "35", "general", "morning"))
        self.assertTrue(self.db.remove("Ana"))
        self.assertFalse(self.db.remove("Ana"))
        self.assertEqual(self.db.load_all(), [])

    def test_names_are_unique_ignoring_case(self):
        self.db.add(create_participant("Ana", "35", "general", "morning"))
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.add(create_participant("ANA", "40", "general", "afternoon"))


if __name__ == "__main__":
    unittest.main()