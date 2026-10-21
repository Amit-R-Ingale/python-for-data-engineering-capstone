import unittest

from participants import (
    BookingError,
    ElderlyParticipant,
    GeneralParticipant,
    HealthcareWorker,
    Participant,
    create_participant,
)


class ParticipantTests(unittest.TestCase):
    def test_factory_picks_subclass_for_each_group(self):
        self.assertIsInstance(
            create_participant("Ana", "35", "healthcare", "morning"), HealthcareWorker)
        self.assertIsInstance(
            create_participant("Ben", "70", "Elderly", "afternoon"), ElderlyParticipant)
        self.assertIsInstance(
            create_participant("Cy", "25", "GENERAL", "morning"), GeneralParticipant)

    def test_subclasses_inherit_from_participant(self):
        p = create_participant("Ana", "35", "healthcare", "morning")
        self.assertIsInstance(p, Participant)

    def test_fields_are_cleaned(self):
        p = create_participant("  Ana Diaz ", " 35 ", "healthcare", " Morning ", " gp")
        self.assertEqual(p.name, "Ana Diaz")
        self.assertEqual(p.age, 35)
        self.assertEqual(p.session, "morning")
        self.assertEqual(p.voucher, "GP")

    def test_unknown_group_rejected(self):
        with self.assertRaises(BookingError) as ctx:
            create_participant("Ana", "35", "vip", "morning")
        self.assertIn("unknown group", str(ctx.exception))

    def test_unknown_session_rejected(self):
        with self.assertRaises(BookingError) as ctx:
            create_participant("Ana", "35", "general", "evening")
        self.assertIn("unknown session", str(ctx.exception))

    def test_non_numeric_age_rejected(self):
        with self.assertRaises(BookingError) as ctx:
            create_participant("Ana", "thirty", "general", "morning")
        self.assertIn("whole number", str(ctx.exception))

    def test_out_of_range_age_rejected(self):
        with self.assertRaises(BookingError):
            create_participant("Ana", "130", "general", "morning")
        with self.assertRaises(BookingError):
            create_participant("Ana", "-1", "general", "morning")

    def test_empty_name_rejected(self):
        with self.assertRaises(BookingError):
            create_participant("   ", "30", "general", "morning")

    def test_elderly_must_be_sixty_or_over(self):
        with self.assertRaises(BookingError) as ctx:
            create_participant("Dee", "59", "elderly", "morning")
        self.assertIn("60", str(ctx.exception))
        self.assertEqual(create_participant("Dee", "60", "elderly", "morning").age, 60)

    def test_seating_key_orders_priority_then_age(self):
        people = [
            create_participant("Gen Old", "80", "general", "morning"),
            create_participant("Eld Young", "61", "elderly", "morning"),
            create_participant("Health", "30", "healthcare", "morning"),
            create_participant("Eld Old", "90", "elderly", "morning"),
        ]
        ordered = [p.name for p in sorted(people, key=lambda p: p.seating_key())]
        self.assertEqual(ordered, ["Health", "Eld Old", "Eld Young", "Gen Old"])

    def test_fee_uses_voucher(self):
        self.assertEqual(create_participant("A", "30", "general", "morning", "GP").fee_cents(), 1800)
        self.assertEqual(create_participant("B", "30", "general", "morning", "").fee_cents(), 2000)


if __name__ == "__main__":
    unittest.main()