import pytest
from pydantic import ValidationError

from src.models import Energieart, EnergyBillData, TariffComparison, TariffInfo


def test_valid_complete_bill():
    bill = EnergyBillData(
        zahlernummer="12345678",
        jahresverbrauch_kwh=3500.0,
        zahlerstand_alt=10000.0,
        zahlerstand_neu=13500.0,
        arbeitspreis_ct_kwh=32.5,
        grundpreis_eur_jahr=120.0,
        verbrauchszeitraum_von="01.01.2024",
        verbrauchszeitraum_bis="31.12.2024",
        anbieter="Stadtwerke Test",
        energieart=Energieart.STROM,
    )
    assert bill.jahresverbrauch_kwh == 3500.0
    assert bill.energieart == Energieart.STROM


def test_all_none_bill():
    bill = EnergyBillData()
    assert bill.zahlernummer is None
    assert bill.jahresverbrauch_kwh is None
    assert bill.energieart is None


def test_energieart_from_string():
    bill = EnergyBillData(energieart="Strom")
    assert bill.energieart == Energieart.STROM

    bill_gas = EnergyBillData(energieart="Gas")
    assert bill_gas.energieart == Energieart.GAS


def test_invalid_energieart():
    with pytest.raises(ValidationError):
        EnergyBillData(energieart="Wasser")


def test_tariff_info():
    tariff = TariffInfo(
        name="TestTarif",
        anbieter="TestAnbieter",
        arbeitspreis_ct_kwh=30.0,
        grundpreis_eur_jahr=120.0,
        energieart=Energieart.STROM,
    )
    assert tariff.name == "TestTarif"


def test_tariff_comparison():
    tariff = TariffInfo(
        name="Test",
        anbieter="Test GmbH",
        arbeitspreis_ct_kwh=30.0,
        grundpreis_eur_jahr=120.0,
        energieart=Energieart.STROM,
    )
    comp = TariffComparison(tariff=tariff, jahreskosten_eur=1020.0, ersparnis_eur=50.0)
    assert comp.jahreskosten_eur == 1020.0
    assert comp.ersparnis_eur == 50.0
