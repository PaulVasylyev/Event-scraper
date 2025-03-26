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
    driver.get("https://events.fortefoundation.org/")
    time.sleep(5)

    # Bestimme die Anzahl der Events
    event_count = len(driver.find_elements(By.XPATH, "/html/body/div[1]/div/section[1]/div/div/div/div/div[5]/div")) - 2
    print(f"Gefundene Events: {event_count}")

    events = []

    event_links = []

    # Link extrahieren
    for i in range(event_count):
        try:
            xpath_link = f'/html/body/div[1]/div/section[1]/div/div/div/div/div[5]/div[{i+1}]/div[2]/a'
            link_address = driver.find_element(By.XPATH, xpath_link)
            links = link_address.get_attribute("href")
            print(f"Event {i+1} - Link: {links}")
        except Exception as e:
            links = "Kein Link gefunden"
            print(f"Event {i+1} - Fehler beim Extrahieren des Links: {e}")

        event_links.append(links)

    # Jetzt über jeden Link iterieren
    for i in range(event_count):
        driver.get(event_links[i])
        time.sleep(3)  # Warten, bis die Seite vollständig geladen ist

        # Titel extrahieren
        try:
            title_element = driver.find_element(By.XPATH, "/html/body/div[1]/div/div/div/article/div/div[1]/div/div[3]/div/p/a/span[2]/span[2]")
            title = title_element.text.strip()
            print(f"Event {i+1} - Titel: {title}")
        except Exception as e:
            title = "Kein Titel gefunden"
            print(f"Event {i+1} - Fehler beim Extrahieren des Titels: {e}")

        # Datum extrahieren
        try:
            # Start-Datum und Zeit extrahieren
            start_element = driver.find_element(By.CLASS_NAME, "evo_start")
            
            # Unsichtbare Inhalte mit JavaScript auslesen
            start_day = driver.execute_script("return arguments[0].querySelector('.date').textContent;", start_element).strip()
            start_month = driver.execute_script("return arguments[0].querySelector('.month').textContent;", start_element).strip().upper()
            start_time = driver.execute_script("return arguments[0].querySelector('.time').textContent;", start_element).strip()
            date_start = f"{start_day} {start_month} {start_time}"
            
            # Endzeit extrahieren (mit CSS-Selektor, da das Element zwei Klassen hat)
            try:
                extra_element = driver.find_element(By.CSS_SELECTOR, ".evo_end.only_time")
                extra_text = driver.execute_script("return arguments[0].textContent;", extra_element).strip()
                date_end = f"- {extra_text}"
            except Exception as e:
                date_end = ""
            
            # Gesamtdatum zusammenfügen
            date = f"{date_start} {date_end}".strip()
            print(f"Event {i+1} - Datum: {date}")
        except Exception as e:
            date = "Kein Datum gefunden"
            print(f"Event {i+1} - Fehler beim Extrahieren des Datums: {e}")

        # Location extrahieren
        try:
            location_elements = driver.find_elements(By.CLASS_NAME, "evo_location_name")
            location_list = [elem.text.strip() for elem in location_elements if elem.text.strip()]
            location = " ".join(location_list)
            print(f"Event {i+1} - Location: {location}")
        except Exception as e:
            location = ""
            #location = "Kein Location gefunden"
            print(f"Event {i+1} - Fehler beim Extrahieren der Location: {e}")

        # Description Extrahieren
        try:
            description_elements = driver.find_elements(By.CLASS_NAME, "eventon_desc_in")
            description_text = [
                elem.text.strip()
                for elem in description_elements
                if elem.text.strip() and elem.text.strip() not in ["REGISTER", "REGISTER [FOR FREE]"]
            ]
            
            # Falls du alles zu einem String zusammenfügen willst:
            description = " ".join(description_text)
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
            "Organisation": "ForTe",
            "Titel": title,
            "Datum": date,
            "Location": location,
            "Description": description,
            "Link": link,
        }) 

       

    #Rückgabe von den gesammelten Events an das main Programm
    driver.quit()
    return events