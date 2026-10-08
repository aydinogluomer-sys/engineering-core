CREATE TABLE public.tenant_items (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tenant_id text NOT NULL,
    payload text NOT NULL
);
ALTER TABLE public.tenant_items OWNER TO app_owner;
REVOKE ALL ON public.tenant_items FROM PUBLIC;
GRANT SELECT, INSERT, UPDATE ON public.tenant_items TO tenant_a, tenant_b, service_role;
GRANT USAGE, SELECT ON SEQUENCE public.tenant_items_id_seq TO tenant_a, tenant_b, service_role;
ALTER TABLE public.tenant_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tenant_items FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON public.tenant_items
    FOR ALL TO tenant_a, tenant_b
    USING (tenant_id = current_setting('app.tenant_id', true))
    WITH CHECK (tenant_id = current_setting('app.tenant_id', true));
