from backend.config import get_settings

CONDITION_MAP = {
    "to_renovate": "to_renovate", "te_renoveren": "to_renovate",
    "partial": "partial", "gedeeltelijk": "partial",
    "renovated": "renovated", "gerenoveerd": "renovated",
    "turnkey": "turnkey", "instapklaar": "turnkey",
    "new": "new", "nieuwbouw": "new",
}

def condition_key(raw):
    if not raw:
        return "renovated"
    k = raw.lower().strip().replace(" ", "_")
    return CONDITION_MAP.get(k, "renovated")

def adjustment_per_m2(condition):
    s = get_settings()
    key = condition_key(condition)
    return {
        "to_renovate": s.adj_to_renovate, "partial": s.adj_partial,
        "renovated": s.adj_renovated, "turnkey": s.adj_turnkey, "new": s.adj_new,
    }.get(key, 0.0)

def adjusted_ppm2(comp_ppm2, condition):
    return comp_ppm2 + adjustment_per_m2(condition)
