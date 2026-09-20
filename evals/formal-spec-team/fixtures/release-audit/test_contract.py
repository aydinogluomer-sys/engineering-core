from producer import produce
from consumer import consume
assert consume(produce("ok")) == "ok"
