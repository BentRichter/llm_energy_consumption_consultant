import pytest

from src.models import Energieart, EnergyBillData, TariffInfo
from src.tariff_calculator import (
    calculate_current_cost,
    calculate_yearly_cost,
    compare_tariffs,
)


def test_yearly_cost_calculation():
    tariff = TariffInfo(
        name="Test",
        anbieter="Test GmbH",
        arbeitspreis_ct_kwh=30.0,
        grundpreis_eur_jahr=120.0,
        energieart=Energieart.STROM,
    )
    # 3000 kWh * 0.30 EUR/kWh + 120 EUR = 1020 EUR
    assert calculate_yearly_cost(tariff, 3000.0) == pytest.approx(1020.0)


def test_yearly_cost_zero_consumption():
    tariff = TariffInfo(
        name="Test",
        anbieter="Test GmbH",
        arbeitspreis_ct_kwh=30.0,
        grundpreis_eur_jahr=120.0,
        energieart=Energieart.STROM,
    )
    assert calculate_yearly_cost(tariff, 0.0) == pytest.approx(120.0)


def test_current_cost_complete():
    bill = EnergyBillData(
        jahresverbrauch_kwh=3000.0,
        arbeitspreis_ct_kwh=35.0,
        grundpreis_eur_jahr=100.0,
    )
    # 3000 * 0.35 + 100 = 1150
    assert calculate_current_cost(bill) == pytest.approx(1150.0)


def test_current_cost_missing_verbrauch():
    bill = EnergyBillData(arbeitspreis_ct_kwh=35.0, grundpreis_eur_jahr=100.0)
    assert calculate_current_cost(bill) is None


def test_current_cost_missing_arbeitspreis():
    bill = EnergyBillData(jahresverbrauch_kwh=3000.0, grundpreis_eur_jahr=100.0)
    assert calculate_current_cost(bill) is None


def test_current_cost_no_grundpreis():
    bill = EnergyBillData(jahresverbrauch_kwh=3000.0, arbeitspreis_ct_kwh=35.0)
    # 3000 * 0.35 + 0 = 1050
    assert calculate_current_cost(bill) == pytest.approx(1050.0)


def test_compare_tariffs_sorted():
    bill = EnergyBillData(
        jahresverbrauch_kwh=3000.0,
        arbeitspreis_ct_kwh=35.0,
        grundpreis_eur_jahr=100.0,
        energieart=Energieart.STROM,
    )
    results = compare_tariffs(bill)
    assert len(results) > 0
    costs = [r.jahreskosten_eur for r in results]
    assert costs == sorted(costs)


def test_compare_tariffs_filters_by_energieart():
    bill = EnergyBillData(
        jahresverbrauch_kwh=15000.0,
        energieart=Energieart.GAS,
    )
    results = compare_tariffs(bill)
    for r in results:
        assert r.tariff.energieart == Energieart.GAS


def test_compare_tariffs_no_verbrauch():
    bill = EnergyBillData(energieart=Energieart.STROM)
    assert compare_tariffs(bill) == []


def test_compare_tariffs_savings_positive():
    """Wenn der aktuelle Tarif teurer ist, sollte Ersparnis positiv sein."""
    bill = EnergyBillData(
        jahresverbrauch_kwh=3000.0,
        arbeitspreis_ct_kwh=40.0,  # teurer als alle Dummy-Tarife
        grundpreis_eur_jahr=200.0,
        energieart=Energieart.STROM,
    )
    results = compare_tariffs(bill)
    assert len(results) > 0
    assert all(r.ersparnis_eur > 0 for r in results)
