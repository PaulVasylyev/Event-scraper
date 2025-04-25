try:
    from dateutil import parser
except ImportError:
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-dateutil"])
    from dateutil import parser

import sys
sys.stdout.reconfigure(encoding='utf-8')

import pandas as pd
import requests
import time
import os

FAILED_EVENTS = []       # Liste für fehlgeschlagene Uploads

# === KONFIGURATION ===
NOTION_TOKEN = os.getenv("SECRET_NotionToken")
DATABASE_ID = os.getenv("SECRET_NotionDatabaseLink")
CSV_PATH = "scraped_events_formatted.csv"  # Pfad zur CSV-Datei

# === HEADER für Notion API ===
headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

def get_database_rows(database_id):
    url = f"https://api.notion.com/v1/databases/{database_id}/query"
    rows = []

    while url:
        response = requests.post(url, headers=headers)
        data = response.json()
        rows.extend(data.get("results", []))
        url = data.get("next_cursor")
        if url:
            time.sleep(0.3)

    return rows

def extract_plain_text(property_obj):
    if "title" in property_obj:
        return "".join([t["text"]["content"] for t in property_obj["title"]])
    elif "rich_text" in property_obj:
        return "".join([t["text"]["content"] for t in property_obj["rich_text"]])
    elif "date" in property_obj and property_obj["date"]:
        return property_obj["date"]["start"]
    elif "url" in property_obj:
        return property_obj["url"]
    else:
        return ""

def notion_to_csv(database_id, output_csv="notion_export.csv"):
    rows = get_database_rows(database_id)
    data = []

    for row in rows:
        props = row["properties"]
        data.append({
            "Organisation": extract_plain_text(props.get("Organisation", {})),
            "Titel": extract_plain_text(props.get("Titel", {})),
            "Datum": extract_plain_text(props.get("Datum", {})),
            "Location": extract_plain_text(props.get("Location", {})),
            "Description": extract_plain_text(props.get("Description", {})),
            "Link": extract_plain_text(props.get("Link", {}))
        })

    df = pd.DataFrame(data)

    if df.empty:
        print("⚠️ Keine Daten vorhanden - leere Datei mit Spalten wird geschrieben.")
        df = pd.DataFrame(columns=["Organisation", "Titel", "Datum", "Location", "Description", "Link"])

    df.to_csv(output_csv, index=False, encoding="utf-8")
    print(f"✅ Exportiert nach {output_csv}")

# Notion-Daten exportieren
notion_to_csv(DATABASE_ID)

# Dateien laden
scraped = pd.read_csv("scraped_events_formatted.csv")
notion = pd.read_csv("notion_export.csv")

# Normieren der Links (trimmen und in Kleinbuchstaben, damit der Vergleich funktioniert)
scraped["Link"] = scraped["Link"].astype(str).str.strip().str.lower()
notion["Link"] = notion["Link"].astype(str).str.strip().str.lower()

# Inner Merge → Zeilen, die sowohl in scraped als auch in notion vorkommen (basierend auf "Link")
duplikate = pd.merge(scraped, notion, on=["Link"], how="inner")

# Übrig bleiben nur Events, die nicht in Notion vorhanden sind (basierend auf "Link")
bereinigt = scraped[~scraped.set_index("Link").index.isin(duplikate.set_index("Link").index)]

# Überschreiben der Originaldatei
bereinigt.to_csv("scraped_events_formatted.csv", index=False, encoding="utf-8")
print(f"✅ {len(duplikate)} Duplikate entfernt. Neue scraped_events_formatted.csv gespeichert mit {len(bereinigt)} Zeilen.")

# === FUNKTION: ISO-Datum mit oder ohne Enddatum parsen
def parse_date_range_iso(value):
    try:
        if " - " in value:
            start, end = value.split(" - ", 1)
            return {
                "start": start.strip(),
                "end": end.strip()
            }
        else:
            return {
                "start": value.strip()
            }
    except Exception:
        return None

