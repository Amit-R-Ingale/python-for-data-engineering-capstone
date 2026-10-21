import unittest

from fees import compute_fee_cents, format_money, cents_to_dollars, normalise_voucher


class FeeTests(unittest.TestCase):
    def test_no_voucher_pays_full_fee(self):
        self.assertEqual(compute_fee_cents(""), 2000)

    def test_gp_voucher_gives_ten_percent_off(self):
        self.assertEqual(compute_fee_cents("GP"), 1800)

    def test_gp_voucher_is_case_and_space_insensitive(self):
        self.assertEqual(compute_fee_cents(" gp "), 1800)

    def test_other_voucher_gives_no_discount(self):
        self.assertEqual(compute_fee_cents("SAVE50"), 2000)

    def test_invalid_booking_owes_nothing_even_with_gp(self):
        self.assertEqual(compute_fee_cents("GP", is_valid=False), 0)

    def test_custom_base_fee(self):
        self.assertEqual(compute_fee_cents("GP", base_cents=1550), 1395)

    def test_format_money(self):
        self.assertEqual(format_money(1800), "$18.00")
        self.assertEqual(format_money(5), "$0.05")
        self.assertEqual(format_money(0), "$0.00")

    def test_cents_to_dollars(self):
        self.assertEqual(cents_to_dollars(1800), 18.0)

    def test_normalise_none_voucher(self):
        self.assertEqual(normalise_voucher(None), "")


if __name__ == "__main__":
    unittest.main()