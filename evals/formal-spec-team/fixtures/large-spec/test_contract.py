from accounts import normalize_account
from events import apply_credit, _seen
from exports import export_record, EXPORT_SCHEMA_VERSION
from presentation import export_label, EXPECTED_EXPORT_SCHEMA

assert normalize_account(" Acme ") == "acme"
try:
    normalize_account("   ")
    raise AssertionError("empty account accepted")
except ValueError:
    pass
assert export_record("a", "a", "ok")["payload"] == "ok"
try:
    export_record("a", "b", "secret")
    raise AssertionError("cross-tenant export accepted")
except PermissionError:
    pass
_seen.clear()
balance = apply_credit("evt-1", 5, 10)
assert apply_credit("evt-1", 5, balance) == 15
try:
    apply_credit("evt-2", -1, balance)
    raise AssertionError("negative credit accepted")
except ValueError:
    pass
assert export_label(" Acme ", "a", "a", None) == "acme:unavailable"
assert EXPORT_SCHEMA_VERSION == EXPECTED_EXPORT_SCHEMA
