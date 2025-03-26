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
    driver.get("https://lu.ma/vlsa?compact=true")
    time.sleep(5)

    # Bestimme die Anzahl der Container
    container_count = len(driver.find_elements(By.XPATH, "//*[@id='__next']/div/div/div[2]/div/div/div[2]/div/div[2]/div"))

    # Bestimme die Anzahl der Events
    xpath_events = f"//*[@id='__next']/div/div/div[2]/div/div/div[2]/div/div[2]/div[{container_count}]/div[1]/div"
    event_count = len(driver.find_elements(By.XPATH, xpath_events))
    print(f"Gefundene Events: {event_count}")

    events = []

    event_links = []

    # Link extrahieren
    for i in range(event_count):
        try:
            xpath_link = f"//*[@id='__next']/div/div/div[2]/div/div/div[2]/div/div[2]/div[{container_count}]/div[1]/div[{i+1}]/div[2]/a"
            link_address = driver.find_element(By.XPATH, xpath_link)
            link = link_address.get_attribute("href")
            
            # Überspringe Links, die mit "http" beginnen
            if link.startswith("https://lu.ma/"):
                print(f"Event {i+1} - Link: {link}")
                event_links.append(link)
            else:
                print(f"Event {i+1} - Link wird übersprungen: {link}")
                continue
        except Exception as e:
            print(f"Event {i+1} - Fehler beim Extrahieren des Links: {e}")


    # Jetzt über jeden Link iterieren
    for i in range(len(event_links)):
        driver.get(event_links[i])
        time.sleep(4)  # Warten, bis die Seite vollständig geladen ist

        # Titel extrahieren
        try:
            title_element = driver.find_element(By.XPATH, "//*[@id='__next']/div/div[2]/div/div/div[7]/div/div[2]/div[1]/div/div[1]/div/h1")
            title = title_element.text.strip()
            print(f"Event {i+1} - Titel: {title}")
        except Exception as e:
            title = "Kein Titel gefunden"
            print(f"Event {i+1} - Fehler beim Extrahieren des Titels: {e}")

        # View all event details button
        try:
            view_button = driver.find_element(By.XPATH, "//*[@id='root']/div/div/div[2]/div/div/div/div[1]/div/main/div[1]/div[1]/div[2]/div[2]/div[1]/div[11]/div[1]/div/button")
            view_button.click()
            time.sleep(1)
        except NoSuchElementException:
            pass

        # Datum extrahieren
        try:
            # Start-Datum und Zeit extrahieren
            date_elements = driver.find_elements(By.XPATH, "//*[@id='__next']/div/div[2]/div/div/div[7]/div/div[2]/div[1]/div/div[3]/div/div[1]/div[2]/div")
            date1 = date_elements[0].text.strip()
            date2 = date_elements[1].text.strip()
            date = f'{date1} {date2}'
            print(f"Event {i+1} - Datum: {date}")
        except Exception as e:
            date = "Kein Datum gefunden"
            print(f"Event {i+1} - Fehler beim Extrahieren des Datums: {e}")

        # Location extrahieren
        try:
            location_elements = driver.find_element(By.XPATH, "//*[@id='__next']/div/div[2]/div/div/div[7]/div/div[2]/div[1]/div/div[3]/a/div/div[2]/div/div/div[1]")
            location = location_elements.text.strip()
            print(f"Event {i+1} - Location: {location}")
        except Exception as e:
            location = ""
            #location = "Kein Location gefunden"
            print(f"Event {i+1} - Fehler beim Extrahieren der Location: {e}")

        # Description Extrahieren
        try:
            description_element = driver.find_element(By.XPATH, "//*[@id='__next']/div/div[2]/div/div/div[7]/div/div[2]/div[3]/div[2]/div")
            description = description_element.text.strip()
            print(f"Event {i+1} - Description: {description[:50]}")
        except Exception as e:
            description = "Keine Description gefunden"
            print(f"Event {i+1} - Fehler beim Extrahieren des Description: {e}")

        try:
            if len(description) > 2000:
                truncated = description[:1800]                         # hart auf 1997 kürzen
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