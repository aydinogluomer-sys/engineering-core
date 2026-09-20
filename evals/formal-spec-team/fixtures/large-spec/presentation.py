from accounts import normalize_account
from exports import export_record

EXPECTED_EXPORT_SCHEMA = 1

def export_label(account, tenant, record_tenant, payload):
    record = export_record(tenant, record_tenant, payload)
    return f"{normalize_account(account)}:{record['payload']}"
