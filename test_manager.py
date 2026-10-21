import json
import os
import tempfile
import unittest

from database import BookingDatabase
from manager import BookingManager
from vaxtrack import run


class ManagerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "test.db")
        self.manager = BookingManager(BookingDatabase(self.db_path), capacity=3)

    def tearDown(self):
        self.tmp.cleanup()

    def test_valid_booking_is_accepted_and_stored(self):
        msg = self.manager.handle("BOOK|Ana|35|healthcare|morning|GP")
        self.assertEqual(msg, "BOOKED: Ana (healthcare, morning) fee $18.00")
        self.assertEqual(self.manager.count("morning"), 1)

    def test_duplicate_name_rejected_ignoring_case(self):
        self.manager.handle("BOOK|Ana|35|healthcare|morning|")
        msg = self.manager.handle("BOOK|ana|40|general|afternoon|")
        self.assertEqual(msg, "REJECTED: 'ana' is already booked")
        self.assertEqual(len(self.manager.bookings), 1)

    def test_overbooking_rejected(self):
        for name in ["A", "B", "C"]:
            self.manager.handle(f"BOOK|{name}|30|general|morning|")
        msg = self.manager.handle("BOOK|D|30|general|morning|")
        self.assertEqual(msg, "REJECTED: morning session is full (3/3)")
        self.assertEqual(self.manager.count("morning"), 3)

    def test_full_morning_does_not_block_afternoon(self):
        for name in ["A", "B", "C"]:
            self.manager.handle(f"BOOK|{name}|30|general|morning|")
        msg = self.manager.handle("BOOK|D|30|general|afternoon|")
        self.assertTrue(msg.startswith("BOOKED"))

    def test_cancel_frees_a_seat(self):
        for name in ["A", "B", "C"]:
            self.manager.handle(f"BOOK|{name}|30|general|morning|")
        self.assertEqual(self.manager.handle("CANCEL|b"), "CANCELLED: B (morning)")
        self.assertTrue(self.manager.handle("BOOK|D|30|general|morning|").startswith("BOOKED"))

    def test_cancel_unknown_name(self):
        self.assertEqual(self.manager.handle("CANCEL|Nobody"),
                         "REJECTED: no booking found for 'Nobody'")

    def test_bad_input_messages(self):
        self.assertIn("BOOK needs 5 fields", self.manager.handle("BOOK|Ana|35"))
        self.assertIn("whole number", self.manager.handle("BOOK|Ana|abc|general|morning|"))
        self.assertIn("unknown group", self.manager.handle("BOOK|Ana|35|vip|morning|"))
        self.assertIn("unknown session", self.manager.handle("BOOK|Ana|35|general|night|"))
        self.assertEqual(self.manager.handle("HELLO"), "REJECTED: unknown command 'HELLO'")
        self.assertEqual(self.manager.bookings, [])

    def test_rejected_booking_not_saved_to_database(self):
        self.manager.handle("BOOK|Kid|10|elderly|morning|GP")
        reloaded = BookingManager(BookingDatabase(self.db_path))
        self.assertEqual(reloaded.bookings, [])

    def test_overbooked_person_is_not_saved_to_database(self):
        for name in ["A", "B", "C"]:
            self.manager.handle(f"BOOK|{name}|30|general|morning|")
        self.manager.handle("BOOK|D|30|general|morning|")
        reloaded = BookingManager(BookingDatabase(self.db_path), capacity=3)
        self.assertEqual([p.name for p in reloaded.bookings], ["A", "B", "C"])

    def test_bookings_reload_from_database(self):
        self.manager.handle("BOOK|Ana|35|healthcare|morning|GP")
        self.manager.handle("BOOK|Ben|70|elderly|afternoon|")
        self.manager.handle("CANCEL|Ana")
        reloaded = BookingManager(BookingDatabase(self.db_path))
        self.assertEqual([p.name for p in reloaded.bookings], ["Ben"])
        self.assertIn("already booked", reloaded.handle("BOOK|Ben|71|elderly|morning|"))

    def test_capacity_counts_bookings_loaded_from_database(self):
        for name in ["A", "B", "C"]:
            self.manager.handle(f"BOOK|{name}|30|general|morning|")
        reloaded = BookingManager(BookingDatabase(self.db_path), capacity=3)
        self.assertIn("full", reloaded.handle("BOOK|D|30|general|morning|"))

    def test_seating_order(self):
        self.manager.handle("BOOK|Gina|82|general|morning|")
        self.manager.handle("BOOK|Ed|65|elderly|morning|")
        self.manager.handle("BOOK|Hal|29|healthcare|morning|")
        names = [p.name for p in self.manager.seating_order("morning")]
        self.assertEqual(names, ["Hal", "Ed", "Gina"])

    def test_report_lists_counts_and_seats(self):
        self.manager.handle("BOOK|Gina|82|general|morning|GP")
        self.manager.handle("BOOK|Hal|29|healthcare|morning|")
        report = self.manager.handle("REPORT")
        lines = report.split("\n")
        self.assertEqual(lines[1], "Morning (09:00-12:00): 2/3 booked")
        self.assertTrue(lines[2].startswith("  1. Hal"))
        self.assertTrue(lines[3].startswith("  2. Gina"))
        self.assertIn("Afternoon (13:00-16:00): 0/3 booked", report)
        self.assertIn("(no bookings)", report)
        self.assertEqual(lines[-1], "Total fees due: $38.00")

    def test_export_writes_json_with_discounted_fees(self):
        self.manager.handle("BOOK|Gina|82|general|morning|GP")
        self.manager.handle("BOOK|Ed|65|elderly|afternoon|")
        self.manager.handle("BOOK|Zed|40|general|morning|")
        self.manager.handle("CANCEL|Zed")
        out_path = os.path.join(self.tmp.name, "out.json")
        msg = self.manager.handle(f"EXPORT|{out_path}")
        self.assertEqual(msg, f"EXPORTED: 2 bookings to {out_path}")
        with open(out_path, encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["base_fee"], 20.0)
        self.assertEqual(data["capacity_per_session"], 3)
        by_name = {b["name"]: b for b in data["bookings"]}
        self.assertEqual(set(by_name), {"Gina", "Ed"})
        self.assertEqual(by_name["Gina"]["fee"], 18.0)
        self.assertEqual(by_name["Ed"]["fee"], 20.0)
        self.assertEqual(by_name["Gina"]["seat"], 1)

    def test_run_skips_blank_and_comment_lines_and_handles_crlf(self):
        printed = []
        lines = ["# day one\r\n", "\r\n", "BOOK|Ana|35|healthcare|morning|GP\r\n", "REPORT\r\n"]
        handled = run(lines, self.manager, out=printed.append)
        self.assertEqual(handled, 2)
        self.assertEqual(printed[0], "> BOOK|Ana|35|healthcare|morning|GP")
        self.assertEqual(printed[1], "BOOKED: Ana (healthcare, morning) fee $18.00")
        self.assertEqual(self.manager.find("ana").voucher, "GP")

    def test_run_ignores_byte_order_mark_on_first_line(self):
        printed = []
        run(["\ufeffBOOK|Ana|35|healthcare|morning|\n"], self.manager, out=printed.append)
        self.assertEqual(printed[1], "BOOKED: Ana (healthcare, morning) fee $20.00")


if __name__ == "__main__":
    unittest.main()