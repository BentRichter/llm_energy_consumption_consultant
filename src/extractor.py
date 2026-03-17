import anthropic
from dotenv import load_dotenv

from src.image_utils import prepare_image_for_api
from src.models import EnergyBillData
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


def extract_bill_data(image_bytes: bytes, filename: str) -> EnergyBillData:
    """Extract energy bill data from a single image."""
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

    return response.parsed_output


def extract_from_pdf(pdf_bytes: bytes) -> EnergyBillData:
    """Extract from PDF. Sends up to 5 pages as separate images in one request."""
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

    return response.parsed_output
