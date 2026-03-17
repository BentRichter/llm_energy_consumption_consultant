import json
from pathlib import Path

from src.models import EnergyBillData, TariffComparison, TariffInfo

TARIFF_FILE = Path(__file__).parent.parent / "tariffs" / "sample_tariffs.json"


def load_tariffs() -> list[TariffInfo]:
    with open(TARIFF_FILE) as f:
        data = json.load(f)
    return [TariffInfo(**t) for t in data]


def calculate_yearly_cost(tariff: TariffInfo, jahresverbrauch_kwh: float) -> float:
    """Jahreskosten = Grundpreis + (Verbrauch * Arbeitspreis)"""
    arbeitspreis_eur = tariff.arbeitspreis_ct_kwh / 100
    return tariff.grundpreis_eur_jahr + (jahresverbrauch_kwh * arbeitspreis_eur)


def calculate_current_cost(bill: EnergyBillData) -> float | None:
    """Calculate yearly cost from the extracted bill data."""
    if bill.jahresverbrauch_kwh is None or bill.arbeitspreis_ct_kwh is None:
        return None
    grundpreis = bill.grundpreis_eur_jahr or 0.0
    arbeitspreis_eur = bill.arbeitspreis_ct_kwh / 100
    return grundpreis + (bill.jahresverbrauch_kwh * arbeitspreis_eur)


def compare_tariffs(bill: EnergyBillData) -> list[TariffComparison]:
    """Compare extracted bill data against available tariffs, sorted by cost."""
    if bill.jahresverbrauch_kwh is None:
        return []

    current_cost = calculate_current_cost(bill)
    tariffs = load_tariffs()

    if bill.energieart:
        tariffs = [t for t in tariffs if t.energieart == bill.energieart]

    comparisons = []
    for tariff in tariffs:
        yearly = calculate_yearly_cost(tariff, bill.jahresverbrauch_kwh)
        savings = (current_cost - yearly) if current_cost else 0.0
        comparisons.append(
            TariffComparison(
                tariff=tariff,
                jahreskosten_eur=round(yearly, 2),
                ersparnis_eur=round(savings, 2),
            )
        )

    comparisons.sort(key=lambda c: c.jahreskosten_eur)
    return comparisons
