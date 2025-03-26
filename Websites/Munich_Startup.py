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
    
    # Aktuelles Datum abrufen
    from datetime import date
    heute = date.today().isoformat()
    print(heute)  # z.B. 2025-03-21

    # Scraped Event-Daten von TUM und gibt sie als Liste von Directories zurück.
    driver = webdriver.Chrome(options=options)
    url_heute = f'https://www.munich-startup.de/veranstaltungen/liste/?tribe_paged=1&tribe_event_display=list&tribe-bar-date={heute}'
    driver.get(url_heute)
    time.sleep(2)

    # Cookie-Banner schließen
    try:
        cookie_button = driver.find_element(By.XPATH, "//*[@id='BorlabsCookieBox']/div/div/div[2]/div/div/div[2]/div/div/div/div/div/div/div[3]/div/div[1]/button")
        cookie_button.click()
        time.sleep(2)
    except NoSuchElementException:
        pass

    events = []

    for Seite in range(1, 5):
        url_Seite = f'https://www.munich-startup.de/veranstaltungen/liste/?tribe_paged={Seite}&tribe_event_display=list&tribe-bar-date={heute}'
        driver.get(url_Seite)
        time.sleep(2)

        # Bestimme die Anzahl der Events
        event_count = len(driver.find_elements(By.XPATH, "/html/body/div[1]/main/div[1]/div/div[2]/div[2]/div/div[1]/div")) - 1
        print(f"Gefundene Events: {event_count}")

        # Zuerst alle Events-Links sammeln
        event_links = []
        for i in range(1, event_count + 1):
            xpath_event_container_links_div_unfiltered = f'/html/body/div[1]/main/div[1]/div/div[2]/div[2]/div/div[1]/div[{i+1}]/div'
            event_container_links_div_elements = driver.find_elements(By.XPATH, xpath_event_container_links_div_unfiltered)
            event_container_links_div_amount = len(event_container_links_div_elements)
            xpath_event_container_links_div_filtered = f'/html/body/div[1]/main/div[1]/div/div[2]/div[2]/div/div[1]/div[{i+1}]/div[{event_container_links_div_amount}]/h3/a'
            try:
                link = driver.find_element(By.XPATH, xpath_event_container_links_div_filtered)
            except Exception:
                link = ""
            try:
                event_links.append(link.get_attribute("href"))
            except Exception:
                driver.quit()
                return events        
            
        #Jetzt über jeden Link iterieren
        for i in range(event_count):
            driver.get(event_links[i])
            time.sleep(3)  # Warten, bis die Seite vollständig geladen ist

            # Titel extrahieren
            try:
                title_element = driver.find_element(By.XPATH, "/html/body/div[1]/main/div/div/div[2]/div[4]/div[1]/div/div[1]/h1")
                title = title_element.text.strip()
                print(f"Event {i+1} - Titel: {title}")
            except Exception as e:
                title = "Kein Titel gefunden"
                print(f"Event {i+1} - Fehler beim Extrahieren des Titels: {e}")

            # Datum extrahieren 
            try:
                #date_elements = driver.find_elements(By.XPATH, "/html/body/div[1]/main/div/div/div[2]/div[4]/div[1]/div/div[2]/div/div[1]/dl/dd[1]/abbr")
                #date = date_elements.text.strip()
                date_elements = driver.find_elements(By.XPATH, "/html/body/div[1]/main/div/div/div[2]/div[4]/div[1]/div/div[2]/div/div[1]/dl/dd/abbr")
                date_list = [elem.text.strip() for elem in date_elements if elem.text.strip()]
                date = " - ".join(date_list)
                print(f"Event {i+1} - Datum: {date}")
            except Exception as e:
                date = "Kein Datum gefunden"
                print(f"Event {i+1} - Fehler beim Extrahieren des Datums: {e}")
            
            # Location extrahieren
            try:
                location_element = driver.find_element(By.XPATH, "/html/body/div[1]/main/div/div/div[2]/div[4]/div[2]/div/div/div/address/span")
                location = location_element.text.strip()
                print(f"Event {i+1} - Location: {location}")
            except Exception as e:
                location = ""
                #location = "Kein Location gefunden"
                print(f"Event {i+1} - Fehler beim Extrahieren der Location: {e}")

            # Description Extrahieren
            try:
                description_element = driver.find_element(By.CLASS_NAME, "entry-content")
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
                "Organisation": "Munich Startup",
                "Titel": title,
                "Datum": date,
                "Location": location,
                "Description": description,
                "Link": link,
            })


    #Rückgabe von den gesammelten Events an das main Programm
    driver.quit()
    return events