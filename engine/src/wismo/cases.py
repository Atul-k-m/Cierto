"""The resolution desk: turns the resolver's decisions into facts in the event log.

For one engine it records the customer's action, asks the resolver what to do, appends the
decision as an ``engine.resolution`` event (asserted_by engine, so every decision is auditable),
schedules follow-ups on the engine's clock (the courier's window to prove delivery, the
reattempt deadline), executes approved remedies, and emits outgoing webhooks through ``emit``.
Approvals arrive as ``remedy.approved`` events asserted by the merchant.
"""
from collections.abc import Callable
from dataclasses import replace
from datetime import datetime

from .engine import Engine
from .events import AssertedBy, Event, EventType
from .projection import ProofState
from .resolver import (ACTIONABLE, ACTIONS, LLM_MODEL, Policy, Resolution, Situation, _rs, approved_messages, current,
                       executed_messages, llm_enabled, remedy_state, rephrase, resolve, situation, view_of)
from .store.base import AppendResult

Emit = Callable[[str, str, dict], None]   # (tenant_id, webhook type, data object)

# The customer's action becomes a fact first; the resolver then reads it like any other event.
_CUSTOMER_EVENTS = {
    "confirm_received": (EventType.CUSTOMER_RECEIPT_CONFIRMED, {}),
    "report_not_received": (EventType.CUSTOMER_RECEIPT_DISPUTED, {"via": "widget"}),
    "talk_to_person": (EventType.CUSTOMER_CONTACTED, {"channel": "widget", "replied": False, "human": True}),
    "report_missing_item": (EventType.CUSTOMER_CONTACTED, {"channel": "widget", "replied": False, "topic": "missing_item"}),
    "fix_address": (EventType.ADDRESS_CONFIRMED, {"via": "widget"}),
}


class ActionError(ValueError):
    """The action or approval can't apply to this order as it stands."""


