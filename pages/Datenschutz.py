import streamlit as st

st.set_page_config(page_title="Datenschutzerklärung", page_icon="⚡")

st.title("Datenschutzerklärung")

st.markdown(
    """
    ## 1. Verantwortlicher

    Muster GmbH, Musterstraße 1, 12345 Musterstadt
    E-Mail: datenschutz@energie-funnel.de

    ## 2. Welche Daten wir erheben und warum

    ### 2.1 Energierechnung (Analysezweck)

    Sie laden Ihre Jahresabrechnung hoch, damit wir daraus Verbrauchsdaten extrahieren können.
    **Die Rechnung wird nicht gespeichert.** Sie wird ausschließlich im Arbeitsspeicher verarbeitet
    und nach der Analyse sofort verworfen.

    Die extrahierten Werte (Jahresverbrauch, Arbeitspreis, Grundpreis, Energieart) werden
    temporär in Ihrer Browser-Session gespeichert und gehen mit dem Schließen des Tabs verloren.

    **Rechtsgrundlage:** Art. 6 Abs. 1 lit. b DSGVO (Vertragsanbahnung)

    ### 2.2 Kontaktdaten bei Wechselanfrage

    Wenn Sie einen Tarifwechsel beantragen, erheben wir:
    - Vor- und Nachname
    - E-Mail-Adresse
    - Telefonnummer (optional)
    - Lieferadresse (optional)
    - Energieart und Jahresverbrauch (aus Rechnungsanalyse)
    - Angebotener Tarif und geschätzte Ersparnis

    Diese Daten werden in unserer gesicherten Datenbank gespeichert, um Ihre Wechselanfrage
    zu bearbeiten und die gesetzlich vorgeschriebene Auftragsbestätigung zu versenden.

    **Rechtsgrundlage:** Art. 6 Abs. 1 lit. b DSGVO (Vertragserfüllung / Vertragsanbahnung)

    ## 3. Verwendete Dienste (Auftragsverarbeiter)

    ### Anthropic (KI-Extraktion)
    Zur Analyse Ihrer Rechnung verwenden wir die KI-API von Anthropic, Inc., 548 Market Street,
    San Francisco, CA 94104, USA. Dabei werden Bilder Ihrer Rechnung an Anthropic übermittelt.
    Anthropic verarbeitet diese Daten ausschließlich zur Erbringung des API-Diensts.

    Wir haben mit Anthropic einen Auftragsverarbeitungsvertrag nach Art. 28 DSGVO abgeschlossen.
    Datenübertragung in die USA erfolgt auf Basis von Standardvertragsklauseln (SCCs).

    ### Supabase (Datenbankdienst)
    Ihre Kontaktdaten werden in einer Datenbank bei Supabase Inc. gespeichert, die in der
    EU (Frankfurt, AWS eu-central-1) gehostet wird.

    ### Resend (E-Mail-Versand)
    Bestätigungs-E-Mails werden über Resend, Inc. versendet. Die E-Mail-Adresse wird dabei
    an Resend übermittelt.

    ## 4. Speicherdauer

    Ihre Kontaktdaten und Wechselanfragen werden für die Dauer der Geschäftsbeziehung sowie
    den gesetzlichen Aufbewahrungsfristen (i. d. R. 10 Jahre für Geschäftskorrespondenz)
    gespeichert.

    ## 5. Ihre Rechte

    Sie haben das Recht auf:
    - **Auskunft** über Ihre gespeicherten Daten (Art. 15 DSGVO)
    - **Berichtigung** unrichtiger Daten (Art. 16 DSGVO)
    - **Löschung** Ihrer Daten (Art. 17 DSGVO)
    - **Einschränkung** der Verarbeitung (Art. 18 DSGVO)
    - **Datenübertragbarkeit** (Art. 20 DSGVO)
    - **Widerspruch** gegen die Verarbeitung (Art. 21 DSGVO)

    Zur Ausübung Ihrer Rechte wenden Sie sich an: datenschutz@energie-funnel.de

    Sie haben außerdem das Recht, sich bei der zuständigen Datenschutzaufsichtsbehörde
    zu beschweren.

    ## 6. Widerrufsrecht

    Sie können eine abgegebene Wechselanfrage innerhalb von **14 Tagen** widerrufen.
    Senden Sie hierzu eine E-Mail an widerruf@energie-funnel.de mit dem Betreff „Widerruf".

    ## 7. Cookies und Tracking

    Diese Anwendung verwendet keine Tracking-Cookies oder Analyse-Tools.
    Streamlit verwendet technisch notwendige Session-Cookies für die Funktionalität der App.

    ---

    *Stand: Mai 2026*
    """
)
