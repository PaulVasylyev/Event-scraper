# --- Automatisch nötige Pakete installieren ---
import sys
import subprocess
import importlib

required_packages = [
    "selenium",
    "webdriver-manager",
    "pandas",
    "openpyxl"  # wird für Excel-Export mit pandas benötigt
]

for package in required_packages:
    try:
        importlib.import_module(package.replace("-", "_"))
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# --- Imports nach der Installation ---
import csv
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import pandas as pd
from datetime import date

# — Setup WebDriver (automatisch mit webdriver-manager) —
service = Service(ChromeDriverManager().install())
options = webdriver.ChromeOptions()
options.add_argument("--headless")           # ohne UI (optional)
options.add_argument("--disable-gpu")
driver = webdriver.Chrome(service=service, options=options)

#import the scripts of the Websites to be included in the final excel
import AppliedAI
import TUM
import TUM_Venture_Labs
import Social_Startup_hub
import Munich_Startup
import LifeLong_Learning_TUM
import ForTe

import Datumsformatierung

# Event-Daten sammeln
all_events = []

all_events.extend(AppliedAI.scrape())
all_events.extend(TUM.scrape())
all_events.extend(TUM_Venture_Labs.scrape())
all_events.extend(Social_Startup_hub.scrape())
all_events.extend(Munich_Startup.scrape())
all_events.extend(LifeLong_Learning_TUM.scrape())
all_events.extend(ForTe.scrape())

seen = set()
unique_events = []
for event in all_events:
    key = (
        event['Organisation'],
        event['Titel'],
        event['Datum'],
        event['Location'],
        event['Description']
    )
    if key not in seen:
        unique_events.append(event)
        seen.add(key)

all_events = unique_events

# Datumsformatierung in Datumsformatierung.py vornehmen
all_events = Datumsformatierung.process_events(all_events)

# --- In CSV speichern ---
df = pd.DataFrame(all_events)
df.to_csv("scraped_events.csv", index=False, encoding="utf-8")
print(f"{len(all_events)} Events gespeichert in 'scraped_events.csv'")

# In Excel speichern
df = pd.DataFrame(all_events)
df.to_excel("scraped_events.xlsx", index=False)
print(f"{len(all_events)} Events gespeichert in 'scraped_events.xlsx'")

# NotionAPI.py als Subskript ausführen
subprocess.check_call([sys.executable, "NotionAPI.py"])