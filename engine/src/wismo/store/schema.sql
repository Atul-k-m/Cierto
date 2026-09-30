-- Event log schema (ADR-002) with tenant isolation (architecture §9).
-- Idempotent: safe to run on every start.

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'wismo_app') THEN
        CREATE ROLE wismo_app NOLOGIN;
    END IF;
END
$$;

CREATE TABLE IF NOT EXISTS tenant (
    id          text PRIMARY KEY,
    name        text NOT NULL,
    vertical    text NOT NULL CHECK (vertical IN ('parcel', 'quick')),
    created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS event (
    seq             bigserial PRIMARY KEY,
    tenant_id       text NOT NULL REFERENCES tenant (id),
    event_id        text NOT NULL,
    order_ref       text NOT NULL,
    shipment_ref    text,
    type            text NOT NULL,
    status          text,
    substatus       text,
    occurred_at     timestamptz NOT NULL,
    received_at     timestamptz NOT NULL DEFAULT now(),
    asserted_by     text NOT NULL,
    source_adapter  text NOT NULL,
    body            jsonb NOT NULL,
    payload_hash    text NOT NULL,
    UNIQUE (tenant_id, event_id)
);

CREATE INDEX IF NOT EXISTS event_order_timeline
    ON event (tenant_id, order_ref, occurred_at, received_at, seq);

-- The log is append-only, even for the table owner.
CREATE OR REPLACE FUNCTION event_forbid_mutation() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'event log is append-only';
END
$$;

DROP TRIGGER IF EXISTS event_append_only ON event;
CREATE TRIGGER event_append_only
    BEFORE UPDATE OR DELETE ON event
    FOR EACH ROW EXECUTE FUNCTION event_forbid_mutation();

DROP TRIGGER IF EXISTS event_no_truncate ON event;
CREATE TRIGGER event_no_truncate
    BEFORE TRUNCATE ON event
    FOR EACH STATEMENT EXECUTE FUNCTION event_forbid_mutation();

-- Tenant isolation: a session sees and writes only its own tenant's rows.
-- An unset app.tenant_id yields NULL, so the policy fails closed.
ALTER TABLE event ENABLE ROW LEVEL SECURITY;
ALTER TABLE event FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS event_tenant_isolation ON event;
CREATE POLICY event_tenant_isolation ON event
    USING (tenant_id = current_setting('app.tenant_id', true))
    WITH CHECK (tenant_id = current_setting('app.tenant_id', true));

GRANT SELECT ON tenant TO wismo_app;
GRANT SELECT, INSERT ON event TO wismo_app;
GRANT USAGE ON SEQUENCE event_seq_seq TO wismo_app;
