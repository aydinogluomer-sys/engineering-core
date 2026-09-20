from pipeline import normalize, render
assert normalize(" A ") == "a"
assert render(" A ") == "item:a"
