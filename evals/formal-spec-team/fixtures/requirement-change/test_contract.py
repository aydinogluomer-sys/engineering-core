from pipeline import deliver

attempts = []
def send():
    attempts.append(1)
    if len(attempts) < 3:
        raise RuntimeError("transient")
    return "ok"
assert deliver(send) == "ok"
assert len(attempts) == 3
