
CRITICAL_SYSTEMS = {"braking", "steering", "engine", "transmission"}

def escalate_severity(base_severity: str, related_systems: list, unresolved_count: int, ignored_count: int):
    level_order = ["low", "moderate", "critical"]
    idx = level_order.index(base_severity)

    if any(sys in CRITICAL_SYSTEMS for sys in related_systems):
        idx = max(idx, 2)

    if unresolved_count >= 3:
        idx = min(idx + 1, 2)

    if ignored_count >= 2:
        idx = min(idx + 1, 2)

    return level_order[idx]

def compute_drive_safety(unresolved_critical: int, unresolved_moderate: int, compounded_risk: float):
    if unresolved_critical > 0:
        return False
    if unresolved_moderate >= 2:
        return False
    if compounded_risk > 2500:
        return False
    return True