# === FUNKTION: Bereits vorhandene Events aus Notion abrufen
def get_existing_events():
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    payload = {}
    existing_events = []
    has_more = True
    next_cursor = None

    while has_more:
        if next_cursor:
            payload = {"start_cursor": next_cursor}
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            print("❌ Fehler beim Abrufen der bestehenden Events:", response.status_code, response.text)
            return existing_events
        data = response.json()
        for result in data.get("results", []):
            # Annahme: Datum ist in der Property "Date" (als ISO-String) und Beschreibung in "Description"
            date_val = None
            description_val = None
            if "Date" in result["properties"]:
                date_field = result["properties"]["Date"]["date"]
                if date_field is not None:
                    date_val = date_field.get("start", None)
            if "Description" in result["properties"]:
                rich_text = result["properties"]["Description"]["rich_text"]
                if rich_text and len(rich_text) > 0:
                    description_val = rich_text[0]["text"]["content"]
            # Nur Events mit beiden Angaben aufnehmen
            if date_val and description_val:
                existing_events.append((date_val.strip(), description_val.strip()))
        has_more = data.get("has_more", False)
        next_cursor = data.get("next_cursor", None)
    return set(existing_events)

# === FUNKTION: Notion-Page erstellen
def create_page(row):
    """Legt einen Datensatz in Notion an.
       Scheitert der Aufruf, wird das Event + Fehlermeldung gespeichert."""
    date_obj = parse_date_range_iso(str(row["Datum"]))

    properties = {
        "Title":        {"title":      [{"text": {"content": str(row["Titel"])}}]},
        "Organisation": {"rich_text":  [{"text": {"content": str(row["Organisation"])}}]},
        "Location":     {"rich_text":  [{"text": {"content": str(row["Location"])}}]},
        "Description":  {"rich_text":  [{"text": {"content": str(row["Description"])}}]},
        "Link":         {"url": str(row["Link"])}
    }
    if date_obj:
        properties["Date"] = {"date": date_obj}

    payload = {"parent": {"database_id": DATABASE_ID}, "properties": properties}

    try:
        resp = requests.post(
            "https://api.notion.com/v1/pages",
            headers=headers,
            json=payload,
            timeout=15          # Netzwerk-Timeout
        )
        if resp.status_code != 200:
            # Fehler protokollieren, aber Programm weiterführen
            FAILED_EVENTS.append({
                "Titel": row["Titel"],
                "Datum": row["Datum"],
                "Fehlercode": resp.status_code,
                "Fehlertext": resp.text
            })
            print(f"❌ Fehler {resp.status_code}: {row['Titel']} → geloggt")
        else:
            print("✅ Hinzugefügt:", row["Titel"])
    except Exception as e:
        # Unvorhergesehene Ausnahmen ebenfalls festhalten
        FAILED_EVENTS.append({
            "Titel": row["Titel"],
            "Datum": row["Datum"],
            "Fehlercode": "Exception",
            "Fehlertext": str(e)
        })
        print(f"❌ Exception bei {row['Titel']} → geloggt")

# === FUNKTION: CSV verarbeiten und in Notion importieren
def import_csv_to_notion(csv_path):
    df = pd.read_csv(csv_path)
    df.columns = [c.strip() for c in df.columns]

    for _, row in df.iterrows():
        create_page(row)
        time.sleep(0.3)          # API-Rate-Limit

    # Nach der Schleife evtl. Fehlversuche sichern
    if FAILED_EVENTS:
        pd.DataFrame(FAILED_EVENTS).to_csv(
            "notion_failed_events.csv", index=False, encoding="utf-8"
        )
        print(f"⚠️ {len(FAILED_EVENTS)} fehlgeschlagene Events in notion_failed_events.csv gespeichert")
    else:
        print("🎉 Alle Events erfolgreich übertragen")

# === START
if __name__ == "__main__":
    import_csv_to_notion(CSV_PATH)

# Optional: Dateien löschen
files_to_delete = ["scraped_events_formatted.csv", "notion_export.csv", "scraped_events_formatted.xlsx"]

for file in files_to_delete:
    try:
        os.remove(file)
        print(f"🗑️ Datei gelöscht: {file}")
    except FileNotFoundError:
        print(f"⚠️ Datei nicht gefunden: {file}")
    except Exception as e:
        print(f"❌ Fehler beim Löschen von {file}: {e}")