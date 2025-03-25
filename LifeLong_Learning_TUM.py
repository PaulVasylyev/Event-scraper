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
    driver.get("https://www.lll.tum.de/events/")
    time.sleep(2)

    # Bestimme die Anzahl der Events
    event_count = len(driver.find_elements(By.XPATH, "//*[@id='events_query']/div/div/div"))
    print(f"Gefundene Events: {event_count}")

    events = []

    for i in range(event_count):

        # Titel extrahieren
        try:
            xpath_title = f'//*[@id="events_query"]/div/div/div[{i+1}]/div/div[2]/p[2]'
            title_element = driver.find_element(By.XPATH, xpath_title)
            title = title_element.text.strip()
            print(f"Event {i+1} - Titel: {title}")
        except Exception as e:
            title = "Kein Titel gefunden"
            print(f"Event {i+1} - Fehler beim Extrahieren des Titels: {e}")

        # Datum extrahieren
        try:
            xpath_date = f'//*[@id="events_query"]/div/div/div[{i+1}]/div/div[1]'
            date_element = driver.find_element(By.XPATH, xpath_date)

            element = driver.find_element(By.XPATH, xpath_date)

            # Hole alle untergeordneten Textelemente einzeln und füge sie mit Leerzeichen zusammen
            texts = element.find_elements(By.XPATH, './/*')
            text_list = [t.text.strip() for t in texts if t.text.strip()]
            date_1 = ' '.join(text_list)

            xpath_extra = f'//*[@id="events_query"]/div/div/div[{i+1}]/div/div[3]/p[1]'
            extra_element = driver.find_element(By.XPATH, xpath_extra)
            extra_text = extra_element.text.strip()

            cleaned = extra_text.replace("Zeit:", "").strip()
            date = f"{date_1} {cleaned}"

            #date = date_element.text.strip()
            print(f"Event {i+1} - Datum: {date}")
        except Exception as e:
            date = "Kein Datum gefunden"
            print(f"Event {i+1} - Fehler beim Extrahieren des Datums: {e}")

        # Location
        try:
            xpath_location = f'//*[@id="events_query"]/div/div/div[{i+1}]/div/div[2]/p[1]'
            location_element = driver.find_element(By.XPATH, xpath_location)
            location = location_element.text.strip()
            print(f"Event {i+1} - Location: {location}")
        except Exception as e:
            location = "Kein Location gefunden"
            print(f"Event {i+1} - Fehler beim Extrahieren der Location: {e}")
        
        # Description Extrahieren
        try:
            xpath_description = f'//*[@id="events_query"]/div/div/div[{i+1}]/div/div[2]/p[4]'
            description_element = driver.find_element(By.XPATH, xpath_description)
            description = description_element.text.strip()
            print(f"Event {i+1} - Description: {description}")
        except Exception as e:
            description = "Kein Description gefunden"
            print(f"Event {i+1} - Fehler beim Extrahieren der Description: {e}")

        try:
            if len(description) > 2000:
                truncated = description[:1997]                         # hart auf 1997 kürzen
                truncated = truncated.rsplit(' ', 1)[0] + '...'        # am letzten Leerzeichen cutten und "..." anhängen
                description = truncated
            else:
                pass
        except Exception:
            pass

        # Link extrahieren
        try:
            xpath_link = f'//*[@id="events_query"]/div/div/div[{i+1}]/div/div[3]/div/div/a'
            link_address = driver.find_element(By.XPATH, xpath_link)
            link = link_address.get_attribute("href")
            print(f"Event {i+1} - Link: {link}")
        except Exception as e:
            link = "Kein Link gefunden"
            print(f"Event {i+1} - Fehler beim Extrahieren des Links: {e}")


        # Speichern in Events
        events.append({
            "Organisation": "LifeLong Learning TUM",
            "Titel": title,
            "Datum": date,
            "Location": location,
            "Description": description,
            "Link": link,
        })

    #Rückgabe von den gesammelten Events an das main Programm
    driver.quit()
    return events