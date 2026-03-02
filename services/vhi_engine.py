
def calculate_vhi(open_issue_count, critical_count, failure_probabilities, compounded_multipliers, neglect_penalty):
    # Base score starts at 100
    score = 100

    # Deduct for open issues
    score -= open_issue_count * 5

    # Deduct heavily for critical issues
    score -= critical_count * 12

    # Deduct based on average failure probability
    if failure_probabilities:
        avg_failure = sum(failure_probabilities) / len(failure_probabilities)
        score -= avg_failure * 20

    # Deduct based on compounded economic stress
    if compounded_multipliers:
        avg_compound = sum(compounded_multipliers) / len(compounded_multipliers)
        score -= (avg_compound - 1) * 15

    # Apply neglect penalty multiplier
    score = score / neglect_penalty

    # Clamp between 0 and 100
    return round(max(0, min(score, 100)), 2)
