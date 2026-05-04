import streamlit as st
from pydantic import ValidationError

from src.email_sender import send_confirmation_to_user, send_internal_notification
from src.extractor import extract_bill_data, extract_from_pdf
from src.models import EnergyBillData, Energieart, LeadData
from src.supabase_client import save_lead
from src.tariff_calculator import calculate_current_cost, compare_tariffs

st.set_page_config(
    page_title="Energiekosten prüfen & sparen",
    page_icon="⚡",
    layout="centered",
)

# ── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    .funnel-step { font-size: 0.8rem; color: #888; margin-bottom: 0.5rem; }
    .big-number { font-size: 2.5rem; font-weight: 700; color: #ff6b00; }
    .savings-box {
        background: #fff8f0; border: 2px solid #ff6b00;
        border-radius: 12px; padding: 1.5rem; text-align: center;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Session state init ───────────────────────────────────────────────────────

def _init_state() -> None:
    defaults = {
        "step": 1,
        "bill_data": None,
        "confidence": 0.0,
        "upload_count": 0,
        "best_tariff_comparison": None,
        "current_cost": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


_init_state()

# ── Step helpers ─────────────────────────────────────────────────────────────

def _go_to(step: int) -> None:
    st.session_state["step"] = step
    st.rerun()


def _step_label(current: int, total: int = 6) -> None:
    st.markdown(f'<p class="funnel-step">Schritt {current} von {total}</p>', unsafe_allow_html=True)


# ── Step 1: Landing ──────────────────────────────────────────────────────────

def step_landing() -> None:
    st.title("Energie-Rechnung analysieren & sparen")
    st.markdown(
        """
        Laden Sie Ihre aktuelle Jahresabrechnung hoch — in unter einer Minute sehen Sie,
        wie viel Sie mit einem günstigeren Tarif sparen könnten.

        **So funktioniert es:**
        1. Rechnung hochladen (Foto oder PDF)
        2. Daten automatisch auslesen lassen
        3. Günstigen Tarif sehen
        4. Wechsel beantragen
        """
    )
    st.info("Ihre Rechnung wird nur zur Analyse verwendet und nicht gespeichert.")
    if st.button("Jetzt Rechnung analysieren", type="primary", use_container_width=True):
        _go_to(2)


# ── Step 2: Upload ───────────────────────────────────────────────────────────

def step_upload() -> None:
    _step_label(1)
    st.header("Rechnung hochladen")

    if st.session_state["upload_count"] >= 3:
        st.error(
            "Sie haben die maximale Anzahl an Uploads erreicht. "
            "Bitte kontaktieren Sie uns direkt."
        )
        return

    uploaded = st.file_uploader(
        "Jahresabrechnung (JPG, PNG, HEIC oder PDF)",
        type=["jpg", "jpeg", "png", "heic", "pdf"],
        label_visibility="collapsed",
    )

    if uploaded:
        if st.button("Rechnung auswerten", type="primary", use_container_width=True):
            st.session_state["upload_count"] += 1
            with st.spinner("Rechnung wird ausgelesen …"):
                file_bytes = uploaded.read()
                filename = uploaded.name
                try:
                    if filename.lower().endswith(".pdf"):
                        bill, confidence = extract_from_pdf(file_bytes)
                    else:
                        bill, confidence = extract_bill_data(file_bytes, filename)
                except Exception as e:
                    st.error(f"Fehler beim Auslesen der Rechnung: {e}")
                    return

            st.session_state["bill_data"] = bill
            st.session_state["confidence"] = confidence
            _go_to(3)


# ── Step 3: Review / Correct ─────────────────────────────────────────────────

def step_review() -> None:
    _step_label(2)
    st.header("Daten prüfen")

    bill: EnergyBillData = st.session_state["bill_data"]
    confidence: float = st.session_state["confidence"]

    if confidence < 0.6:
        st.warning(
            "Einige Werte konnten nicht sicher erkannt werden. "
            "Bitte prüfen und korrigieren Sie die markierten Felder."
        )

    def _field_label(label: str, field_name: str) -> str:
        missing = getattr(bill, field_name) is None
        return f"{label} {'⚠️' if missing and confidence < 0.6 else ''}"

    with st.form("review_form"):
        col1, col2 = st.columns(2)

        with col1:
            anbieter = st.text_input(
                _field_label("Anbieter", "anbieter"),
                value=bill.anbieter or "",
            )
            energieart_options = [None, Energieart.STROM, Energieart.GAS]
            energieart_labels = ["– bitte wählen –", "Strom", "Gas"]
            current_idx = (
                energieart_options.index(bill.energieart)
                if bill.energieart in energieart_options
                else 0
            )
            energieart_sel = st.selectbox(
                _field_label("Energieart", "energieart"),
                options=energieart_labels,
                index=current_idx,
            )
            jahresverbrauch = st.number_input(
                _field_label("Jahresverbrauch (kWh)", "jahresverbrauch_kwh"),
                value=float(bill.jahresverbrauch_kwh) if bill.jahresverbrauch_kwh else 0.0,
                min_value=0.0,
                step=100.0,
            )

        with col2:
            arbeitspreis = st.number_input(
                _field_label("Arbeitspreis (ct/kWh)", "arbeitspreis_ct_kwh"),
                value=float(bill.arbeitspreis_ct_kwh) if bill.arbeitspreis_ct_kwh else 0.0,
                min_value=0.0,
                step=0.1,
                format="%.2f",
            )
            grundpreis = st.number_input(
                _field_label("Grundpreis (EUR/Jahr)", "grundpreis_eur_jahr"),
                value=float(bill.grundpreis_eur_jahr) if bill.grundpreis_eur_jahr else 0.0,
                min_value=0.0,
                step=1.0,
                format="%.2f",
            )
            zahlernummer = st.text_input(
                "Zählernummer",
                value=bill.zahlernummer or "",
            )

        confirmed = st.form_submit_button(
            "Weiter zur Kostenanalyse", type="primary", use_container_width=True
        )

        if confirmed:
            energieart_map = {"Strom": Energieart.STROM, "Gas": Energieart.GAS}
            corrected = EnergyBillData(
                anbieter=anbieter or None,
                energieart=energieart_map.get(energieart_sel),
                jahresverbrauch_kwh=jahresverbrauch if jahresverbrauch > 0 else None,
                arbeitspreis_ct_kwh=arbeitspreis if arbeitspreis > 0 else None,
                grundpreis_eur_jahr=grundpreis if grundpreis > 0 else None,
                zahlernummer=zahlernummer or None,
                zahlerstand_alt=bill.zahlerstand_alt,
                zahlerstand_neu=bill.zahlerstand_neu,
                verbrauchszeitraum_von=bill.verbrauchszeitraum_von,
                verbrauchszeitraum_bis=bill.verbrauchszeitraum_bis,
            )
            st.session_state["bill_data"] = corrected

            comparisons = compare_tariffs(corrected)
            current_cost = calculate_current_cost(corrected)
            st.session_state["current_cost"] = current_cost
            st.session_state["best_tariff_comparison"] = comparisons[0] if comparisons else None

            _go_to(4)


# ── Step 4: Cost overview ────────────────────────────────────────────────────

def step_costs() -> None:
    _step_label(3)
    st.header("Ihre aktuellen Energiekosten")

    bill: EnergyBillData = st.session_state["bill_data"]
    current_cost = st.session_state["current_cost"]
    best = st.session_state["best_tariff_comparison"]

    if current_cost:
        col1, col2 = st.columns(2)
        col1.metric("Aktuelle Jahreskosten", f"{current_cost:.2f} €")
        if bill.arbeitspreis_ct_kwh:
            col2.metric("Ihr Arbeitspreis", f"{bill.arbeitspreis_ct_kwh:.2f} ct/kWh")
    else:
        st.info(
            "Wir konnten die aktuellen Jahreskosten nicht berechnen. "
            "Bitte prüfen Sie die Eingaben im vorherigen Schritt."
        )

    if bill.verbrauchszeitraum_von and bill.verbrauchszeitraum_bis:
        st.caption(
            f"Abrechnungszeitraum: {bill.verbrauchszeitraum_von} – {bill.verbrauchszeitraum_bis}"
        )

    if best:
        savings = best.ersparnis_eur
        if savings > 0:
            st.success(f"Mit einem günstigeren Tarif könnten Sie **ca. {savings:.0f} €/Jahr** sparen!")
        else:
            st.info("Ihr aktueller Tarif ist bereits wettbewerbsfähig.")
    else:
        st.info(
            "Wir konnten keinen passenden Tarif für Ihre Region und Energieart finden. "
            "Kontaktieren Sie uns direkt für ein individuelles Angebot."
        )

    if st.button("Angebot ansehen", type="primary", use_container_width=True):
        _go_to(5)
    if st.button("Zurück", use_container_width=True):
        _go_to(3)


# ── Step 5: Offer ─────────────────────────────────────────────────────────────

def step_offer() -> None:
    _step_label(4)
    st.header("Ihr persönliches Angebot")

    bill: EnergyBillData = st.session_state["bill_data"]
    best = st.session_state["best_tariff_comparison"]
    current_cost = st.session_state["current_cost"]

    if not best:
        st.warning(
            "Leider konnten wir kein passendes Angebot ermitteln. "
            "Bitte hinterlassen Sie Ihre Kontaktdaten – wir melden uns bei Ihnen."
        )
        if st.button("Kontakt aufnehmen", type="primary", use_container_width=True):
            _go_to(6)
        return

    tariff = best.tariff
    savings = best.ersparnis_eur
    used_fallback_consumption = bill.jahresverbrauch_kwh is None

    if used_fallback_consumption:
        avg = 15000.0 if bill.energieart == Energieart.GAS else 3500.0
        st.caption(
            f"Kein Jahresverbrauch erkannt — Berechnung basiert auf Durchschnittswert {avg:,.0f} kWh."
        )

    st.markdown('<div class="savings-box">', unsafe_allow_html=True)
    st.markdown(f"### {tariff.name}")
    st.markdown(f"**{tariff.anbieter}**")

    col1, col2 = st.columns(2)
    col1.metric("Arbeitspreis", f"{tariff.arbeitspreis_ct_kwh:.2f} ct/kWh")
    col2.metric("Grundpreis", f"{tariff.grundpreis_eur_jahr:.2f} €/Jahr")

    st.markdown(f'<p class="big-number">{best.jahreskosten_eur:.0f} €/Jahr</p>', unsafe_allow_html=True)

    if savings > 0 and current_cost:
        st.markdown(f"**Sie sparen ca. {savings:.0f} €/Jahr** gegenüber Ihrem aktuellen Tarif.")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(
        "✅ Keine Vorauskasse  ✅ Kein Risiko – 14 Tage Widerrufsrecht  ✅ Lokaler Anbieter"
    )

    if st.button("Jetzt wechseln", type="primary", use_container_width=True):
        _go_to(6)
    if st.button("Zurück", use_container_width=True):
        _go_to(4)


# ── Step 6: Lead form ─────────────────────────────────────────────────────────

def step_lead_form() -> None:
    _step_label(5)
    st.header("Kontaktdaten eingeben")

    st.markdown(
        "Wir leiten Ihre Anfrage an das zuständige Stadtwerk weiter. "
        "Ein Mitarbeiter meldet sich innerhalb von 1 Werktag."
    )

    bill: EnergyBillData = st.session_state["bill_data"]
    best = st.session_state["best_tariff_comparison"]
    current_cost = st.session_state["current_cost"]

    with st.form("lead_form"):
        col1, col2 = st.columns(2)
        first_name = col1.text_input("Vorname *")
        last_name = col2.text_input("Nachname *")
        email = st.text_input("E-Mail-Adresse *")
        phone = st.text_input("Telefonnummer (optional)")

        st.markdown("**Lieferadresse**")
        street = st.text_input("Straße und Hausnummer")
        col3, col4 = st.columns([1, 3])
        zip_code = col3.text_input("PLZ")
        city = col4.text_input("Ort")

        st.markdown("---")
        agreed = st.checkbox(
            "Ich stimme den AGB und der Datenschutzerklärung zu *"
        )
        marketing = st.checkbox(
            "Ich möchte Angebote und Neuigkeiten per E-Mail erhalten (optional)"
        )

        submitted = st.form_submit_button(
            "Wechsel beantragen", type="primary", use_container_width=True
        )

        if submitted:
            errors = []
            if not first_name.strip():
                errors.append("Vorname ist erforderlich.")
            if not last_name.strip():
                errors.append("Nachname ist erforderlich.")
            if not email.strip():
                errors.append("E-Mail-Adresse ist erforderlich.")
            if not agreed:
                errors.append("Bitte stimmen Sie den AGB und der Datenschutzerklärung zu.")

            if errors:
                for err in errors:
                    st.error(err)
            else:
                try:
                    lead = LeadData(
                        first_name=first_name.strip(),
                        last_name=last_name.strip(),
                        email=email.strip(),
                        phone=phone.strip() or None,
                        street=street.strip() or None,
                        zip=zip_code.strip() or None,
                        city=city.strip() or None,
                        energieart=bill.energieart.value if bill.energieart else None,
                        jahresverbrauch_kwh=bill.jahresverbrauch_kwh,
                        current_cost_eur=current_cost,
                        offered_tariff_name=best.tariff.name if best else None,
                        offered_tariff_anbieter=best.tariff.anbieter if best else None,
                        estimated_savings_eur=best.ersparnis_eur if best else None,
                        agreed_to_terms=agreed,
                        marketing_consent=marketing,
                    )
                except ValidationError as e:
                    st.error(f"Eingabefehler: {e}")
                    return

                with st.spinner("Anfrage wird übermittelt …"):
                    try:
                        save_lead(lead)
                    except Exception as e:
                        st.error(f"Speicherung fehlgeschlagen: {e}")
                        return

                    try:
                        tariff_name = best.tariff.name if best else "Ihr neuer Tarif"
                        savings_val = best.ersparnis_eur if best else None
                        send_confirmation_to_user(
                            email.strip(), first_name.strip(), tariff_name, savings_val
                        )
                        send_internal_notification(lead)
                    except Exception:
                        # E-Mail-Fehler blockiert den Lead-Flow nicht
                        pass

                _go_to(7)

    if st.button("Zurück", use_container_width=True):
        _go_to(5)


# ── Step 7: Thank you ─────────────────────────────────────────────────────────

def step_thank_you() -> None:
    st.balloons()
    st.success("Vielen Dank! Ihre Anfrage wurde erfolgreich übermittelt.")
    st.markdown(
        """
        **Was passiert als nächstes?**
        - Sie erhalten eine Bestätigungs-E-Mail.
        - Ein Mitarbeiter meldet sich innerhalb von 1 Werktag bei Ihnen.
        - Nach Ihrer Zustimmung wird der Wechsel eingeleitet.

        **Widerrufsrecht**: Sie können diese Anfrage innerhalb von 14 Tagen ohne Angabe
        von Gründen widerrufen. Senden Sie dazu eine E-Mail an widerruf@energie-funnel.de.
        """
    )
    if st.button("Neue Analyse starten", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        _go_to(1)


# ── Router ────────────────────────────────────────────────────────────────────

step = st.session_state["step"]

if step == 1:
    step_landing()
elif step == 2:
    step_upload()
elif step == 3:
    step_review()
elif step == 4:
    step_costs()
elif step == 5:
    step_offer()
elif step == 6:
    step_lead_form()
elif step == 7:
    step_thank_you()
