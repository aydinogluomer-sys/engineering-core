from __future__ import annotations

import math


def wilson_interval(successes: int, total: int, z: float = 1.959963984540054) -> tuple[float, float] | None:
    if type(successes) is not int or type(total) is not int or successes < 0 or total <= 0 or successes > total:
        return None
    p = successes / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * total)) / total) / denominator
    return round(max(0.0, center - margin), 6), round(min(1.0, center + margin), 6)


def sample_assessment(successes: int, total: int, minimum: int = 20) -> dict:
    interval = wilson_interval(successes, total)
    return {
        "successes": successes,
        "total": total,
        "wilson_95": interval,
        "sample_adequate": type(total) is int and total >= minimum,
        "limitation": None if type(total) is int and total >= minimum else f"fewer than {minimum} independent prompts; do not generalize reliability",
    }
