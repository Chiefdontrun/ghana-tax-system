"""
Tax-domain constants — income brackets and affordability cap.

Bracket representative incomes are used at registration as declared_turnover_pesewas
for PERCENTAGE_TURNOVER schedules, and for the hard 25% affordability ceiling.
Amounts are in pesewas (1 GHS = 100 pesewas).
"""

from __future__ import annotations

from typing import Optional

# Hard safety ceiling: no assessment may exceed this fraction of the bracket's
# representative annual income when income_bracket is set on the business.
AFFORDABILITY_CAP_FRACTION = 0.25

# Code → display range (monthly) + representative annual income (pesewas)
INCOME_BRACKETS: dict[str, dict] = {
    "BRACKET_1": {
        "display_monthly": "GHC 100 – 400",
        "ussd_label": "GHC 100-400",
        "representative_annual_income_pesewas": 300_000,  # GHC 3,000
    },
    "BRACKET_2": {
        "display_monthly": "GHC 401 – 1,000",
        "ussd_label": "GHC 401-1000",
        "representative_annual_income_pesewas": 840_000,  # GHC 8,400
    },
    "BRACKET_3": {
        "display_monthly": "GHC 1,001 – 3,000",
        "ussd_label": "GHC 1001-3000",
        "representative_annual_income_pesewas": 2_400_000,  # GHC 24,000
    },
    "BRACKET_4": {
        "display_monthly": "GHC 3,001+",
        "ussd_label": "GHC 3001+",
        "representative_annual_income_pesewas": 4_800_000,  # GHC 48,000
    },
}

VALID_INCOME_BRACKETS: tuple[str, ...] = tuple(INCOME_BRACKETS.keys())


def get_representative_annual_income_pesewas(bracket: Optional[str]) -> Optional[int]:
    """Return representative annual income in pesewas, or None if unknown/missing."""
    if not bracket:
        return None
    entry = INCOME_BRACKETS.get(bracket)
    if not entry:
        return None
    return int(entry["representative_annual_income_pesewas"])


def affordability_cap_pesewas(bracket: Optional[str]) -> Optional[int]:
    """
    25% of the bracket's representative annual income, in pesewas.
    Returns None when no bracket (pre-existing traders — skip cap).
    """
    rep = get_representative_annual_income_pesewas(bracket)
    if rep is None:
        return None
    return int(rep * AFFORDABILITY_CAP_FRACTION)
