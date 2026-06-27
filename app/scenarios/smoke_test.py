"""Smoke test for the scenario builder.

Run from the worktree root:
    python app/scenarios/smoke_test.py

Does NOT require .env: the builder composes prompts from app.scenarios.niches +
app.prompts_pt_pt, neither of which loads app.config.settings. FastAPI/Pydantic are
not imported here (the router is not exercised by this test).
"""
import os
import sys

# Make the worktree root importable so `app.scenarios...` resolves when this file is
# run directly (python app/scenarios/smoke_test.py puts app/scenarios on sys.path[0],
# not the worktree root).
sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
)

from app.scenarios.builder import build_scenario  # noqa: E402
from app.scenarios.niches import NICHE_ORDER, list_niches  # noqa: E402

# Section headers produced by app.prompts_pt_pt.build_system_prompt (accent-free, as
# defined in the shared module). The task requires these to be present.
REQUIRED_SECTIONS = [
    "## IDENTIDADE",
    "## COMO FALAR",
    "## SE NAO PERCEBESTE",
    "## RITMO",
    "## GUARDRAILS",
    "## O QUE FAZES",
]

# PT-PT markers that prove European Portuguese wording is present.
PT_PT_MARKERS = ["português europeu", "não", "consulta"]


def main() -> int:
    print("=== niches (12 expected, in NICHE_ORDER) ===")
    niches = list_niches()
    for n in niches:
        print(
            f"  {n['id']:<12} label={n['label']!r} "
            f"role={n['role']} booking_term={n['booking_term']}"
        )
    assert len(niches) == 12, f"expected 12 niches, got {len(niches)}"
    assert [n["id"] for n in niches] == NICHE_ORDER, "niche order mismatch"
    assert {n["id"] for n in niches} == set(NICHE_CONFIG_KEYS), "niche id set mismatch"
    print()

    scenario = build_scenario("dental", "Clinica Exemplo")
    sp = scenario["system_prompt"]

    print("=== keys returned by build_scenario ===")
    print(list(scenario.keys()))
    print()

    print("=== system_prompt (first 500 chars) ===")
    print(sp[:500])
    print("...\n")

    print("=== first_message_inbound ===")
    print(scenario["first_message_inbound"])
    print("=== first_message_outbound ===")
    print(scenario["first_message_outbound"])
    print()

    print("=== capture_fields ===")
    print(scenario["capture_fields"])
    print()

    print("=== section check ===")
    missing = [s for s in REQUIRED_SECTIONS if s not in sp]
    if missing:
        print("MISSING SECTIONS:", missing)
        return 1
    print(
        "OK: all required sections present "
        "(IDENTIDADE / COMO FALAR / SE NAO PERCEBESTE / RITMO / GUARDRAILS / O QUE FAZES)"
    )
    print()

    print("=== PT-PT check ===")
    found = [m for m in PT_PT_MARKERS if m in sp]
    print("PT-PT markers found:", found)
    if len(found) != len(PT_PT_MARKERS):
        print("FAIL: missing PT-PT markers:", set(PT_PT_MARKERS) - set(found))
        return 1
    print("OK: PT-PT markers present")
    print()

    print("=== knowledge_block (dental, no extra -> example) ===")
    print(scenario["knowledge_block"][:300], "...\n")

    print("=== build with extra overrides knowledge_block ===")
    s2 = build_scenario(
        "legal",
        "Sociedade Lima",
        extra={"opening_hours": "9h-18h", "services": "Direito civil", "prices": "", "notes": ""},
    )
    print(s2["knowledge_block"])
    print()

    print("=== unknown niche raises ValueError ===")
    try:
        build_scenario("unknown", "X")
    except ValueError as exc:
        print("OK: ValueError ->", exc)
    else:
        print("FAIL: expected ValueError for unknown niche")
        return 1
    print()

    print("ALL SMOKE CHECKS PASSED")
    return 0


# Local alias to avoid importing the whole package just for the key set in the assert.
NICHE_CONFIG_KEYS = (
    ("dental", "legal", "accounting", "automotive", "real_estate", "fitness", "restaurant", "bakery", "beauty", "hospitality", "pharmacy", "custom")
)


if __name__ == "__main__":
    sys.exit(main())
