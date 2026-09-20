EXPORT_SCHEMA_VERSION = 2

def export_record(user_tenant, record_tenant, payload):
    return {"schema": EXPORT_SCHEMA_VERSION, "payload": payload}