class CaseDesk:
    def __init__(self, engine: Engine, brand_for: Callable[[str], str], policy_for: Callable[[str], Policy],
                 emit: Emit | None = None):
        self.engine = engine
        self.brand_for = brand_for
        self.policy_for = policy_for
        self.emit = emit or (lambda tenant, kind, obj: None)
        self.remedies: dict[tuple[str, str], str] = {}   # (tenant, remedy id) -> order ref

    # ---- reading ----

    def situation(self, tenant_id: str, order_ref: str) -> Situation | None:
        return situation(self.engine, tenant_id, order_ref, self.brand_for(tenant_id))

    def state(self, tenant_id: str, order_ref: str) -> dict | None:
        return current(self.engine.events(tenant_id, order_ref))

    def remedy(self, tenant_id: str, remedy_id: str) -> dict | None:
        order_ref = self.remedies.get((tenant_id, remedy_id))
        if not order_ref:
            return None
        state, superseded = remedy_state(self.engine.events(tenant_id, order_ref), remedy_id)
        return self._remedy_object(tenant_id, order_ref, state, superseded=superseded) if state else None

    # ---- writing ----

    def ingest(self, event: Event) -> AppendResult:
        """Append an event from a host or carrier, re-evaluate, and react to proof changing under a pending remedy."""
        tenant, order = event.tenant_id, event.order_ref
        before = self._proof(tenant, order)
        result = self.engine.store.append(event)
        self.engine.evaluate(tenant, order)
        after = self._proof(tenant, order)
        if before != after and after is not None:
            self.emit(tenant, "order.proof_changed", {
                "object": "order", "id": order, "proof": {"state": after[0], "verified_by": after[1]},
                "previous": {"state": before[0] if before else None}, "order_version": self._version(tenant, order)})
        self.reconcile(tenant, order)
        return result

    def act(self, tenant_id: str, order_ref: str, action: str, detail: dict | None = None,
            locale: str = "en-IN") -> dict | None:
        """The shopper's action. Idempotent: repeating the action behind the current resolution changes nothing."""
        if action not in ACTIONS:
            raise ActionError(f"unknown action {action!r}; expected one of {', '.join(ACTIONS)}")
        if not self.engine.events(tenant_id, order_ref):
            raise ActionError(f"no order {order_ref!r}")
        state = self.state(tenant_id, order_ref)
        if state and state["action"] == action:
            return state
        now = self.engine.clock.now()
        kind, data = _CUSTOMER_EVENTS[action]
        p = self.engine.projection(tenant_id, order_ref)
        if action == "report_not_received" and not p.delivery_claim:
            kind, data = EventType.CUSTOMER_CONTACTED, {"channel": "widget", "replied": False, "topic": "not_arrived"}
        if action == "report_missing_item":
            data = {**data, "items": list((detail or {}).get("items") or [])}
        if action == "fix_address" and (detail or {}).get("landmark"):
            data = {**data, "landmark": detail["landmark"]}
        self.ingest(Event(
            event_id=f"{order_ref}:{action}:{now.isoformat()}", tenant_id=tenant_id, order_ref=order_ref,
            type=kind, occurred_at=now, asserted_by=AssertedBy.CUSTOMER, source_adapter="widget", data=data))
        return self._decide(tenant_id, order_ref, action, detail, locale)

    def approve(self, tenant_id: str, remedy_id: str, approved_by: str = "host") -> dict:
        order_ref = self.remedies.get((tenant_id, remedy_id))
        if not order_ref:
            raise KeyError(remedy_id)
        state = self.state(tenant_id, order_ref)
        if not state or state["remedy"].get("id") != remedy_id:
            raise ActionError("this remedy was superseded by a later decision")
        if state["status"] != "proposed":
            raise ActionError(f"remedy is already {state['status']}")
        s = self.situation(tenant_id, order_ref)
        msgs, summary = approved_messages(state, s, approved_by)
        r = state["remedy"]
        self._append(tenant_id, order_ref, EventType.REMEDY_APPROVED, AssertedBy.MERCHANT, f"approve:{remedy_id}", {
            "remedy_id": remedy_id, "approved_by": approved_by, "shopper_message": msgs, "agent_summary": summary,
            "steps": [{"at": s.now.isoformat(), "actor": "host",
                       "text": f"{s.brand} approved the {_rs(r['amount_inr'])} {r['kind'].replace('_', ' ')} ({approved_by})"}]},
            source="api.remedies")
        state = self.state(tenant_id, order_ref)
        self.emit(tenant_id, "remedy.approved", self._remedy_object(tenant_id, order_ref, state))
        fu = state.get("follow_up") or {}
        if fu.get("kind") in ("execute_now", "execute_on_approval"):
            self._execute(tenant_id, order_ref, remedy_id)
        elif fu.get("at") and datetime.fromisoformat(fu["at"]) <= s.now:
            self._follow_up(tenant_id, order_ref, remedy_id)
        return self.remedy(tenant_id, remedy_id)

    def simulate(self, tenant_id: str, order_ref: str, action: str, policy: Policy,
                 customer: dict | None = None) -> Resolution:
        """Run the resolver without writing anything (templates only, no LLM)."""
        s = self.situation(tenant_id, order_ref)
        if s is None:
            raise KeyError(order_ref)
        if customer is not None:
            s = replace(s, placed={**s.placed, "customer": {**s.customer, **customer}})
        return resolve(s, action, policy)

    def reconcile(self, tenant_id: str, order_ref: str) -> None:
        """New evidence while a remedy is pending: proof of delivery pauses a refund; a delivery ends a reattempt."""
        state = self.state(tenant_id, order_ref)
        if not state or state["status"] not in ("proposed", "approved"):
            return
        fu = state.get("follow_up") or {}
        p = self.engine.projection(tenant_id, order_ref)
        decided = datetime.fromisoformat(state["decided_at"])
        claim_after = p.delivery_claim is not None and p.delivery_claim.at > decided
        if fu.get("kind") == "refund_unless_proven" and _proof_strong(p):
            self._decide(tenant_id, order_ref, "proof_arrived")
        elif fu.get("kind") == "refund_unless_delivered" and claim_after:
            self._decide(tenant_id, order_ref, "proof_arrived")
        elif fu.get("kind") == "check_reattempt" and claim_after:
            self._execute(tenant_id, order_ref, state["remedy"]["id"], outcome="delivered")

    # ---- internals ----

    def _decide(self, tenant_id: str, order_ref: str, action: str, detail: dict | None = None,
                locale: str = "en-IN") -> dict:
        s = self.situation(tenant_id, order_ref)
        prior = s.prior
        res = resolve(s, action, self.policy_for(tenant_id), detail)
        loc = locale if locale in res.shopper_message else "en-IN"
        shopper, summary, used = rephrase(res.facts, res.shopper_message[loc], res.agent_summary, loc)
        res.shopper_message[loc], res.agent_summary = shopper, summary
        data = res.data()
        data["llm"] = {"model": LLM_MODEL, "rephrased": used, "locale": loc} if llm_enabled() else None
        self._append(tenant_id, order_ref, EventType.ENGINE_RESOLUTION, AssertedBy.ENGINE,
                     f"resolution:{res.version}", data, source="cierto.resolver")
        state = self.state(tenant_id, order_ref)
        rid = state["remedy"]["id"]
        if rid:
            self.remedies[(tenant_id, rid)] = order_ref

        # Webhooks: what changed for the host.
        if state["case_id"] and not (prior and prior.get("case_id")):
            self.emit(tenant_id, "case.opened", {
                "object": "case", "id": state["case_id"], "order_id": order_ref, "reason": action, **(state["case"] or {})})
        prior_rid = prior["remedy"].get("id") if prior else None
        if prior and prior_rid and prior_rid != rid and prior["status"] in ("proposed", "approved"):
            self.emit(tenant_id, "remedy.cancelled", {**self._remedy_object(tenant_id, order_ref, prior),
                                                      "status": "cancelled", "superseded_by": state["resolution_id"]})
        if rid and rid != prior_rid and state["remedy"]["kind"] in ACTIONABLE:
            self.emit(tenant_id, "remedy.proposed", self._remedy_object(tenant_id, order_ref, state))
            if state["status"] == "approved":
                self.emit(tenant_id, "remedy.approved", {**self._remedy_object(tenant_id, order_ref, state),
                                                         "approved_by": "policy"})

        # Follow-ups: act now, or at the deadline.
        fu = state.get("follow_up") or {}
        if rid and rid != prior_rid:
            if fu.get("kind") == "execute_now" and state["status"] == "approved":
                self._execute(tenant_id, order_ref, rid)
            elif fu.get("kind") in ("refund_unless_proven", "refund_unless_delivered", "check_reattempt"):
                at = datetime.fromisoformat(fu["at"])
                self.engine.clock.schedule(("remedy", tenant_id, rid), at,
                                           lambda: self._follow_up(tenant_id, order_ref, rid))
        return self.state(tenant_id, order_ref)

    def _follow_up(self, tenant_id: str, order_ref: str, remedy_id: str) -> None:
        state = self.state(tenant_id, order_ref)
        if not state or state["remedy"].get("id") != remedy_id or state["status"] == "executed":
            return
        kind = (state.get("follow_up") or {}).get("kind")
        p = self.engine.projection(tenant_id, order_ref)
        decided = datetime.fromisoformat(state["decided_at"])
        claim_after = p.delivery_claim is not None and p.delivery_claim.at > decided
        if kind == "refund_unless_proven":
            if _proof_strong(p):
                self._decide(tenant_id, order_ref, "proof_arrived")
            elif state["status"] == "approved":
                self._execute(tenant_id, order_ref, remedy_id)
        elif kind == "refund_unless_delivered":
            if claim_after:
                self._decide(tenant_id, order_ref, "proof_arrived")
            elif state["status"] == "approved":
                self._execute(tenant_id, order_ref, remedy_id)
        elif kind == "check_reattempt":
            if claim_after:
                self._execute(tenant_id, order_ref, remedy_id, outcome="delivered")
            else:
                self._decide(tenant_id, order_ref, "reattempt_missed")

    def _execute(self, tenant_id: str, order_ref: str, remedy_id: str, outcome: str = "done") -> None:
        state = self.state(tenant_id, order_ref)
        if not state or state["remedy"].get("id") != remedy_id or state["status"] == "executed":
            return
        s = self.situation(tenant_id, order_ref)
        r = state["remedy"]
        reference = r["reference"]
        if outcome == "done" and r["kind"] in ("refund", "partial_refund"):
            # Cierto initiates the refund through the host's payment connector; the bank's credit arrives later
            # as refund.status events from the host or gateway.
            self._append(tenant_id, order_ref, EventType.REFUND_STATUS, AssertedBy.ENGINE, f"refund:{remedy_id}", {
                "stage": "initiated", "amount_inr": r["amount_inr"], "reference": reference, "method": "original",
                "remedy_id": remedy_id}, source="cierto.remedy")
        msgs, summary, steps = executed_messages(state, s, reference, outcome)
        self._append(tenant_id, order_ref, EventType.REMEDY_EXECUTED, AssertedBy.ENGINE, f"execute:{remedy_id}", {
            "remedy_id": remedy_id, "reference": reference, "outcome": outcome, "steps": steps,
            "shopper_message": msgs, "agent_summary": summary}, source="cierto.remedy")
        self.emit(tenant_id, "remedy.executed",
                  self._remedy_object(tenant_id, order_ref, self.state(tenant_id, order_ref)))

    def _append(self, tenant_id: str, order_ref: str, kind: EventType, by: AssertedBy, suffix: str, data: dict,
                source: str) -> None:
        self.engine.store.append(Event(
            event_id=f"{order_ref}:{suffix}", tenant_id=tenant_id, order_ref=order_ref, type=kind,
            occurred_at=self.engine.clock.now(), asserted_by=by, source_adapter=source, data=data))
        self.engine.evaluate(tenant_id, order_ref)

    def _proof(self, tenant_id: str, order_ref: str) -> tuple[str, str | None] | None:
        if not self.engine.events(tenant_id, order_ref):
            return None
        p = self.engine.projection(tenant_id, order_ref)
        return p.proof_state.value, p.verified_by

    def _version(self, tenant_id: str, order_ref: str) -> int:
        return len(self.engine.store.events_for_order(tenant_id, order_ref))

    def _remedy_object(self, tenant_id: str, order_ref: str, state: dict, superseded: bool = False) -> dict:
        r = state["remedy"]
        return {
            "object": "remedy", "id": r["id"], "order_id": order_ref, "case_id": state["case_id"],
            "decision": state["decision"], "kind": r["kind"], "amount_inr": r["amount_inr"], "eta": r["eta"],
            "reference": r["reference"], "needs_approval": state["needs_approval"],
            "approval_reason": state.get("approval_reason"),
            "status": "superseded" if superseded else state["status"], "approved_by": state.get("approved_by"),
            "trust": state.get("trust"), "resolution": view_of(state), "order_version": self._version(tenant_id, order_ref),
        }


def _proof_strong(p) -> bool:
    """Proof that outweighs the customer's word: OTP, or photo plus GPS (not silence, not a claim)."""
    return p.proof_state is ProofState.VERIFIED and p.verified_by in ("otp", "photo_and_geofence")

