import streamlit as st
from dotenv import load_dotenv

from src.extractor import extract_bill_data, extract_from_pdf
from src.models import Energieart, EnergyBillData
from src.tariff_calculator import calculate_current_cost, compare_tariffs, load_tariffs

load_dotenv()

st.set_page_config(page_title="Energierechnung Analyzer", page_icon="⚡", layout="wide")

st.markdown(
    """
    <style>
    .upload-box {
        border: 2px dashed #4a9eff;
        border-radius: 12px;
        padding: 1.5rem;
        background: #f8faff;
    }
    .cost-bar {
        background: #f0f2f6;
        border-radius: 10px;
        padding: 1.2rem 1.5rem;
        margin: 1rem 0;
    }
    .tariff-card {
        border: 1px solid #e0e4ea;
        border-radius: 10px;
        padding: 0.9rem 1.1rem;
        margin-bottom: 0.6rem;
        background: #fff;
    }
    .tariff-card-best {
        border: 2px solid #f5a623;
        border-radius: 10px;
        padding: 0.9rem 1.1rem;
        margin-bottom: 0.6rem;
        background: #fffdf5;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def check_password():
    if st.session_state.get("authenticated"):
        return True
    st.title("⚡ Energierechnung Analyzer")
    with st.form("login"):
        password = st.text_input("Passwort", type="password")
        submitted = st.form_submit_button("Anmelden")
    if submitted:
        if password == st.secrets["APP_PASSWORD"]:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Falsches Passwort.")
    return False


if not check_password():
    st.stop()

st.title("⚡ Energierechnung Analyzer")

# ── Pre-upload: two-column layout ──────────────────────────────────────────
if "bill_data" not in st.session_state:
    col_upload, col_tariffs = st.columns([1, 1], gap="large")

    with col_upload:
        st.markdown("#### Rechnung hochladen")
        uploaded_file = st.file_uploader(
            "Foto oder PDF deiner Jahresabrechnung",
            type=["jpg", "jpeg", "png", "heic", "heif", "pdf"],
            help="JPG, PNG, HEIC oder PDF",
            label_visibility="collapsed",
        )
        analyse_btn = st.button(
            "Analyse starten",
            disabled=uploaded_file is None,
            type="primary",
            use_container_width=True,
        )

    with col_tariffs:
        st.markdown("#### Welche Tarife vergleichen?")
        all_tariffs = load_tariffs()

        strom_tariffs = [t for t in all_tariffs if t.energieart == Energieart.STROM]
        gas_tariffs = [t for t in all_tariffs if t.energieart == Energieart.GAS]

        # Initialise checkbox state once
        for t in all_tariffs:
            key = f"tariff_{t.name}_{t.anbieter}"
            if key not in st.session_state:
                st.session_state[key] = True

        with st.expander(f"Strom-Tarife ({len(strom_tariffs)})", expanded=True):
            for t in strom_tariffs:
                key = f"tariff_{t.name}_{t.anbieter}"
                st.checkbox(f"{t.anbieter} — {t.name}", key=key)

        with st.expander(f"Gas-Tarife ({len(gas_tariffs)})", expanded=True):
            for t in gas_tariffs:
                key = f"tariff_{t.name}_{t.anbieter}"
                st.checkbox(f"{t.anbieter} — {t.name}", key=key)

        selected_count = sum(
            1 for t in all_tariffs if st.session_state.get(f"tariff_{t.name}_{t.anbieter}")
        )
        st.caption(f"{selected_count} Tarife ausgewählt")

    # Run analysis when button clicked
    if analyse_btn and uploaded_file is not None:
        file_bytes = uploaded_file.read()
        is_pdf = uploaded_file.type == "application/pdf"
        with st.spinner("Analysiere Rechnung mit KI..."):
            try:
                if is_pdf:
                    bill_data = extract_from_pdf(file_bytes)
                else:
                    bill_data = extract_bill_data(file_bytes, uploaded_file.name)
            except Exception as e:
                st.error(f"Fehler bei der Analyse: {e}")
                st.stop()
        st.session_state["bill_data"] = bill_data
        st.rerun()

# ── Post-analysis layout ────────────────────────────────────────────────────
else:
    bill_data: EnergyBillData = st.session_state["bill_data"]

    # Reset button
    if st.button("← Neue Rechnung analysieren"):
        del st.session_state["bill_data"]
        st.session_state.pop("data_confirmed", None)
        st.rerun()

    st.success("Daten erfolgreich extrahiert!")

    # ── Section 1: Collapsible data review ─────────────────────────────────
    data_confirmed = st.session_state.get("data_confirmed", False)
    with st.expander("Erkannte Rechnungsdaten", expanded=not data_confirmed):
        st.markdown("*Bitte prüfen und bei Bedarf korrigieren:*")
        col1, col2 = st.columns(2)

        with col1:
            anbieter = st.text_input("Anbieter", value=bill_data.anbieter or "")
            zahlernummer = st.text_input("Zählernummer", value=bill_data.zahlernummer or "")
            energieart_options = ["Strom", "Gas"]
            energieart_index = 1 if bill_data.energieart == Energieart.GAS else 0
            energieart = st.selectbox("Energieart", options=energieart_options, index=energieart_index)
            jahresverbrauch = st.number_input(
                "Jahresverbrauch (kWh)",
                value=bill_data.jahresverbrauch_kwh or 0.0,
                min_value=0.0,
                step=100.0,
            )

        with col2:
            arbeitspreis = st.number_input(
                "Arbeitspreis (ct/kWh)",
                value=bill_data.arbeitspreis_ct_kwh or 0.0,
                min_value=0.0,
                step=0.1,
                format="%.2f",
            )
            grundpreis = st.number_input(
                "Grundpreis (EUR/Jahr)",
                value=bill_data.grundpreis_eur_jahr or 0.0,
                min_value=0.0,
                step=1.0,
                format="%.2f",
            )
            zahlerstand_alt = st.number_input(
                "Zählerstand alt",
                value=bill_data.zahlerstand_alt or 0.0,
                step=1.0,
            )
            zahlerstand_neu = st.number_input(
                "Zählerstand neu",
                value=bill_data.zahlerstand_neu or 0.0,
                step=1.0,
            )

        if st.button("Bestätigen ✓", type="primary"):
            st.session_state["data_confirmed"] = True
            # Persist corrected values
            st.session_state["corrected_bill"] = EnergyBillData(
                anbieter=anbieter or None,
                zahlernummer=zahlernummer or None,
                energieart=Energieart(energieart),
                jahresverbrauch_kwh=jahresverbrauch if jahresverbrauch > 0 else None,
                arbeitspreis_ct_kwh=arbeitspreis if arbeitspreis > 0 else None,
                grundpreis_eur_jahr=grundpreis if grundpreis > 0 else None,
                zahlerstand_alt=zahlerstand_alt if zahlerstand_alt > 0 else None,
                zahlerstand_neu=zahlerstand_neu if zahlerstand_neu > 0 else None,
                verbrauchszeitraum_von=bill_data.verbrauchszeitraum_von,
                verbrauchszeitraum_bis=bill_data.verbrauchszeitraum_bis,
            )
            st.rerun()

    # Use confirmed bill if available, otherwise fall back to live form values
    if "corrected_bill" in st.session_state:
        corrected_bill: EnergyBillData = st.session_state["corrected_bill"]
    else:
        corrected_bill = EnergyBillData(
            anbieter=bill_data.anbieter,
            zahlernummer=bill_data.zahlernummer,
            energieart=bill_data.energieart,
            jahresverbrauch_kwh=bill_data.jahresverbrauch_kwh,
            arbeitspreis_ct_kwh=bill_data.arbeitspreis_ct_kwh,
            grundpreis_eur_jahr=bill_data.grundpreis_eur_jahr,
            zahlerstand_alt=bill_data.zahlerstand_alt,
            zahlerstand_neu=bill_data.zahlerstand_neu,
            verbrauchszeitraum_von=bill_data.verbrauchszeitraum_von,
            verbrauchszeitraum_bis=bill_data.verbrauchszeitraum_bis,
        )

    # ── Section 2: Cost summary bar ─────────────────────────────────────────
    if corrected_bill.jahresverbrauch_kwh:
        current_cost = calculate_current_cost(corrected_bill)

        st.markdown('<div class="cost-bar">', unsafe_allow_html=True)
        m1, m2, m3 = st.columns(3)
        with m1:
            cost_display = f"{current_cost:.2f} EUR" if current_cost else "—"
            st.metric("Aktuelle Jahreskosten", cost_display)
        with m2:
            if corrected_bill.arbeitspreis_ct_kwh:
                st.metric("Arbeitspreis", f"{corrected_bill.arbeitspreis_ct_kwh:.2f} ct/kWh")
            else:
                st.metric("Arbeitspreis", "—")
        with m3:
            if corrected_bill.verbrauchszeitraum_von and corrected_bill.verbrauchszeitraum_bis:
                period = f"{corrected_bill.verbrauchszeitraum_von} – {corrected_bill.verbrauchszeitraum_bis}"
            else:
                period = "—"
            st.metric("Abrechnungszeitraum", period)
        st.markdown("</div>", unsafe_allow_html=True)

        # ── Section 3: Tariff cards ─────────────────────────────────────────
        all_tariffs = load_tariffs()
        selected_names = {
            f"{t.name}_{t.anbieter}"
            for t in all_tariffs
            if st.session_state.get(f"tariff_{t.name}_{t.anbieter}", True)
        }

        comparisons = compare_tariffs(corrected_bill)
        comparisons = [
            c for c in comparisons
            if f"{c.tariff.name}_{c.tariff.anbieter}" in selected_names
        ]
        comparisons.sort(key=lambda c: (c.tariff.anbieter, c.tariff.name))

        if comparisons:
            st.markdown("#### Tarifvergleich")
            for i, comp in enumerate(comparisons):
                card_class = "tariff-card-best" if i == 0 else "tariff-card"
                st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)

                col_name, col_cost, col_save = st.columns([2, 1, 1])
                with col_name:
                    label = f"🥇 {comp.tariff.anbieter}" if i == 0 else comp.tariff.anbieter
                    st.markdown(f"**{label}**  \n{comp.tariff.name}")
                    st.caption(
                        f"Arbeitspreis: {comp.tariff.arbeitspreis_ct_kwh} ct/kWh | "
                        f"Grundpreis: {comp.tariff.grundpreis_eur_jahr:.2f} EUR/Jahr"
                    )
                with col_cost:
                    st.metric("Jahreskosten", f"{comp.jahreskosten_eur:.2f} EUR")
                with col_save:
                    if comp.ersparnis_eur > 0:
                        st.metric(
                            "Ersparnis",
                            f"{comp.ersparnis_eur:.2f} EUR",
                            delta=f"+{comp.ersparnis_eur:.2f}",
                        )
                    elif comp.ersparnis_eur < 0:
                        st.metric(
                            "Mehrkosten",
                            f"{abs(comp.ersparnis_eur):.2f} EUR",
                            delta=f"{comp.ersparnis_eur:.2f}",
                        )
                    else:
                        st.metric("Differenz", "0 EUR")

                st.markdown("</div>", unsafe_allow_html=True)

            best = comparisons[0]
            if best.ersparnis_eur > 0:
                st.success(
                    f"Empfehlung: Wechsel zu **{best.tariff.anbieter} — {best.tariff.name}**"
                    f" — du sparst ca. **{best.ersparnis_eur:.2f} EUR/Jahr**!"
                )
            else:
                st.info("Dein aktueller Tarif ist bereits der günstigste im Vergleich.")
        else:
            st.warning("Keine Tarife ausgewählt oder keine passenden Tarife gefunden.")
    else:
        st.warning("Jahresverbrauch fehlt — Tarifvergleich nicht möglich.")
