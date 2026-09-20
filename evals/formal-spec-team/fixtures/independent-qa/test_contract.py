from auth import read_export
assert read_export("a", "a", "ok") == "ok"
try:
    read_export("a", "b", "secret")
    raise AssertionError("cross tenant allowed")
except PermissionError as exc:
    assert "secret" not in str(exc)
