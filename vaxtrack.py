"""VaxTrack - vaccination drive appointment manager (console entry point).

Give a command file name as the first argument, or pipe the commands
into standard input. Bookings are kept in vaxtrack.db in the folder
you run the program from.
"""

import os
import sys

from database import BookingDatabase
from manager import BookingManager

DB_FILE = os.path.join(os.getcwd(), "vaxtrack.db")


def run(lines, manager, out=print):
    """Process each command line; skip blanks and # comments."""
    handled = 0
    for raw in lines:
        line = raw.replace("\ufeff", "").strip()
        if line == "" or line.startswith("#"):
            continue
        out(f"> {line}")
        out(manager.handle(line))
        handled += 1
    return handled


def main(argv):
    manager = BookingManager(BookingDatabase(DB_FILE))
    print(f"VaxTrack loaded {len(manager.bookings)} existing bookings")
    if len(argv) > 1:
        try:
            with open(argv[1], encoding="utf-8-sig") as f:
                lines = f.readlines()
        except FileNotFoundError:
            print(f"ERROR: command file '{argv[1]}' not found")
            return 1
    else:
        lines = sys.stdin
    run(lines, manager)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))