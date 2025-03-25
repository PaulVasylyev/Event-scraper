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
    driver.get("https://www.social-startup-hub.de/events/")
    time.sleep(2)

    # Cookie-Banner ggf. schließen
    try:
        cookie_button = driver.find_element(By.XPATH, "//*[@id='CookieBoxSaveButton']")
        cookie_button.click()
        time.sleep(1)
    except NoSuchElementException:
        pass

    # Bestimme die Anzahl der Events
    event_count = len(driver.find_elements(By.XPATH, "//*[@id='jet-tabs-content-1411']/div/div/div[2]/div"))
    print(f"Gefundene Events: {event_count}")

    events = []

    for i in range(event_count):

        # Titel extrahieren
        try:
            xpath_title = f'//*[@id="jet-tabs-content-1411"]/div/div/div[2]/div[{i+1}]/div[2]/article/div/header/h3/a'
            title_element = driver.find_element(By.XPATH, xpath_title)
            title = title_element.text.strip()
            print(f"Event {i+1} - Titel: {title}")
        except Exception as e:
            title = "Kein Titel gefunden"
            print(f"Event {i+1} - Fehler beim Extrahieren des Titels: {e}")

        # Datum extrahieren
        try:
            xpath_date = f'//*[@id="jet-tabs-content-1411"]/div/div/div[2]/div[{i+1}]/div[2]/article/div/header/div/time'
            date_element = driver.find_element(By.XPATH, xpath_date)
            date = date_element.text.strip()
            print(f"Event {i+1} - Datum: {date}")
        except Exception as e:
            date = "Kein Datum gefunden"
            print(f"Event {i+1} - Fehler beim Extrahieren des Datums: {e}")

        # Location
        try:
            xpath_location = f'//*[@id="jet-tabs-content-1411"]/div/div/div[2]/div[{i+1}]/div[2]/article/div/header/address/span[1]'
            location_element = driver.find_element(By.XPATH, xpath_location)
            location = location_element.text.strip()
            print(f"Event {i+1} - Location: {location}")
        except Exception as e:
            location = "Kein Location gefunden"
            print(f"Event {i+1} - Fehler beim Extrahieren der Location: {e}")
        
        # Description Extrahieren
        try:
            xpath_description = f'/html/body/div[1]/section[1]/div/div/div/section/div/div/div/div[2]/div/div/div[2]/div[1]/div/div/div[2]/div[{i+1}]/div[2]/article/div/div/p[1]/text()'
            script = f'''
            var xpath = "{xpath_description}";
            var result = document.evaluate(xpath, document, null, XPathResult.STRING_TYPE, null);
            return result.stringValue;
            '''
            description = driver.execute_script(script).strip()
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
            xpath_link = f'//*[@id="jet-tabs-content-1411"]/div/div/div[2]/div[{i+1}]/div[2]/article/div/header/h3/a'
            link_address = driver.find_element(By.XPATH, xpath_link)
            link = link_address.get_attribute("href")
            print(f"Event {i+1} - Link: {link}")
        except Exception as e:
            link = "Kein Link gefunden"
            print(f"Event {i+1} - Fehler beim Extrahieren des Links: {e}")


        # Speichern in Events
        events.append({
            "Organisation": "Social Startup hub",
            "Titel": title,
            "Datum": date,
            "Location": location,
            "Description": description,
            "Link": link,
        })

    #Rückgabe von den gesammelten Events an das main Programm
    driver.quit()
    return events