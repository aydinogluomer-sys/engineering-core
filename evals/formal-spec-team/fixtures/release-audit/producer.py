SCHEMA_VERSION = 2
def produce(value):
    return {"version": SCHEMA_VERSION, "value": value}
