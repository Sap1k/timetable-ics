import streamlit as st
import pandas as pd
from datetime import datetime
import re
import uuid

# === Multilingual UI Strings ===
translations = {
    "en": {
        "title": "📅 InSIS timetab. to ICS converter",
        "description": "Upload your `.xlsx` file with your school timetable and download a calendar file you can import into your favorite calendar app.",
        "help": "You can find the required data in InSIS \n* My college -> Course registrations -> Display timetables.\n* Type of list: particular in days, format: list of timetable items, date range for the entire semester. \n* The \"Export to Excel\" button will download the required file.",
        "upload": "Upload Excel file (.xlsx)",
        "timezone": "Select your time zone",
        "generate": "Generate ICS",
        "download": "📥 Download ICS",
        "preview": "Preview of your data",
        "success": "Excel file loaded successfully!",
        "error": "⚠️ Something went wrong:",
    },
    "cz": {
        "title": "📅 Převod rozvrhu z InSISu na ICS",
        "description": "Nahraj svůj soubor `.xlsx` s rozvrhem a stáhni si kalendář, který si můžeš importovat do svojí oblíbené aplikace kalendáře.",
        "help": "Data najdeš v InSISu \n* Moje studium -> Zápisy předmětů -> Zobrazení rozvrhů. \n* Typ seznamu: konkrétní ve dnech, formát: seznam rozvrhových akcí, od/do pro celý semestr. \n* Tlačítko \"Export do Excelu\" stáhne požadovaný soubor.",
        "upload": "Nahraj Excel soubor (.xlsx)",
        "timezone": "Vyber časové pásmo",
        "generate": "Vygenerovat ICS",
        "download": "📥 Stáhnout ICS",
        "preview": "Náhled dat",
        "success": "Excel byl úspěšně načten!",
        "error": "⚠️ Něco se pokazilo:",
    }
}

# === Setup page ===
st.set_page_config(page_title="ICS Generator", layout="centered")

# === Language Selection ===
lang = st.selectbox("🌐 Jazyk / Language", options=["cz", "en"], format_func=lambda x: {"cz": "Čeština", "en": "English"}[x])
t = translations[lang]

st.title(t["title"])
st.markdown(t["description"])
st.markdown(t["help"])

# === File Upload ===
uploaded_file = st.file_uploader(t["upload"], type="xlsx")

# === Helper to parse Czech-style dates ===
def parse_datetime(date_str, time_str):
    match = re.search(r"(\d{2}\.\d{2}\.\d{4})", str(date_str))
    if match:
        full_str = f"{match.group(1)} {time_str}"
        try:
            return datetime.strptime(full_str, "%d.%m.%Y %H:%M")
        except ValueError:
            return None
    return None

# === Process File ===
if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        st.success(t["success"])
        st.markdown(f"### {t['preview']}")
        st.dataframe(df.head())

        timezone = "Europe/Prague"

        if st.button(t["generate"]):
            ics = [
                "BEGIN:VCALENDAR",
                "VERSION:2.0",
                "PRODID:-//Schedule Export//EN",
                "CALSCALE:GREGORIAN"
            ]

            for _, row in df.iterrows():
                start = parse_datetime(row["Den"], row["Od"])
                end = parse_datetime(row["Den"], row["Do"])
                if not start or not end:
                    continue

                uid = str(uuid.uuid4())
                dtstart = start.strftime("%Y%m%dT%H%M%S")
                dtend = end.strftime("%Y%m%dT%H%M%S")
                summary = f"{row['Předmět']} – {row['Akce']}"
                location = row.get("Místnost", "")
                description = (
                    f"Vyučující: {row.get('Vyučující', '')}\\n"
                    f"Omezení: {row.get('Omezení', '')}\\n"
                    f"Kapacita: {row.get('Kapacita', '')}"
                )

                ics.extend([
                    "BEGIN:VEVENT",
                    f"UID:{uid}",
                    f"DTSTART;TZID={timezone}:{dtstart}",
                    f"DTEND;TZID={timezone}:{dtend}",
                    f"SUMMARY:{summary}",
                    f"LOCATION:{location}",
                    f"DESCRIPTION:{description}",
                    "END:VEVENT"
                ])

            ics.append("END:VCALENDAR")
            ics_content = "\n".join(ics)

            st.download_button(t["download"], data=ics_content, file_name="timetable.ics", mime="text/calendar")

    except Exception as e:
        st.error(f"{t['error']} {e}")
