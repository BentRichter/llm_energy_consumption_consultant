from src.models import EnergyBillData


def test_schema_is_valid_json_schema():
    schema = EnergyBillData.model_json_schema()
    assert schema["type"] == "object"
    assert "zahlernummer" in schema["properties"]
    assert "jahresverbrauch_kwh" in schema["properties"]
    assert "energieart" in schema["properties"]


def test_schema_all_fields_present():
    schema = EnergyBillData.model_json_schema()
    expected_fields = [
        "zahlernummer",
        "jahresverbrauch_kwh",
        "zahlerstand_alt",
        "zahlerstand_neu",
        "arbeitspreis_ct_kwh",
        "grundpreis_eur_jahr",
        "verbrauchszeitraum_von",
        "verbrauchszeitraum_bis",
        "anbieter",
        "energieart",
    ]
    for field in expected_fields:
        assert field in schema["properties"], f"Field {field} missing from schema"


def test_parse_from_json():
    """Simulate what the API would return as structured output."""
    raw_json = """{
        "zahlernummer": "1234567890",
        "jahresverbrauch_kwh": 3200.0,
        "zahlerstand_alt": 45678.0,
        "zahlerstand_neu": 48878.0,
        "arbeitspreis_ct_kwh": 31.5,
        "grundpreis_eur_jahr": 132.0,
        "verbrauchszeitraum_von": "01.01.2024",
        "verbrauchszeitraum_bis": "31.12.2024",
        "anbieter": "Stadtwerke Musterstadt",
        "energieart": "Strom"
    }"""
    bill = EnergyBillData.model_validate_json(raw_json)
    assert bill.jahresverbrauch_kwh == 3200.0
    assert bill.anbieter == "Stadtwerke Musterstadt"


def test_parse_partial_json():
    """API might return nulls for fields it couldn't extract."""
    raw_json = """{
        "zahlernummer": null,
        "jahresverbrauch_kwh": 2800.0,
        "zahlerstand_alt": null,
        "zahlerstand_neu": null,
        "arbeitspreis_ct_kwh": null,
        "grundpreis_eur_jahr": null,
        "verbrauchszeitraum_von": null,
        "verbrauchszeitraum_bis": null,
        "anbieter": "E.ON",
        "energieart": "Strom"
    }"""
    bill = EnergyBillData.model_validate_json(raw_json)
    assert bill.jahresverbrauch_kwh == 2800.0
    assert bill.zahlernummer is None
    assert bill.arbeitspreis_ct_kwh is None
