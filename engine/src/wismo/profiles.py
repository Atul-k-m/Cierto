"""Per-vertical thresholds. Parcel clocks run in hours and days; quick commerce in minutes.

Values are starting points taken from the research (Smytten FAQ, E-Commerce Rules 2020,
RBI TAT circular, Swiggy/Instamart policies), meant to be tuned per tenant.
"""
from dataclasses import dataclass
from datetime import timedelta


@dataclass(frozen=True)
class Profile:
    name: str
    stall_after: timedelta            # no carrier scan for this long while moving
    pickup_within: timedelta          # packed but never picked up
    ofd_max: timedelta                # out for delivery with no outcome
    report_window: timedelta          # customer can dispute a "delivered" this long after the claim
    support_ack: timedelta            # E-Commerce Rules 2020: acknowledge within 48 hours
    resolution: timedelta             # E-Commerce Rules 2020: redress within one month
    refund_start_within: timedelta    # cancelled / returned prepaid order must start a refund
    refund_working_days: int          # merchant's refund promise once initiated
    order_after_payment: timedelta    # payment captured but no order created
    rbi_reversal: timedelta           # RBI TAT: failed merchant transaction reversed by T+5
    repeat_contact_window: timedelta
    late_data_grace: timedelta        # carrier pushes arrive late; wait this long before calling a deadline missed
    rider_stall_after: timedelta      # rider pings keep coming from the same spot for this long: stopped
    fresh_for: timedelta              # when answering a shopper, tracking data older than this is called out as stale
    address_mismatch_m: int           # map pin this far from the typed address: ask the customer to confirm the spot


PARCEL = Profile(
    name="parcel",
    stall_after=timedelta(hours=72),
    pickup_within=timedelta(hours=48),
    ofd_max=timedelta(hours=24),
    report_window=timedelta(hours=48),        # Smytten FAQ: 48 working hours for "delivered without code verification"
    support_ack=timedelta(hours=48),
    resolution=timedelta(days=30),
    refund_start_within=timedelta(hours=48),
    refund_working_days=7,                    # Smytten FAQ: 5-7 working days after processing
    order_after_payment=timedelta(minutes=30),
    rbi_reversal=timedelta(days=5),
    repeat_contact_window=timedelta(days=7),
    late_data_grace=timedelta(hours=12),
    rider_stall_after=timedelta(minutes=20),  # last-mile van or bike: a long stop between drops is normal
    fresh_for=timedelta(hours=24),            # parcel scans come every 12-24 hours on most lanes
    address_mismatch_m=500,
)

QUICK = Profile(
    name="quick",
    stall_after=timedelta(minutes=12),
    pickup_within=timedelta(minutes=15),
    ofd_max=timedelta(minutes=25),
    report_window=timedelta(minutes=40),      # Swish reviews cite a 30-40 minute window
    support_ack=timedelta(hours=48),
    resolution=timedelta(days=30),
    refund_start_within=timedelta(hours=2),   # Instamart: cancellation refunds in 2 hours
    refund_working_days=5,                    # Swiggy: UPI refunds 5-7 business days
    order_after_payment=timedelta(minutes=5),
    rbi_reversal=timedelta(days=5),
    repeat_contact_window=timedelta(days=1),
    late_data_grace=timedelta(minutes=3),
    rider_stall_after=timedelta(minutes=4),   # a 10-minute promise has no room for a 4-minute stop
    fresh_for=timedelta(minutes=5),           # rider apps ping every few seconds; 5 minutes of nothing is stale
    address_mismatch_m=150,
)

PROFILES = {p.name: p for p in (PARCEL, QUICK)}


def add_working_days(start, days: int):
    """Add Monday-Friday working days (bank holidays ignored; a known simplification)."""
    current = start
    remaining = days
    while remaining > 0:
        current += timedelta(days=1)
        if current.weekday() < 5:
            remaining -= 1
    return current
