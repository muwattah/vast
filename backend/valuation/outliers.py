"""Outlier detection for EUR/m2 among comparables."""
from typing import List, Dict, Any
import statistics

def detect_ppm2_outliers(ppm2_values: List[float], factor: float = 1.5) -> Dict[str, Any]:
    if not ppm2_values:
        return {"median": None, "outlier_indices": [], "trimmed_median": None, "count": 0}
    vals = sorted(ppm2_values)
    med = statistics.median(vals)
    outlier_idx = []
    if len(vals) >= 6:
        q1 = statistics.median(vals[: len(vals) // 2])
        q3 = statistics.median(vals[(len(vals) + 1) // 2 :])
        iqr = q3 - q1
        low, high = q1 - factor * iqr, q3 + factor * iqr
        outlier_idx = [i for i, v in enumerate(ppm2_values) if v < low or v > high]
    else:
        low, high = med * 0.55, med * 1.55
        outlier_idx = [i for i, v in enumerate(ppm2_values) if v < low or v > high]
        q1 = q3 = iqr = None
    trimmed = [v for i, v in enumerate(ppm2_values) if i not in outlier_idx]
    trimmed_med = statistics.median(sorted(trimmed)) if trimmed else med
    return {
        "median": med, "q1": q1 if len(vals) >= 6 else None,
        "q3": q3 if len(vals) >= 6 else None, "iqr": iqr if len(vals) >= 6 else None,
        "bounds": (low, high), "outlier_indices": outlier_idx,
        "trimmed_median": trimmed_med, "count": len(vals),
    }
