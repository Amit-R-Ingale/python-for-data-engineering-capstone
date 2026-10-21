"""Fee helper for VaxTrack.

Money is kept in whole cents (integers) so 10% of $20.00 is exactly
1800 cents, with no floating point rounding surprises.
"""

BASE_FEE_CENTS = 2000          # $20.00 administration fee
DISCOUNT_VOUCHER = "GP"        # the only voucher that gives a discount
DISCOUNT_PERCENT = 10


def normalise_voucher(code):
    """Return the voucher in upper case with spaces removed ('' if none)."""
    if code is None:
        return ""
    return code.strip().upper()


def compute_fee_cents(voucher, is_valid=True, base_cents=BASE_FEE_CENTS):
    """Return the fee in cents for one booking.

    A booking that is not valid (rejected or cancelled) owes nothing,
    and the GP discount is only applied to a valid booking.
    """
    if not is_valid:
        return 0
    if normalise_voucher(voucher) == DISCOUNT_VOUCHER:
        return base_cents - base_cents * DISCOUNT_PERCENT // 100
    return base_cents


def cents_to_dollars(cents):
    """Convert cents to a float in dollars, e.g. 1800 -> 18.0."""
    return cents / 100


def format_money(cents):
    """Format cents as a dollar string, e.g. 1800 -> '$18.00'."""
    return f"${cents // 100}.{cents % 100:02d}"