"""Extract only the facts a complaint states. Anything unstated stays unknown.

Deterministic keyword and date rules over the complaint's verbatim fragment and
summary; every extracted fact is listed in the report so it can be checked by eye.
"""
import re
from dataclasses import dataclass, field
from datetime import date

_MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], start=1)}
_DATE = r"(\d{1,2})\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)"

_PATTERNS = {
    "no_call": r"no (courier |agent )?call|not calling|any calls?\b|no calls|without call|no attempt",
    "no_otp": r"no otp|otpany|no call or otp|without otp|no delivery verification",
    "delivered_early": r"two days early|before 2 of delivery",
    "wrong_phone": r"wrong (phone )?number|invalid number|different contact number|false and invalid",
    "undispatched": r"undispatched|not dispatched|not even shipped",
    "eta_slipping": r"eta slips|slips daily|extended daily|delayed very day|dates not updated|not updating the delivery dates",
    "tracking_frozen": r"frozen|stuck|continuously the same|can't track|cannot track",
    "still_out_for_delivery": r"still 'out for delivery'|status 'out for delivery'",
    "no_partner": r"no (delivery )?partner (available )?(in|for) (my |your )?area",
    "address_blamed": r"address is wrong|wrong address",
    "failed_attempt_msg": r"non-delivery message|branch will not",
    "returned": r"order returned|returned after",
    "doorstep_cancel": r"doorstep|cancellation code",
    "system_cancelled": r"auto-cancelled|automatically cancelled|'user-cancelled'",
    "cancelled": r"cancel",
    "refund_initiated": r"refund 'initiated'|refund initiated|refund promised",
    "payment_no_order": r"(debit|deducted).*(no order|not been placed|not confirmed|order id not generated)|order unconfirmed",
    "support_unanswered": r"unanswered|no reply|not replying|no response|unresponsive|silent|ignored|no help|nobody responds|no assistance|busy|cannot reach",
    "bot_loop": r"\bai\b|bot|chatbot|repeats questions",
    "many_contacts": r"10 (chat|bar|times)|issue raised 10|raised 10|repeated emails|so many time|follow-ups",
    "ticket_closed": r"closed|marked resolved|denied|rejected",
}


@dataclass
class Facts:
    complaint_id: str
    category_id: int
    complaint_date: date
    flags: dict
    stated: set[str] = field(default_factory=set)
    dates: dict[str, date] = field(default_factory=dict)   # ordered / due / delivered
    days: int | None = None
    amount_inr: int | None = None
    refunded_of: tuple[int, int] | None = None

    def has(self, fact: str) -> bool:
        return fact in self.stated


def _to_date(day: str, month: str, complaint: date) -> date:
    m = _MONTHS[month]
    year = complaint.year - 1 if m > complaint.month else complaint.year
    return date(year, m, int(day))


def extract(c: dict) -> Facts:
    text = f"{c.get('quote', '')} | {c['summary']}".lower()
    f = Facts(c["id"], c["category_id"], date.fromisoformat(c["date"]), c.get("flags", {}))
    f.stated = {name for name, pat in _PATTERNS.items() if re.search(pat, text)}

    for label, key in (("ordered", "ordered"), ("paid", "ordered"), ("promised", "due"), ("due", "due"),
                       ("eta", "due"), ("delivered", "delivered")):
        if m := re.search(rf"\b{label}\b(?: on| by)?\s+{_DATE}", text):
            f.dates.setdefault(key, _to_date(m.group(1), m.group(2), f.complaint_date))

    spans = [int(n) for n in re.findall(r"(\d+)\s*days?\b", text)]
    if "a month" in text:
        spans.append(30)
    if re.search(r"two weeks|half of month", text):
        spans.append(14)
    if re.search(r"\ba week\b", text):
        spans.append(7)
    f.days = max(spans) if spans else None

    if m := re.search(r"refunded rs ([\d,]+) of rs ([\d,]+)", text):
        f.refunded_of = (int(m.group(1).replace(",", "")), int(m.group(2).replace(",", "")))
    if m := re.search(r"rs\s*([\d,]+)", text):
        f.amount_inr = int(m.group(1).replace(",", ""))
    return f
