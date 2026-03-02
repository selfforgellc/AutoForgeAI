
from datetime import datetime

def downgrade_severity_after_resolution(severity: str):
    order = ["critical", "moderate", "low"]
    if severity in order:
        idx = order.index(severity)
        if idx + 1 < len(order):
            return order[idx + 1]
    return severity

def should_auto_close(vhi_score):
    return vhi_score >= 85
