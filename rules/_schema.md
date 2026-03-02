# AutoForge Mechanic Playbook Schema (v1)

This is NOT a script. It is guardrails + heuristics.

## Rule file structure
- version: "1.x"
- domain: "hvac|engine|electrical|cooling|brakes|..."
- rules: list of rule objects

## Rule object fields
- id: unique string
- priority: integer (higher wins)
- triggers:
  - keywords: list[str]  (simple contains match)
  - regex: list[str]     (python regex patterns, case-insensitive)
- lock:
  - system: "hvac|electrical|cooling|engine|..."
  - component_hints: list[str]
- forbid:
  - systems: list[str]
  - claims: list[str] (phrases/ideas the model must not assert)
- safety:
  - flags: list[str] ("fire_risk", "do_not_drive", ...)
  - message: str (short warning)
- questions:
  - confirm: list[str] (high-value narrowing questions)
  - disambiguate: list[str] (clarify fan=blower vs radiator fan etc)
- next_actions:
  - micro_steps: list[str] (1–3 steps, human language)
  - what_it_means: str (how to interpret result)
- confidence_caps:
  - initial_max: float (0..1)
  - after_evidence_max: float (0..1)

## Why this works
- Engine code stays stable.
- Behavior is controlled by rules + examples.
- If it violates reality, you edit YAML, not Python.
