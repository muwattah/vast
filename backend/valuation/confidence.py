def valuation_confidence(matches, subject_area):
    if not matches:
        return "LOW"
    n = len(matches)
    avg_sim = sum(s for _, s in matches) / n
    top_sim = matches[0][1]
    areas_ok = True
    if subject_area and subject_area > 0:
        ratios = []
        for c, _ in matches:
            if c.living_area and c.living_area > 0:
                ratios.append(min(subject_area, c.living_area) / max(subject_area, c.living_area))
        if ratios and (sum(ratios) / len(ratios)) < 0.7:
            areas_ok = False
    if n >= 5 and avg_sim >= 80 and top_sim >= 85 and areas_ok:
        return "HIGH"
    if n >= 3 and avg_sim >= 70 and top_sim >= 75:
        return "MEDIUM"
    if n >= 1 and top_sim >= 70:
        return "LOW"
    return "LOW"
