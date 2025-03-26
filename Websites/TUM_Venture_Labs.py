from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import time

from selenium.webdriver.chrome.options import Options
options = Options()
options.add_argument("--headless")  # Kein GUI
options.add_argument("--disable-gpu")  # Für Kompatibilität
options.add_argument("--window-size=1920,1080")  # Optional für konsistentes Verhalten

def scrape():
    # Scraped Event-Daten von TUM und gibt sie als Liste von Directories zurück.
    driver = webdriver.Chrome(options=options)
    driver.get("https://www.tum-venture-labs.de/events")
    time.sleep(2)

    # Cookie-Banner schließen
    try:
        cookie_button = driver.find_element(By.XPATH, "//*[@id='CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll']")
        cookie_button.click()
        time.sleep(2)
    except NoSuchElementException:
        pass

    # Zuerst alle Event-Links sammeln
    event_links = []
    link_elements = driver.find_elements(By.XPATH, "//*[@id='events-list']/div[1]/div/div/div/div[2]/h3/a")
    for link in link_elements:
        event_links.append(link.get_attribute("href"))

    events = []

    # Bestimme die Anzahl der Events
    event_count = len(event_links)
    print(f"Gefundene Events: {event_count}")

    # Jetzt über jeden Link iterieren
    for i in range(event_count):
        driver.get(event_links[i])
        time.sleep(3)  # Warten, bis die Seite vollständig geladen ist

        # Titel extrahieren
        try:
            title_element = driver.find_element(By.XPATH, "//*[@id='main']/header/section[1]/div/h1")
            title = title_element.text.strip()
            print(f"Event {i+1} - Titel: {title}")
        except Exception as e:
            title = "Kein Titel gefunden"
            print(f"Event {i+1} - Fehler beim Extrahieren des Titels: {e}")

        # Datum extrahieren
        try:
            date_element = driver.find_element(By.XPATH, "//*[@id='main']/header/section[2]/div/div[1]/div[1]/dl/div[1]/dd")
            date = date_element.text.strip()
            print(f"Event {i+1} - Datum: {date}")
        except Exception as e:
            date = "Kein Datum gefunden"
            print(f"Event {i+1} - Fehler beim Extrahieren des Datums: {e}")

        # Location extrahieren
        try:
            location_element = driver.find_element(By.XPATH, "//*[@id='main']/header/section[2]/div/div[1]/div[1]/dl/div[2]/dd")
            location = location_element.text.strip()
            print(f"Event {i+1} - Location: {location}")
        except Exception as e:
            location = ""
            #location = "Kein Location gefunden"
            print(f"Event {i+1} - Fehler beim Extrahieren der Location: {e}")

        # Description Extrahieren
        try:
            description_element = driver.find_element(By.XPATH, "//*[@id='main']/header/section[2]/div/div[1]/div[1]/div")
            description = description_element.text.strip()
            print(f"Event {i+1} - Description: {description[:50]}")
        except Exception as e:
            description = "Keine Description gefunden"
            print(f"Event {i+1} - Fehler beim Extrahieren des Description: {e}")

        try:
            if len(description) > 2000:
                truncated = description[:1997]                         # hart auf 1997 kürzen
                truncated = truncated.rsplit(' ', 1)[0] + '...'        # am letzten Leerzeichen cutten und "..." anhängen
                description = truncated
            else:
                pass
        except Exception:
            pass

        # Link Extrahieren
        try:
            link = driver.current_url
            print(f"Event {i+1} - Link: {link}")
        except Exception as e:
            link = "Kein Link gefunden"
            print(f"Event {i+1} - Fehler beim Extrahieren des Links: {e}")
        

        # Speichern in Events
        events.append({
            "Organisation": "TUM Venture Labs",
            "Titel": title,
            "Datum": date,
            "Location": location,
            "Description": description,
            "Link": link,
        })

    #Rückgabe von den gesammelten Events an das main Programm
    driver.quit()
    return events