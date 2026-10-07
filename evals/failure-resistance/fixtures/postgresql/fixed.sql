ALTER TABLE tenant_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_items FORCE ROW LEVEL SECURITY;
REVOKE ALL ON tenant_items FROM PUBLIC;
CREATE POLICY tenant_isolation ON tenant_items USING (tenant_id = current_setting('app.tenant_id', true));
