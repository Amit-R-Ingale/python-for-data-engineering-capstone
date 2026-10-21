"""Participant classes for VaxTrack.

Each priority group is a subclass of Participant. The subclass sets its
own priority rank (lower = seated first) and can add its own rules.
"""

from fees import compute_fee_cents, normalise_voucher

SESSIONS = {
    "morning": "09:00-12:00",
    "afternoon": "13:00-16:00",
}


class BookingError(Exception):
    """Raised when a booking or command cannot be accepted."""


class Participant:
    group = "participant"
    priority_rank = 99

    def __init__(self, name, age, session, voucher=""):
        self.name = name.strip()
        self.age = age
        self.session = session.strip().lower()
        self.voucher = normalise_voucher(voucher)
        self.validate()

    def validate(self):
        if self.name == "":
            raise BookingError("name must not be empty")
        if "|" in self.name:
            raise BookingError("name must not contain '|'")
        if not isinstance(self.age, int) or self.age < 0 or self.age > 120:
            raise BookingError(f"age must be a whole number from 0 to 120, got {self.age!r}")
        if self.session not in SESSIONS:
            raise BookingError(
                f"unknown session '{self.session}' (use morning or afternoon)"
            )

    def fee_cents(self):
        return compute_fee_cents(self.voucher, is_valid=True)

    def seating_key(self):
        """Sort key: priority group first, then oldest first, then name."""
        return (self.priority_rank, -self.age, self.name.lower())

    def to_dict(self):
        return {
            "name": self.name,
            "age": self.age,
            "group": self.group,
            "session": self.session,
            "voucher": self.voucher,
        }

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name!r}, {self.age}, {self.session!r})"


class HealthcareWorker(Participant):
    group = "healthcare"
    priority_rank = 0


class ElderlyParticipant(Participant):
    group = "elderly"
    priority_rank = 1
    MIN_AGE = 60

    def validate(self):
        super().validate()
        if self.age < self.MIN_AGE:
            raise BookingError(
                f"elderly group requires age {self.MIN_AGE} or over, got {self.age}"
            )


class GeneralParticipant(Participant):
    group = "general"
    priority_rank = 2


GROUP_CLASSES = {
    "healthcare": HealthcareWorker,
    "elderly": ElderlyParticipant,
    "general": GeneralParticipant,
}


def parse_age(text):
    """Turn the age text into an int, or raise BookingError."""
    try:
        return int(str(text).strip())
    except ValueError:
        raise BookingError(f"age must be a whole number, got '{text}'")


def create_participant(name, age, group, session, voucher=""):
    """Build the right subclass for the group, validating everything."""
    key = str(group).strip().lower()
    if key not in GROUP_CLASSES:
        raise BookingError(
            f"unknown group '{group}' (use healthcare, elderly or general)"
        )
    participant_class = GROUP_CLASSES[key]
    return participant_class(name, parse_age(age), session, voucher)