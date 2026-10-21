"""SQLite persistence for VaxTrack.

Every method opens its own connection and closes it again, so the
database file is never left locked (important on Windows).
"""

import sqlite3

from participants import create_participant

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS bookings (
    name    TEXT PRIMARY KEY COLLATE NOCASE,
    age     INTEGER NOT NULL,
    grp     TEXT NOT NULL,
    session TEXT NOT NULL,
    voucher TEXT NOT NULL DEFAULT ''
)
"""


class BookingDatabase:
    def __init__(self, path):
        self.path = path
        conn = sqlite3.connect(self.path)
        try:
            conn.execute(CREATE_TABLE)
            conn.commit()
        finally:
            conn.close()

    def load_all(self):
        """Return every stored booking as a Participant object."""
        conn = sqlite3.connect(self.path)
        try:
            rows = conn.execute(
                "SELECT name, age, grp, session, voucher FROM bookings ORDER BY rowid"
            ).fetchall()
        finally:
            conn.close()
        return [create_participant(*row) for row in rows]

    def add(self, participant):
        conn = sqlite3.connect(self.path)
        try:
            conn.execute(
                "INSERT INTO bookings (name, age, grp, session, voucher) "
                "VALUES (?, ?, ?, ?, ?)",
                (participant.name, participant.age, participant.group,
                 participant.session, participant.voucher),
            )
            conn.commit()
        finally:
            conn.close()

    def remove(self, name):
        """Delete a booking by name. Return True if a row was deleted."""
        conn = sqlite3.connect(self.path)
        try:
            cursor = conn.execute("DELETE FROM bookings WHERE name = ?", (name,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()