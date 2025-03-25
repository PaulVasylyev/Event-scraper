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

NOTION_TOKEN = "SECRET_NotionToken"  # Dein Integration Token
DATABASE_ID = "SECRET_NotionDatabaseLink"  # Deine Datenbank-ID

# === HEADER ===
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

# Ausführen
notion_to_csv(DATABASE_ID)

# Dateien laden
scraped = pd.read_csv("scraped_events.csv")
notion = pd.read_csv("notion_export.csv")

# Normieren (klein schreiben, trimmen) für sauberen Vergleich
scraped["Titel"] = scraped["Titel"].astype(str).str.strip().str.lower()
scraped["Description"] = scraped["Description"].astype(str).str.strip()

notion["Titel"] = notion["Titel"].astype(str).str.strip().str.lower()
notion["Description"] = notion["Description"].astype(str).str.strip()

# Inner Merge → Zeilen, die sowohl in scraped als auch in notion vorkommen
duplikate = pd.merge(scraped, notion, on=["Titel", "Description"], how="inner")

# Übrig bleiben nur Events, die nicht in Notion sind
bereinigt = scraped[~scraped.set_index(["Titel", "Description"]).index.isin(duplikate.set_index(["Titel", "Description"]).index)]

# Überschreiben der Originaldatei
bereinigt.to_csv("scraped_events.csv", index=False, encoding="utf-8")
print(f"✅ {len(duplikate)} Duplikate entfernt. Neue scraped_events.csv gespeichert mit {len(bereinigt)} Zeilen.")


def parse_date(value):
    try:
        parsed = parser.parse(value, fuzzy=True)
        return parsed.isoformat()
    except Exception:
        return None
    
# === HILFSFUNKTION ===
def create_page(row):
    iso_date = parse_date(str(row["Datum"]))

    properties = {
        "Organisation": {
            "title": [{
                "text": {"content": str(row["Organisation"])}
            }]
        },
        "Titel": {
            "rich_text": [{
                "text": {"content": str(row["Titel"])}
            }]
        },
        "Location": {
            "rich_text": [{
                "text": {"content": str(row["Location"])}
            }]
        },
        "Description": {
            "rich_text": [{
                "text": {"content": str(row["Description"])}
            }]
        },
        "Link": {
            "url": str(row["Link"])
        }
    }

    if iso_date:
        properties["Datum"] = {
            "date": {
                "start": iso_date
            }
        }

    payload = {
        "parent": { "database_id": DATABASE_ID },
        "properties": properties
    }

    response = requests.post("https://api.notion.com/v1/pages", headers=headers, json=payload)

    if response.status_code != 200:
        print("Fehler:", response.status_code, response.text)
    else:
        print("Erfolgreich hinzugefügt:", row["Organisation"])

# === IMPORT STARTEN ===
def import_csv_to_notion(csv_path):
    df = pd.read_csv(csv_path)

    # Optional: Spaltennamen bereinigen
    df.columns = [col.strip() for col in df.columns]

    for _, row in df.iterrows():
        create_page(row)
        time.sleep(0.3)  # API-Ratenlimit beachten

# === START ===
if __name__ == "__main__":
    import_csv_to_notion("scraped_events.csv")

# Dateinamen
files_to_delete = ["scraped_events.csv", "notion_export.csv"]

for file in files_to_delete:
    try:
        os.remove(file)
        print(f"🗑️ Datei gelöscht: {file}")
    except FileNotFoundError:
        print(f"⚠️ Datei nicht gefunden: {file}")
    except Exception as e:
        print(f"❌ Fehler beim Löschen von {file}: {e}")