import streamlit as st
from dotenv import load_dotenv

from src.extractor import extract_bill_data, extract_from_pdf
from src.models import Energieart, EnergyBillData
from src.tariff_calculator import calculate_current_cost, compare_tariffs

load_dotenv()

st.set_page_config(page_title="Energierechnung Analyzer", page_icon="⚡", layout="wide")
st.title("⚡ Energierechnung Analyzer")
st.markdown("Lade ein Foto oder PDF deiner Jahresabrechnung hoch.")

uploaded_file = st.file_uploader(
    "Rechnung hochladen",
    type=["jpg", "jpeg", "png", "heic", "heif", "pdf"],
    help="Foto (JPG, PNG, HEIC) oder PDF-Scan deiner Energierechnung",
)

if uploaded_file is not None:
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

    st.success("Daten erfolgreich extrahiert!")

    # -- Extrahierte Daten anzeigen + editieren --
    st.subheader("Extrahierte Daten")
    st.markdown("*Bitte pruefen und bei Bedarf korrigieren:*")

    col1, col2 = st.columns(2)

    with col1:
        anbieter = st.text_input("Anbieter", value=bill_data.anbieter or "")
        zahlernummer = st.text_input("Zaehlernummer", value=bill_data.zahlernummer or "")
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
            "Zaehlerstand alt",
            value=bill_data.zahlerstand_alt or 0.0,
            step=1.0,
        )
        zahlerstand_neu = st.number_input(
            "Zaehlerstand neu",
            value=bill_data.zahlerstand_neu or 0.0,
            step=1.0,
        )

    # Korrigiertes Modell aus Formularwerten bauen
    corrected_bill = EnergyBillData(
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

    # -- Tarifvergleich --
    st.subheader("Tarifvergleich")

    if corrected_bill.jahresverbrauch_kwh:
        current_cost = calculate_current_cost(corrected_bill)
        if current_cost:
            st.metric("Deine aktuellen Jahreskosten", f"{current_cost:.2f} EUR")

        comparisons = compare_tariffs(corrected_bill)

        if comparisons:
            for comp in comparisons:
                col_name, col_cost, col_save = st.columns([3, 2, 2])
                with col_name:
                    st.write(f"**{comp.tariff.name}** ({comp.tariff.anbieter})")
                    st.caption(
                        f"Arbeitspreis: {comp.tariff.arbeitspreis_ct_kwh} ct/kWh | "
                        f"Grundpreis: {comp.tariff.grundpreis_eur_jahr} EUR/Jahr"
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
                st.divider()

            best = comparisons[0]
            if best.ersparnis_eur > 0:
                st.success(
                    f"Empfehlung: Wechsel zu **{best.tariff.name}** "
                    f"({best.tariff.anbieter}) -- "
                    f"du sparst ca. **{best.ersparnis_eur:.2f} EUR/Jahr**!"
                )
            else:
                st.info("Dein aktueller Tarif ist bereits der guenstigste im Vergleich.")
        else:
            st.warning("Keine passenden Tarife gefunden.")
    else:
        st.warning("Jahresverbrauch fehlt -- Tarifvergleich nicht moeglich.")
