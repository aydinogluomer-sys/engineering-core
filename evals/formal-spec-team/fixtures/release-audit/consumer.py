EXPECTED_VERSION = 1
def consume(message):
    if message["version"] != EXPECTED_VERSION:
        raise ValueError("schema mismatch")
    return message["value"]
