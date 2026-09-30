from datetime import timedelta
from pathlib import Path

import pytest

from wismo.scenario import Scenario, parse_offset, replay
from wismo.store import AppendResult, local

SCENARIO = Path(__file__).resolve().parents[2] / "scenarios" / "IC-213360.json"


@pytest.mark.parametrize("text,expected", [
    ("+0h", timedelta(0)),
    ("+2d", timedelta(days=2)),
    ("+4d2h47m", timedelta(days=4, hours=2, minutes=47)),
    ("+45m", timedelta(minutes=45)),
])
def test_parse_offset(text, expected):
    assert parse_offset(text) == expected


@pytest.mark.parametrize("text", ["2d", "+", "+1w", "-1h"])
def test_parse_offset_rejects(text):
    with pytest.raises(ValueError):
        parse_offset(text)


def test_scenario_replays_in_happened_order_and_is_idempotent(admin_uri, store):
    scenario = Scenario.load(SCENARIO)
    local.ensure_tenant(admin_uri, scenario.tenant.id, scenario.tenant.name, scenario.tenant.vertical)

    first = replay(store, scenario)
    again = replay(store, scenario)
    assert first[AppendResult.INSERTED] + first[AppendResult.DUPLICATE] == len(scenario.events)
    assert again[AppendResult.DUPLICATE] == len(scenario.events)

    timeline = [s.event for s in store.events_for_order(scenario.tenant.id, scenario.order_ref)]
    occurred = [e.occurred_at for e in timeline]
    assert occurred == sorted(occurred)
    subs = [e.substatus for e in timeline if e.substatus]
    assert subs.index("in_transit.at_destination_hub") < subs.index("out_for_delivery.out_for_delivery")
    delivered = next(e for e in timeline if e.substatus == "delivered.delivered")
    assert delivered.proof.otp_verified is False
