from typing import List
import math

class Hypothesis:
    def __init__(self, name: str, pri: float = 0.2):
        self.name = name
        self.score = math.log(pri)

def propose_hypotheses(codes: List[str], symptoms: List[str]) -> List[Hypothesis]:
    seeds = []
    if "P0301" in codes:
        seeds += [("Ignition coil cyl 1", 0.35), ("Spark plug cyl 1", 0.35), ("Injector cyl 1", 0.15), ("Vacuum leak", 0.1)]
    if "P0171" in codes:
        seeds += [("Vacuum leak", 0.4), ("MAF sensor fouled", 0.3), ("Fuel pressure low", 0.2)]
    if not seeds:
        seeds = [("Ignition issue", 0.25), ("Fuel delivery issue", 0.25), ("Air metering issue", 0.2), ("Compression issue", 0.15)]
    return [Hypothesis(n, pri) for n,pri in seeds]

def discriminating_tests(hyps: List[Hypothesis]) -> List[str]:
    names = [h.name for h in hyps]
    tests = []
    if any("Ignition" in n or "coil" in n for n in names):
        tests.append("Swap coil from cyl 1 to cyl 2; does misfire move to P0302?")
    if any("Spark plug" in n for n in names):
        tests.append("Inspect/replace plug #1; verify gap and fouling.")
    if any("Injector" in n for n in names):
        tests.append("Listen for injector tick; perform cylinder balance test on #1.")
    if any("Vacuum" in n for n in names):
        tests.append("Spray brake cleaner around intake/hoses; RPM change = leak.")
    if any("MAF" in n for n in names):
        tests.append("Log MAF g/s at warm idle; out-of-range suggests fouling.")
    if any("Fuel pressure" in n for n in names):
        tests.append("Measure fuel rail pressure at idle and WOT.")
    return tests[:3]

def update_scores(hyps: List[Hypothesis], observation: str):
    obs = observation.lower()
    for h in hyps:
        if "misfire move" in obs and "coil" in h.name.lower():
            h.score += 1.0
        if "plug" in obs and ("fouled" in obs or "worn" in obs) and "plug" in h.name.lower():
            h.score += 0.8
        if "vacuum" in obs and ("rpm change" in obs or "leak" in obs) and "vacuum" in h.name.lower():
            h.score += 0.8
        if "injector" in obs and "balance" in obs and "injector" in h.name.lower():
            h.score += 0.7
    hyps.sort(key=lambda x: x.score, reverse=True)
    return hyps
