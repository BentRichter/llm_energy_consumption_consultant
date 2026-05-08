import streamlit as st
import resend

from src.models import LeadData


def _get_api_key() -> str:
    return st.secrets["RESEND_API_KEY"]


def send_confirmation_to_user(
    email: str,
    first_name: str,
    tariff_name: str,
    savings_eur: float | None,
) -> None:
    """Send order confirmation email to the customer (BGB §312i obligation)."""
    resend.api_key = _get_api_key()

    savings_text = (
        f"<p>Ihre geschätzte Ersparnis beträgt <strong>ca. {savings_eur:.0f} €/Jahr</strong>.</p>"
        if savings_eur and savings_eur > 0
        else ""
    )

    resend.Emails.send({
        "from": "Energieberatung <noreply@energie-funnel.de>",
        "to": [email],
        "subject": "Ihre Wechselanfrage ist eingegangen",
        "html": f"""
        <p>Hallo {first_name},</p>
        <p>vielen Dank für Ihre Anfrage! Wir haben Ihre Wechselanfrage für den Tarif
        <strong>{tariff_name}</strong> erhalten.</p>
        {savings_text}
        <p>Unser Team meldet sich in Kürze bei Ihnen, um den Wechsel abzuschließen.</p>
        <p>Sie haben das Recht, diese Anfrage innerhalb von <strong>14 Tagen</strong>
        ohne Angabe von Gründen zu widerrufen. Senden Sie dazu einfach eine E-Mail an
        widerruf@energie-funnel.de mit dem Betreff „Widerruf".</p>
        <p>Mit freundlichen Grüßen,<br>Ihr Energieberatungs-Team</p>
        """,
    })


def send_internal_notification(lead: LeadData) -> None:
    """Notify internal team about a new lead."""
    resend.api_key = _get_api_key()

    internal_email = st.secrets.get("INTERNAL_NOTIFICATION_EMAIL", "team@energie-funnel.de")

    savings_line = (
        f"Ersparnis: ca. {lead.estimated_savings_eur:.0f} €/Jahr"
        if lead.estimated_savings_eur
        else "Ersparnis: unbekannt"
    )

    resend.Emails.send({
        "from": "Funnel System <noreply@energie-funnel.de>",
        "to": [internal_email],
        "subject": f"Neuer Lead: {lead.first_name} {lead.last_name}",
        "html": f"""
        <h2>Neuer Lead eingegangen</h2>
        <table>
          <tr><td><b>Name</b></td><td>{lead.first_name} {lead.last_name}</td></tr>
          <tr><td><b>E-Mail</b></td><td>{lead.email}</td></tr>
          <tr><td><b>Telefon</b></td><td>{lead.phone or "–"}</td></tr>
          <tr><td><b>Adresse</b></td><td>{lead.street or "–"}, {lead.zip or ""} {lead.city or ""}</td></tr>
          <tr><td><b>Energieart</b></td><td>{lead.energieart or "–"}</td></tr>
          <tr><td><b>Jahresverbrauch</b></td><td>{lead.jahresverbrauch_kwh or "–"} kWh</td></tr>
          <tr><td><b>Angebotener Tarif</b></td><td>{lead.offered_tariff_name or "–"} ({lead.offered_tariff_anbieter or "–"})</td></tr>
          <tr><td><b>{savings_line}</b></td><td></td></tr>
          <tr><td><b>Marketing-Einwilligung</b></td><td>{"Ja" if lead.marketing_consent else "Nein"}</td></tr>
        </table>
        """,
    })
