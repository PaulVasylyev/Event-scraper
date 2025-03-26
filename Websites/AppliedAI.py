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
    # Scrapt Event-Daten von AppliedAI und gibt sie als Liste von Dictionaries zurück.
    driver = webdriver.Chrome(options=options)
    driver.get("https://community.appliedai.de/events?view=list")
    time.sleep(2)

    # Cookie-Banner ggf. schließen
    try:
        cookie_button = driver.find_element(By.XPATH, "/html/body/div[3]/div[2]/div/div[2]/div[1]/div[2]/button[2]/div/span")
        cookie_button.click()
        time.sleep(1)
    except NoSuchElementException:
        pass

    # Bestimme die Anzahl der Events
    event_count = len(driver.find_elements(By.XPATH, "//*[@id='po-main-container']/div/div/div[2]/div/div/div/div/div[2]/div/div[2]/div"))
    print(f"Gefundene Events: {event_count}")

    events = []

    for i in range(event_count):
        # Hole die Event-Container neu ab, da sich die Elemente nach einem Seiten-Reload ändern
        event_containers = driver.find_elements(By.XPATH, "//*[@id='po-main-container']/div/div/div[2]/div/div/div/div/div[2]/div/div[2]/div")
        
        # Greife auf das aktuelle Event zu
        try:
            current_event = event_containers[i]
        except IndexError:
            print(f"Kein Event-Container für Index {i} gefunden.")
            continue

        # Cookie-Banner ggf. erneut schließen
        try:
            cookie_button = driver.find_element(By.XPATH, "/html/body/div[3]/div[2]/div/div[2]/div[1]/div[2]/button[2]/div/span")
            cookie_button.click()
            time.sleep(1)
        except NoSuchElementException:
            pass

        try:
            # Verwende einen relativen XPath für den Button innerhalb des aktuellen Containers
            button = current_event.find_element(By.XPATH, ".//div[2]/div/div")
            driver.execute_script("arguments[0].click();", button)
            print(f"Event {i+1} wurde angeklickt.")
            time.sleep(5)  # Warte, bis die Detailseite geladen ist

            # Titel extrahieren
            try:
                title_element = driver.find_element(By.XPATH, "//h1[@data-testid='event-title']")
                title = title_element.text.strip()
                print(f"Event {i+1} - Titel: {title}")
            except Exception as e:
                title = "Kein Titel gefunden"
                print(f"Event {i+1} - Fehler beim Extrahieren des Titels: {e}")

            # Datum extrahieren
            try:
                date_element = driver.find_element(By.XPATH, "//*[@id='event-wrapper']/aside/div[1]/div[2]/time")
                date_unstriped = date_element.text.strip()
                date = date_unstriped.replace(" CEST", "").strip()
                print(f"Event {i+1} - Datum: {date}")
            except Exception as e:
                date = "Kein Datum gefunden"
                print(f"Event {i+1} - Fehler beim Extrahieren des Datums: {e}")
            
            # Location extrahieren
            try:
                location_element = driver.find_element(By.XPATH, "//*[@id='event-wrapper']/aside/div[1]/div[2]/span")
                location = location_element.text.strip()
                print(f"Event {i+1} - Location: {location}")
            except Exception as e:
                location = "Kein Location gefunden"
                print(f"Event {i+1} - Fehler beim Extrahieren der Location: {e}")

            # Description Extrahieren
            try:
                description_element = driver.find_element(By.XPATH, "//*[@id='event-wrapper']/main/div/div/div/div")
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
                "Organisation": "AppliedAI",
                "Titel": title,
                "Datum": date,
                "Location": location,
                "Description": description,
                "Link": link,
            })

            # Zurück zur Event-Übersicht
            driver.get("https://community.appliedai.de/events?view=list")
            time.sleep(3)
            
        except Exception as e:
            print(f"Kein Button gefunden für Event {i+1}: {e}")

    #Rückgabe von den gesammelten Events an das main Programm
    driver.quit()
    return events