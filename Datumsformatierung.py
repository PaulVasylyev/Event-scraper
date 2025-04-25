import re
from datetime import datetime, timezone
from dateutil import parser
from dateutil.tz import gettz
import dateutil.parser
import pandas as pd
import os

DEBUG = True

from datetime import date
DEFAULT_YEAR = date.today().year

# Zeitzonen-Mapping (CEST/CET korrekt interpretieren)
tzinfos = {"CEST": gettz("Europe/Berlin"), "CET": gettz("Europe/Berlin")}

# Mapping deutscher Monatsnamen zu englischen Abkürzungen
german_to_english = {
    "januar": "jan",
    "februar": "feb",
    "märz": "mar",
    "maerz": "mar",
    "april": "apr",
    "mai": "may",
    "juni": "jun",
    "juli": "jul",
    "august": "aug",
    "september": "sep",
    "oktober": "oct",
    "november": "nov",
    "dezember": "dec"
}

def debug_print(*args):
    if DEBUG:
        print("[DEBUG]", *args)

def adjust_german_months(date_str):
    """Ersetzt deutsche Monatsnamen durch englische Abkürzungen (unabhängig von Groß-/Kleinschreibung)."""
    original = date_str
    for ger, eng in german_to_english.items():
        date_str = re.sub(ger, eng, date_str, flags=re.IGNORECASE)
    debug_print("adjust_german_months:", original, "->", date_str)
    return date_str

def preprocess_date_str(date_str):
    """Clean extra dots at the end of simple patterns like '25.6.' or '26. Apr.'."""
    date_str = date_str.strip()
    if re.fullmatch(r'\d{1,2}\.\d{1,2}\.?', date_str):
        date_str = date_str.rstrip('.')
    if re.fullmatch(r'\d{1,2}\.\s*[A-Za-z]+\.?', date_str):
        date_str = re.sub(r'\.\s*$', '', date_str)
    return date_str

def format_datetime(dt):
    """
    Gibt ein datetime-Objekt im ISO8601-Format zurück.
    Wenn die Uhrzeit 00:00:00 ist, wird "YYYY-MM-DD" ausgegeben,
    ansonsten "YYYY-MM-DDTHH:MM:SS.000Z" (UTC).
    """
    if dt.hour == 0 and dt.minute == 0 and dt.second == 0:
        formatted = dt.strftime("%Y-%m-%d")
    else:
        if dt.tzinfo:
            dt_utc = dt.astimezone(timezone.utc)
        else:
            dt_utc = dt.replace(tzinfo=timezone.utc)
        formatted = dt_utc.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    debug_print("format_datetime:", dt, "->", formatted)
    return formatted

def try_manual_date(date_str, default_year):
    """
    Versucht, einen Datum-String manuell zu interpretieren, falls er einem einfachen Muster entspricht.
    Zunächst wird eine eventuell angehängte Jahresangabe entfernt (z. B. "25.6. 2025" -> "25.6").
    Unterstützt werden rein numerische Muster ("25.6") sowie solche mit Monatsnamen ("26. mar").
    """
    clean_str = re.sub(r'\s+\d{4}$', '', date_str).strip()
    debug_print("try_manual_date, cleaned:", date_str, "->", clean_str)
    m = re.fullmatch(r'(\d{1,2})\.(\d{1,2})', clean_str)
    if m:
        day, month = m.groups()
        try:
            dt = datetime(default_year, int(month), int(day))
            debug_print("Manual numeric conversion:", clean_str, "->", dt)
            return dt
        except Exception as e:
            debug_print("Manual numeric conversion failed:", clean_str, e)
    m = re.fullmatch(r'(\d{1,2})\.\s*([A-Za-z]+)', clean_str)
    if m:
        day, month_str = m.groups()
        try:
            try:
                dt_month = datetime.strptime(month_str, "%b")
            except ValueError:
                dt_month = datetime.strptime(month_str, "%B")
            month = dt_month.month
            dt = datetime(default_year, month, int(day))
            debug_print("Manual text conversion:", clean_str, "->", dt)
            return dt
        except Exception as e:
            debug_print("Manual text conversion failed:", clean_str, e)
    return None

