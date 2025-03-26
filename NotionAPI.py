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

try:
    SECRET_NotionToken = os.environ["SECRET_NotionToken"]
except KeyError:
    # Dateinamen
    files_to_delete = ["scraped_events.csv", "scraped_events.xlsx"]

    for file in files_to_delete:
        try:
            os.remove(file)
            print(f"🗑️ Datei gelöscht: {file}")
        except FileNotFoundError:
            print(f"⚠️ Datei nicht gefunden: {file}")
        except Exception as e:
            print(f"❌ Fehler beim Löschen von {file}: {e}")

    SOME_SECRET = "NotionToken not available!"
    sys.exit(1)

try:
    SECRET_NotionDatabaseLink = os.environ["SECRET_NotionDatabaseLink"]
except KeyError:
    # Dateinamen
    files_to_delete = ["scraped_events.csv", "scraped_events.xlsx"]

    for file in files_to_delete:
        try:
            os.remove(file)
            print(f"🗑️ Datei gelöscht: {file}")
        except FileNotFoundError:
            print(f"⚠️ Datei nicht gefunden: {file}")
        except Exception as e:
            print(f"❌ Fehler beim Löschen von {file}: {e}")

    SECRET_NotionDatabaseLink = "DatabaseLink not available!"
    sys.exit(1)

NOTION_TOKEN = f"{SECRET_NotionToken}"  # Dein Integration Token
DATABASE_ID = f"{SECRET_NotionDatabaseLink}"  # Deine Datenbank-ID

# === HEADER für Notion API ===
headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

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

# === FUNKTION: Notion-Page erstellen
def create_page(row):
    date_obj = parse_date_range_iso(str(row["Datum"]))

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

    if date_obj:
        properties["Datum"] = {
            "date": date_obj
        }

    payload = {
        "parent": {"database_id": DATABASE_ID},
        "properties": properties
    }

    response = requests.post("https://api.notion.com/v1/pages", headers=headers, json=payload)

    if response.status_code != 200:
        print("❌ Fehler:", response.status_code, response.text)
    else:
        print("✅ Hinzugefügt:", row["Organisation"])

# === FUNKTION: CSV verarbeiten und importieren
def import_csv_to_notion(csv_path):
    df = pd.read_csv(csv_path)
    df.columns = [col.strip() for col in df.columns]

    for _, row in df.iterrows():
        create_page(row)
        time.sleep(0.3)  # API-Ratenlimit beachten

# === START
if __name__ == "__main__":
    import_csv_to_notion("scraped_events.csv")

# Dateinamen
files_to_delete = ["scraped_events.csv", "notion_export.csv", "scraped_events.xlsx"]

for file in files_to_delete:
    try:
        os.remove(file)
        print(f"🗑️ Datei gelöscht: {file}")
    except FileNotFoundError:
        print(f"⚠️ Datei nicht gefunden: {file}")
    except Exception as e:
        print(f"❌ Fehler beim Löschen von {file}: {e}")