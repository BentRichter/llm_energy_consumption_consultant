import anthropic
from dotenv import load_dotenv

from src.image_utils import prepare_image_for_api
from src.models import EnergyBillData, Energieart
from src.pdf_handler import pdf_to_images

load_dotenv()

MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """\
Du bist ein Experte fuer die Analyse deutscher Energierechnungen (Jahresabrechnung).
Extrahiere strukturierte Daten aus dem Foto oder Scan einer Energierechnung.

Wichtige Hinweise:
- Der Arbeitspreis ist in ct/kWh angegeben (Cent pro Kilowattstunde)
- Der Grundpreis kann monatlich oder jaehrlich angegeben sein.
  Gib ihn IMMER als Jahreswert in EUR zurueck.
  Falls er monatlich angegeben ist, multipliziere mit 12.
- Der Jahresverbrauch ist in kWh angegeben
- Zaehlerstaende sind numerische Werte (oft 5-6 Stellen)
- Datumsformat: DD.MM.YYYY
- Energieart ist entweder "Strom" oder "Gas"
- Wenn du einen Wert nicht sicher erkennen kannst, setze das Feld auf null.
  Lieber null als falsch geraten.
"""

USER_PROMPT = "Bitte extrahiere alle relevanten Daten aus dieser Energierechnung."

# Plausibility ranges for extracted values
_ARBEITSPREIS_RANGE = (5.0, 100.0)  # ct/kWh
_GRUNDPREIS_RANGE = (0.0, 2000.0)  # EUR/Jahr
_VERBRAUCH_STROM_RANGE = (500.0, 50000.0)  # kWh
_VERBRAUCH_GAS_RANGE = (5000.0, 200000.0)  # kWh
_VERBRAUCH_UNKNOWN_RANGE = (500.0, 200000.0)  # kWh (fallback)

# Core fields that contribute to confidence scoring
_CORE_FIELDS = ["jahresverbrauch_kwh", "arbeitspreis_ct_kwh", "grundpreis_eur_jahr", "energieart", "anbieter"]


def _sanitize_and_score(bill: EnergyBillData) -> tuple[EnergyBillData, float]:
    """Nullifies out-of-range values and returns (sanitized_bill, confidence_score 0–1)."""
    data = bill.model_dump()

    if data["arbeitspreis_ct_kwh"] is not None:
        lo, hi = _ARBEITSPREIS_RANGE
        if not (lo <= data["arbeitspreis_ct_kwh"] <= hi):
            data["arbeitspreis_ct_kwh"] = None

    if data["grundpreis_eur_jahr"] is not None:
        lo, hi = _GRUNDPREIS_RANGE
        if not (lo <= data["grundpreis_eur_jahr"] <= hi):
            data["grundpreis_eur_jahr"] = None

    if data["jahresverbrauch_kwh"] is not None:
        energieart = data.get("energieart")
        if energieart == Energieart.GAS:
            lo, hi = _VERBRAUCH_GAS_RANGE
        elif energieart == Energieart.STROM:
            lo, hi = _VERBRAUCH_STROM_RANGE
        else:
            lo, hi = _VERBRAUCH_UNKNOWN_RANGE
        if not (lo <= data["jahresverbrauch_kwh"] <= hi):
            data["jahresverbrauch_kwh"] = None

    sanitized = EnergyBillData(**data)

    present = sum(1 for f in _CORE_FIELDS if getattr(sanitized, f) is not None)
    confidence = present / len(_CORE_FIELDS)

    return sanitized, confidence


def extract_bill_data(image_bytes: bytes, filename: str) -> tuple[EnergyBillData, float]:
    """Extract energy bill data from a single image. Returns (data, confidence_score)."""
    client = anthropic.Anthropic()
    b64_data, media_type = prepare_image_for_api(image_bytes, filename)

    response = client.messages.parse(
        model=MODEL,
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": b64_data,
                        },
                    },
                    {"type": "text", "text": USER_PROMPT},
                ],
            }
        ],
        output_format=EnergyBillData,
    )

    return _sanitize_and_score(response.parsed_output)


def extract_from_pdf(pdf_bytes: bytes) -> tuple[EnergyBillData, float]:
    """Extract from PDF. Sends up to 5 pages as separate images in one request.
    Returns (data, confidence_score)."""
    client = anthropic.Anthropic()
    page_images = pdf_to_images(pdf_bytes)

    if not page_images:
        raise ValueError("PDF enthaelt keine Seiten")

    content: list[dict] = []
    for i, img_bytes in enumerate(page_images[:5]):
        b64_data, media_type = prepare_image_for_api(img_bytes, f"page_{i}.jpg")
        content.append({"type": "text", "text": f"Seite {i + 1}:"})
        content.append(
            {
                "type": "image",
                "source": {"type": "base64", "media_type": media_type, "data": b64_data},
            }
        )

    content.append({"type": "text", "text": USER_PROMPT})

    response = client.messages.parse(
        model=MODEL,
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": content}],
        output_format=EnergyBillData,
    )

    return _sanitize_and_score(response.parsed_output)
