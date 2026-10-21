"""Booking rules and command handling for VaxTrack."""

import json

from fees import BASE_FEE_CENTS, cents_to_dollars, format_money
from participants import SESSIONS, BookingError, create_participant

HALL_CAPACITY = 4              # seats per session in the hall
DEFAULT_EXPORT_FILE = "bookings.json"


class BookingManager:
    def __init__(self, database, capacity=HALL_CAPACITY):
        self.database = database
        self.capacity = capacity
        self.bookings = database.load_all()

    # ----- queries -------------------------------------------------
    def find(self, name):
        wanted = name.strip().lower()
        for participant in self.bookings:
            if participant.name.lower() == wanted:
                return participant
        return None

    def count(self, session):
        return len([p for p in self.bookings if p.session == session])

    def seating_order(self, session):
        in_session = [p for p in self.bookings if p.session == session]
        return sorted(in_session, key=lambda p: p.seating_key())

    # ----- commands ------------------------------------------------
    def book(self, name, age, group, session, voucher=""):
        participant = create_participant(name, age, group, session, voucher)
        if self.find(participant.name) is not None:
            raise BookingError(f"'{participant.name}' is already booked")
        booked = self.count(participant.session)
        if booked >= self.capacity:
            raise BookingError(
                f"{participant.session} session is full ({booked}/{self.capacity})"
            )
        self.database.add(participant)
        self.bookings.append(participant)
        return participant

    def cancel(self, name):
        participant = self.find(name)
        if participant is None:
            raise BookingError(f"no booking found for '{name.strip()}'")
        self.database.remove(participant.name)
        self.bookings.remove(participant)
        return participant

    def report(self):
        lines = ["=== VaxTrack Report ==="]
        total_cents = 0
        for session, hours in SESSIONS.items():
            lines.append(
                f"{session.capitalize()} ({hours}): "
                f"{self.count(session)}/{self.capacity} booked"
            )
            seated = self.seating_order(session)
            if not seated:
                lines.append("  (no bookings)")
            for seat, p in enumerate(seated, start=1):
                fee = p.fee_cents()
                total_cents += fee
                lines.append(
                    f"  {seat}. {p.name:<16} {p.group:<10} age {p.age:>3}  "
                    f"fee {format_money(fee)}"
                )
        lines.append(f"Total fees due: {format_money(total_cents)}")
        return "\n".join(lines)

    def export_records(self):
        records = []
        for session in SESSIONS:
            for seat, p in enumerate(self.seating_order(session), start=1):
                record = p.to_dict()
                record["seat"] = seat
                record["fee"] = cents_to_dollars(p.fee_cents())
                records.append(record)
        return records

    def export(self, path=DEFAULT_EXPORT_FILE):
        data = {
            "capacity_per_session": self.capacity,
            "base_fee": cents_to_dollars(BASE_FEE_CENTS),
            "bookings": self.export_records(),
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return len(data["bookings"])

    # ----- text interface ------------------------------------------
    def handle(self, line):
        """Run one pipe-delimited command and return the message to print."""
        parts = [part.strip() for part in line.strip().split("|")]
        command = parts[0].upper()
        args = parts[1:]
        try:
            if command == "BOOK":
                if len(args) != 5:
                    raise BookingError(
                        "BOOK needs 5 fields: BOOK|name|age|group|session|voucher"
                    )
                p = self.book(*args)
                return (f"BOOKED: {p.name} ({p.group}, {p.session}) "
                        f"fee {format_money(p.fee_cents())}")
            if command == "CANCEL":
                if len(args) != 1:
                    raise BookingError("CANCEL needs 1 field: CANCEL|name")
                p = self.cancel(args[0])
                return f"CANCELLED: {p.name} ({p.session})"
            if command == "REPORT":
                return self.report()
            if command == "EXPORT":
                path = args[0] if args and args[0] else DEFAULT_EXPORT_FILE
                count = self.export(path)
                return f"EXPORTED: {count} bookings to {path}"
            raise BookingError(f"unknown command '{parts[0]}'")
        except BookingError as error:
            return f"REJECTED: {error}"
        except OSError as error:
            return f"ERROR: could not write file ({error.strerror})"