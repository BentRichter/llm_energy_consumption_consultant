import streamlit as st

st.set_page_config(page_title="Impressum", page_icon="⚡")

st.title("Impressum")

st.markdown(
    """
    **Angaben gemäß § 5 TMG**

    Muster GmbH
    Musterstraße 1
    12345 Musterstadt
    Deutschland

    **Vertreten durch:**
    Max Mustermann

    **Kontakt:**
    Telefon: +49 (0) 123 456789
    E-Mail: info@energie-funnel.de

    **Registereintrag:**
    Eintragung im Handelsregister.
    Registergericht: Amtsgericht Musterstadt
    Registernummer: HRB 12345

    **Umsatzsteuer-ID:**
    Umsatzsteuer-Identifikationsnummer gemäß § 27a Umsatzsteuergesetz:
    DE123456789

    ---

    **Verantwortlich für den Inhalt nach § 55 Abs. 2 RStV:**
    Max Mustermann
    Musterstraße 1, 12345 Musterstadt

    ---

    **Streitschlichtung**

    Die Europäische Kommission stellt eine Plattform zur Online-Streitbeilegung (OS) bereit:
    https://ec.europa.eu/consumers/odr/

    Wir sind nicht bereit oder verpflichtet, an Streitbeilegungsverfahren vor einer
    Verbraucherschlichtungsstelle teilzunehmen.
    """
)