def parse_single_date(date_str, default_year=DEFAULT_YEAR):
    debug_print("parse_single_date input:", date_str)
    if "," in date_str:
        # Remove weekday if present
        date_str = date_str.split(",", 1)[1].strip()
        debug_print("Removed weekday:", date_str)
    date_str = adjust_german_months(date_str)
    date_str = preprocess_date_str(date_str)
    if not re.search(r'\b\d{4}\b', date_str):
        date_str += f" {default_year}"
        debug_print("Year appended:", date_str)
    # Use day-first mode for German-style dates (e.g. "4. April")
    if re.search(r'\b\d{1,2}\.\s*[A-Za-z]+', date_str, re.IGNORECASE):
        use_dayfirst = True
    else:
        use_dayfirst = False
    try:
        dt = dateutil.parser.parse(date_str, dayfirst=use_dayfirst, tzinfos=tzinfos, fuzzy=True)
        debug_print("parse_single_date success:", date_str, "->", dt)
        return dt
    except Exception as e:
        debug_print("parse_single_date failed:", date_str, "Error:", e)
    return None

def debug_print(*args):
    # Debug-Ausgaben – kannst du nach Bedarf aktivieren oder entfernen
    print(*args)

def format_datetime(dt):
    return dt.isoformat(timespec='minutes')

def ensure_year(date_str, default_year):
    # If no 4-digit year is present, append the default year.
    if not re.search(r'\b\d{4}\b', date_str):
        date_str = date_str + f" {default_year}"
    return date_str

def try_special_format(date_str, default_year):
    """
    Special-case parser for strings like:
      "Starts on Wednesday, May 14 · 6:30pm CEST"
      "Monday, March 31 · 1 - 2:30pm CEST"
    First, remove any leading phrases like "Starts on ".
    Then, if a centered dot (·) is present, split the string.
    If the time part contains a hyphen, treat it as a range;
    otherwise, treat it as a single event time.
    """
    # Remove a leading "Starts on " if present
    date_str = re.sub(r'^(Starts on\s+)', '', date_str, flags=re.IGNORECASE)
    
    parts = date_str.split("·")
    if len(parts) < 2:
        return None

    # First part: date information
    date_part = parts[0].strip()
    if "," in date_part:
        date_part = date_part.split(",", 1)[1].strip()
    date_part = ensure_year(date_part, default_year)
    date_part = adjust_german_months(date_part)

    # Second part: time information
    time_part = parts[1].strip()
    # Check if it is a range (contains a hyphen) or a single time event
    if "-" in time_part:
        start_time_str, end_time_str = time_part.split("-", 1)
        start_time_str = start_time_str.strip()
        end_time_str = end_time_str.strip()
        # Remove timezone markers from end_time_str
        end_time_str = re.sub(r'\b(?:CEST|CET)\b', '', end_time_str).strip()
        # If the start time does not have an am/pm marker but the end time does, append it
        if not re.search(r'(am|pm)', start_time_str, re.IGNORECASE) and re.search(r'(am|pm)', end_time_str, re.IGNORECASE):
            meridiem = re.search(r'(am|pm)', end_time_str, re.IGNORECASE).group(1).lower()
            start_time_str = start_time_str + " " + meridiem
        try:
            start_dt = dateutil.parser.parse(f"{date_part} {start_time_str}", dayfirst=False, tzinfos=tzinfos)
            end_dt = dateutil.parser.parse(f"{date_part} {end_time_str}", dayfirst=False, tzinfos=tzinfos)
            return f"{start_dt.isoformat(timespec='minutes')} - {end_dt.isoformat(timespec='minutes')}"
        except Exception as e:
            debug_print("Error in try_special_format (range):", e)
            return None
    else:
        # Single time event (no hyphen found)
        time_str = re.sub(r'\b(?:CEST|CET)\b', '', time_part).strip()
        try:
            dt = dateutil.parser.parse(f"{date_part} {time_str}", dayfirst=False, tzinfos=tzinfos)
            return dt.isoformat(timespec='minutes')
        except Exception as e:
            debug_print("Error in try_special_format (single time):", e)
            return None

