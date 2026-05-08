from enum import StrEnum

from pydantic import BaseModel, EmailStr, Field


class Energieart(StrEnum):
    STROM = "Strom"
    GAS = "Gas"


class EnergyBillData(BaseModel):
    zahlernummer: str | None = Field(None, description="Zaehlernummer / Meter number")
    jahresverbrauch_kwh: float | None = Field(None, description="Jahresverbrauch in kWh")
    zahlerstand_alt: float | None = Field(None, description="Alter Zaehlerstand")
    zahlerstand_neu: float | None = Field(None, description="Neuer Zaehlerstand")
    arbeitspreis_ct_kwh: float | None = Field(None, description="Arbeitspreis in ct/kWh")
    grundpreis_eur_jahr: float | None = Field(None, description="Grundpreis in EUR/Jahr")
    verbrauchszeitraum_von: str | None = Field(
        None, description="Beginn Verbrauchszeitraum (DD.MM.YYYY)"
    )
    verbrauchszeitraum_bis: str | None = Field(
        None, description="Ende Verbrauchszeitraum (DD.MM.YYYY)"
    )
    anbieter: str | None = Field(None, description="Energieanbieter")
    energieart: Energieart | None = Field(None, description="Strom oder Gas")


class TariffInfo(BaseModel):
    name: str
    anbieter: str
    arbeitspreis_ct_kwh: float
    grundpreis_eur_jahr: float
    energieart: Energieart


class TariffComparison(BaseModel):
    tariff: TariffInfo
    jahreskosten_eur: float
    ersparnis_eur: float


class LeadData(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str | None = None
    street: str | None = None
    zip: str | None = None
    city: str | None = None
    energieart: str | None = None
    jahresverbrauch_kwh: float | None = None
    current_cost_eur: float | None = None
    offered_tariff_name: str | None = None
    offered_tariff_anbieter: str | None = None
    estimated_savings_eur: float | None = None
    agreed_to_terms: bool
    terms_version: str = "v1.0"
    marketing_consent: bool = False
    source: str = "funnel_mvp"
