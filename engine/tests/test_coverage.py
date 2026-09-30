import json
from datetime import date
from pathlib import Path

import pytest

from wismo.coverage import healthy
from wismo.coverage.facts import extract
from wismo.coverage.generate import build
from wismo.coverage.harness import run_corpus, run_healthy

COMPLAINTS = Path(__file__).resolve().parents[2] / "data" / "complaints.json"


@pytest.fixture(scope="module")
def corpus():
    data = json.loads(COMPLAINTS.read_text(encoding="utf-8"))
    return {c["id"]: c for c in data["complaints"] if c["window"] == "in-window" and not c["duplicate"]}


def test_extracts_only_stated_facts(corpus):
    f = extract(corpus["IC-213360"])
    assert {"wrong_phone", "support_unanswered"} <= f.stated
    assert "no_otp" not in f.stated   # the complaint never mentions an OTP


def test_dates_roll_back_a_year_across_new_year(corpus):
    f = extract(corpus["IC-213885"])   # posted 22 Jan 2026: "paid 24 Dec, promised 2 Jan"
    assert f.dates == {"ordered": date(2025, 12, 24), "due": date(2026, 1, 2)}


def test_unstated_proof_stays_unknown(corpus):
    case = build(corpus["IC-214806"], extract(corpus["IC-214806"]))   # "shown delivered, not received" only
    delivered = [e for _, e in case.arrivals if e.substatus == "delivered.delivered"]
    assert delivered and delivered[0].proof is None


def test_corpus_results(corpus):
    results = {r.complaint_id: r for r in run_corpus(list(corpus.values()))[0]}
    assert len(results) == 93
    assert results["IC-207446"].status == "missed" and "returns" in results["IC-207446"].note
    assert results["IC-213360"].caught_by == "phone_mismatch" and results["IC-213360"].mode == "proactive"
    assert all(r.status == "needs_customer_report" for r in results.values() if r.category_id in (7, 8, 9, 11))


def test_no_false_alarms_on_standard_healthy_orders():
    stats = run_healthy(healthy.generate(n_parcel=120, n_quick=40))
    assert all(v["with_false_alarm"] == 0 for v in stats["per_vertical"].values()), stats