def parse_date_range(date_str, org=None):
    pattern = r'^[A-Za-z]+, [A-Za-z]+ \d{1,2}\s+\d{1,2} - \d{1,2}:\d{2}(am|pm) [A-Z]+$' 
    m = re.match(pattern, date_str)
    if m:
        """
        Parses a date range string and returns it as "start_iso - end_iso".
        Supported formats include, for example:
        • "Monday, March 31 · 1 - 2:30pm CEST"
        • "Starts on Wednesday, May 14 · 6:30pm CEST"
        • "Freitag, 4. April 18:30 - 21:00"
        """
        debug_print("parse_date_range input:", date_str)
        # Try the special case first
        special = try_special_format(date_str, DEFAULT_YEAR)
        if special:
            return special

        # General branch: remove weekday if present
        if "," in date_str:
            date_str = date_str.split(",", 1)[1].strip()
            debug_print("Removed weekday from range:", date_str)
        # Remove time zone markers and extra words
        date_str = re.sub(r'\b(?:CEST|CET)\b', '', date_str)
        date_str = date_str.replace("·", " ").replace("Uhr", "")
        date_str = re.sub(r'\s+', ' ', date_str).strip()
        debug_print("Normalized range string:", date_str)

        parts = re.split(r'\s*-\s*', date_str)
        if len(parts) == 2:
            start_str, end_str = parts
            debug_print("Range parts:", start_str, "|", end_str)
            # If the end time has an am/pm marker but the start time does not, add it.
            if re.search(r'(am|pm)', end_str, re.IGNORECASE) and not re.search(r'(am|pm)', start_str, re.IGNORECASE):
                mer = re.search(r'(am|pm)', end_str, re.IGNORECASE).group(1).lower()
                start_str = start_str + " " + mer
                debug_print("Appended meridiem to start_str:", start_str)
            # If the end part lacks a month, inherit date from the start.
            if not re.search(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b', end_str, re.IGNORECASE):
                dt_start = parse_single_date(start_str, default_year=DEFAULT_YEAR)
                if dt_start:
                    date_part_inherited = dt_start.strftime("%d %b")
                    end_str = f"{date_part_inherited} {end_str}"
                    debug_print("Inherited date for end:", end_str)
            dt_start = parse_single_date(start_str, default_year=DEFAULT_YEAR)
            dt_end = parse_single_date(end_str, default_year=DEFAULT_YEAR)
            if dt_start and dt_end:
                result = f"{format_datetime(dt_start)} - {format_datetime(dt_end)}"
                debug_print("Parsed general range:", result)
                return result

        dt = parse_single_date(date_str, default_year=DEFAULT_YEAR)
        if dt:
            result = format_datetime(dt)
            debug_print("Parsed single date:", result)
            return result
        debug_print("Failed to parse date:", date_str)
        return date_str
    else:
        pass
    
    """
    Parst einen Bereichs-Datum-String und gibt ihn als "start_iso - end_iso" zurück.
    Unterstützte Beispiele:
      • "April 28, 2025 9:00 AM - May 23, 2025 5:00 PM"
      • "23.–26.6." oder "25.6" (TUM)
      • "26. März – 28. März" (Social Startup hub)
      • "03 MAR 1:30 pm - 2:30 pm" bzw. "06 MAR 1:00 pm - 1:45 pm" (ForTe)
    """
    debug_print("parse_date_range input:", date_str)
    date_str = date_str.replace("–", "-").replace("Uhr", "").replace("·", " ")
    date_str = re.sub(r'\s+', ' ', date_str).strip()
    debug_print("Normalized range string:", date_str)


    
    if "@" in date_str:
        date_part, time_part = date_str.split("@", 1)
        date_part = date_part.strip()
        times = re.split(r'\s*-\s*', time_part)
        if len(times) == 2:
            start_time_str = times[0].strip()
            end_time_str = times[1].strip()
            default_year = datetime.now().year
            start_dt = parse_single_date(f"{date_part} {start_time_str}", default_year=default_year)
            end_dt = parse_single_date(f"{date_part} {end_time_str}", default_year=default_year)
            if start_dt and end_dt:
                result = f"{format_datetime(start_dt)} - {format_datetime(end_dt)}"
                debug_print("Parsed range with '@':", result)
                return result
    
    parts = re.split(r'\s*-\s*', date_str)
    if len(parts) == 2:
        start_str, end_str = parts
        debug_print("Range parts:", start_str, "|", end_str)
        # Falls im Endteil bereits am/pm vorkommt, aber nicht im Startteil, "pm" ergänzen.
        if re.search(r'\b(am|pm)\b', end_str, re.IGNORECASE) and not re.search(r'\b(am|pm)\b', start_str, re.IGNORECASE):
            start_str = start_str + " pm"
            debug_print("Appended 'pm' to start_str:", start_str)
        # Sonderfall TUM: Wenn der Startteil nur einen Tag enthält, Monat aus Endteil übernehmen.
        if re.fullmatch(r'\d{1,2}\.?', start_str):
            m = re.search(r'\d{1,2}\.(\d{1,2})\.?', end_str)
            if m:
                month = m.group(1)
                start_str = start_str.rstrip('.') + f".{month}"
                debug_print("Adjusted TUM start_str:", start_str)
        
        # Sonderfall ForTe: Falls der Endteil nur eine Uhrzeit enthält, Datum aus Start übernehmen.
        if re.fullmatch(r'\d{1,2}(:\d{2})?\s*(am|pm)?', end_str, flags=re.IGNORECASE):
            dt_start = parse_single_date(start_str, default_year=datetime.now().year)
            if dt_start:
                date_part = dt_start.strftime("%d %b")
                end_full_str = f"{date_part} {end_str}"
                debug_print("ForTe range: combining date part:", end_full_str)
                dt_end = parse_single_date(end_full_str, default_year=dt_start.year)
                if dt_end:
                    result = f"{format_datetime(dt_start)} - {format_datetime(dt_end)}"
                    debug_print("Parsed ForTe range:", result)
                    return result
        
        default_year = datetime.now().year
        start_dt = parse_single_date(start_str, default_year=default_year)
        end_dt = parse_single_date(end_str, default_year=default_year)
        if start_dt and end_dt:
            result = f"{format_datetime(start_dt)} - {format_datetime(end_dt)}"
            debug_print("Parsed general range:", result)
            return result

    dt = parse_single_date(date_str, default_year=datetime.now().year)
    if dt:
        result = format_datetime(dt)
        debug_print("Parsed single date:", result)
        return result
    debug_print("Failed to parse date:", date_str)
    return date_str

def try_fallback_date_parse(date_str):
    """
    Fallback-Parser für Sonderfälle, die der Haupt-Parser nicht erkennt.
    Jetzt unterstützt er
      • reine Zahlbereiche   (z. B. 23.–26.6.)
      • einzelne numerische  (z. B. 25.6.)
      • Bereiche MIT Monatsnamen (z. B. 26. März – 28. März)
      • einzelne Datumsangaben mit Monatsnamen (z. B. 26. März)
    Liefert ISO-Strings oder – falls unerkannt – den Original-String.
    """
    debug_print("Fallback parser triggered for:", date_str)

    # 1) Sonderzeichen vereinheitlichen
    cleaned = (date_str
               .replace("�", "-")        # ersetztes Ersatz-Symbol
               .replace("–", "-")
               .replace("—", "-")
               .strip())
    cleaned = cleaned.rstrip(".")        # Endpunkt entfernen

    # 2) Deutsche Monatsnamen in englische Kürzel wandeln
    cleaned = adjust_german_months(cleaned)   # z.B. "März" → "mar"

    # 3) ***Bereich mit MONATSNAMEN***   26. mar - 28. mar
    m_range_month = re.fullmatch(
        r"(\d{1,2})\.?\s*([A-Za-z]{3,})\s*-\s*(\d{1,2})\.?\s*([A-Za-z]{3,})",
        cleaned, flags=re.IGNORECASE
    )
    if m_range_month:
        day_start, mon_start_str, day_end, mon_end_str = m_range_month.groups()
        try:
            mon_start = datetime.strptime(mon_start_str[:3], "%b").month
            mon_end   = datetime.strptime(mon_end_str[:3],  "%b").month
            year = datetime.now().year
            dt_start = datetime(year, mon_start, int(day_start))
            dt_end   = datetime(year, mon_end,  int(day_end))
            result = f"{format_datetime(dt_start)} - {format_datetime(dt_end)}"
            debug_print("Fallback parsed month-range:", result)
            return result
        except Exception as e:
            debug_print("Fallback month-range failed:", e)

    # 4) ***Bereich rein numerisch***   23-26.6  oder 23.-26.6
    m_range_num = re.fullmatch(r"(\d{1,2})\.?-?(\d{1,2})\.(\d{1,2})", cleaned)
    if m_range_num:
        day_start, day_end, month = map(int, m_range_num.groups())
        year = datetime.now().year
        try:
            dt_start = datetime(year, month, day_start)
            dt_end   = datetime(year, month, day_end)
            result = f"{format_datetime(dt_start)} - {format_datetime(dt_end)}"
            debug_print("Fallback parsed numeric range:", result)
            return result
        except Exception as e:
            debug_print("Fallback numeric range failed:", e)

    # 5) ***Einzeldatum mit MONATSNAMEN***   26. mar
    m_single_month = re.fullmatch(r"(\d{1,2})\.?\s*([A-Za-z]{3,})", cleaned, flags=re.IGNORECASE)
    if m_single_month:
        day, mon_str = m_single_month.groups()
        try:
            month = datetime.strptime(mon_str[:3], "%b").month
            dt = datetime(datetime.now().year, month, int(day))
            result = format_datetime(dt)
            debug_print("Fallback parsed single month-date:", result)
            return result
        except Exception as e:
            debug_print("Fallback single month-date failed:", e)

    # 6) ***Einzeldatum rein numerisch***   25.6
    m_single_num = re.fullmatch(r"(\d{1,2})\.(\d{1,2})", cleaned)
    if m_single_num:
        day, month = map(int, m_single_num.groups())
        try:
            dt = datetime(datetime.now().year, month, day)
            result = format_datetime(dt)
            debug_print("Fallback parsed single numeric date:", result)
            return result
        except Exception as e:
            debug_print("Fallback single numeric date failed:", e)

    # 7) Unbekanntes Format → Original zurückgeben
    return date_str


def parse_event_date(date_str, org=None):
    """
    Parst den Datum-String eines Events und gibt ihn im ISO8601-Format zurück.
    Wird ein Bindestrich (egal ob mit oder ohne Leerzeichen) oder ein "@" gefunden,
    wird der String als Bereich interpretiert.
    """
    debug_print("parse_event_date input:", date_str, "Org:", org)
    date_str = date_str.replace("Uhr", "").replace("·", " ").strip()
    if "-" in date_str or "-" in date_str or "@" in date_str:
        result = parse_date_range(date_str, org)
        debug_print("parse_event_date range result:", result)
        return result
    else:
        dt = parse_single_date(date_str, default_year=datetime.now().year)
        if dt:
            result = format_datetime(dt)
            debug_print("parse_event_date single result:", result)
            return result
    debug_print("parse_event_date failed, returning original:", date_str)
    # Fallback verwenden, wenn normales Parsen gescheitert ist
    fallback_result = try_fallback_date_parse(date_str)
    debug_print("parse_event_date fallback result:", fallback_result)
    return fallback_result

def process_events(events):
    """
    Nimmt eine Liste von Events entgegen, parst und formatiert deren "Datum"-Feld
    und gibt die bearbeitete Liste zurück.
    """
    debug_print("process_events: Starting processing", len(events), "events")
    for event in events:
        if "Datum" in event and event["Datum"]:
            org = event.get("Organisation")
            original_date = event["Datum"]
            event["Datum"] = parse_event_date(event["Datum"], org)
            debug_print("Processed event date:", original_date, "->", event["Datum"])
    return events

if __name__ == '__main__':
    df = pd.read_excel("scraped_events.xlsx")
    events = df.to_dict(orient="records")
    events = process_events(events)
    new_df = pd.DataFrame(events)
    new_df.to_excel("scraped_events_formatted.xlsx", index=False)
    print("Die Datei 'scraped_events_formatted.xlsx' wurde erstellt.")
    # --- In CSV speichern ---
    new_df.to_csv("scraped_events_formatted.csv", index=False, encoding="utf-8")
    print("Die Datei 'scraped_events_formatted.csv' wurde erstellt.")

# Optional: Dateien löschen
files_to_delete = ["scraped_events.csv", "scraped_events.xlsx"]

for file in files_to_delete:
    try:
        os.remove(file)
        print(f"🗑️ Datei gelöscht: {file}")
    except FileNotFoundError:
        print(f"⚠️ Datei nicht gefunden: {file}")
    except Exception as e:
        print(f"❌ Fehler beim Löschen von {file}: {e}")