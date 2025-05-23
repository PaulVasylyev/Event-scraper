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
import pandas as pd
from datetime import date
import os

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# — Setup WebDriver —
chrome_path = os.getenv("CHROME_BIN", "/opt/chrome/chrome")
driver_path = os.getenv("CHROMEDRIVER_PATH", "/usr/local/bin/chromedriver")

options = Options()
options.binary_location = chrome_path
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")


#driver = webdriver.Chrome(service=Service("/usr/local/bin/chromedriver"), options=options)

#import the scripts of the Websites to be included in the final excel
import Websites.LifeLong_Learning_TUM as AppliedAI
import Websites.TUM as TUM
import Websites.TUM_Venture_Labs as TUM_Venture_Labs
import Websites.Social_Startup_hub as Social_Startup_hub
import Websites.Munich_Startup as Munich_Startup
import Websites.LifeLong_Learning_TUM as LifeLong_Learning_TUM
import Websites.LifeLong_Learning_TUM as ForTe
import Websites.TUM_Venture_Labs_Eventbride as TUM_Venture_Labs_Eventbride
import Websites.TUM_Venture_Labs_LuMa as TUM_Venture_Labs_LuMa

# Event-Daten sammeln
all_events = []

all_events.extend(AppliedAI.scrape())
all_events.extend(TUM.scrape())
all_events.extend(TUM_Venture_Labs.scrape())
all_events.extend(Social_Startup_hub.scrape())
all_events.extend(Munich_Startup.scrape())
all_events.extend(LifeLong_Learning_TUM.scrape())
all_events.extend(ForTe.scrape())
all_events.extend(TUM_Venture_Labs_Eventbride.scrape())
all_events.extend(TUM_Venture_Labs_LuMa.scrape())

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

# --- In CSV speichern ---
df = pd.DataFrame(all_events)
df.to_csv("scraped_events.csv", index=False, encoding="utf-8")
print(f"{len(all_events)} Events gespeichert in 'scraped_events.csv'")

# In Excel speichern
df = pd.DataFrame(all_events)
df.to_excel("scraped_events.xlsx", index=False)
print(f"{len(all_events)} Events gespeichert in 'scraped_events.xlsx'")

# Datumsformatierung in Datumsformatierung.py vornehmen
#all_events = Datumsformatierung.process_events(all_events)
subprocess.check_call([sys.executable, "Datumsformatierung.py"])

# NotionAPI.py als Subskript ausführen
subprocess.check_call([sys.executable, "NotionAPI.py"])