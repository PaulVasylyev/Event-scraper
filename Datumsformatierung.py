import re
from datetime import datetime, timezone
from dateutil import parser
from dateutil.tz import gettz

DEBUG = True

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
    """Entfernt überflüssige Punkte am Ende von Mustern wie '25.6.' oder '26. mar.'"""
    date_str = date_str.strip()
    # Für rein numerische Angaben z. B. "25.6." oder "25.6"
    if re.fullmatch(r'\d{1,2}\.\d{1,2}\.?', date_str):
        date_str = date_str.rstrip('.')
    # Für Tag + Monatsname, z. B. "26. mar." oder "26. mar"
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
    Zunächst wird eine eventuelle Jahresangabe am Ende entfernt (z. B. "25.6. 2025" -> "25.6").
    Unterstützt werden rein numerische Muster ("25.6") sowie solche mit Monatsnamen ("26. mar").
    """
    # Entferne ein eventuell angehängtes Jahr
    clean_str = re.sub(r'\s+\d{4}$', '', date_str).strip()
    debug_print("try_manual_date, cleaned:", date_str, "->", clean_str)
    # Rein numerisch: z. B. "25.6"
    m = re.fullmatch(r'(\d{1,2})\.(\d{1,2})', clean_str)
    if m:
        day, month = m.groups()
        try:
            dt = datetime(default_year, int(month), int(day))
            debug_print("Manual numeric conversion:", clean_str, "->", dt)
            return dt
        except Exception as e:
            debug_print("Manual numeric conversion failed:", clean_str, e)
    # Mit Monatsnamen: z. B. "26. mar"
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

def parse_single_date(date_str, default_year=None):
    """
    Parst einen einzelnen Datum-String.
    Zunächst werden deutsche Monatsnamen ersetzt und der String vorverarbeitet.
    Falls kein Jahr vorhanden ist, wird default_year angehängt.
    Scheitert der reguläre Parser, wird versucht, den String manuell zu interpretieren.
    """
    debug_print("parse_single_date input:", date_str)
    date_str = adjust_german_months(date_str)
    date_str = preprocess_date_str(date_str)
    if default_year and not re.search(r'\b\d{4}\b', date_str):
        date_str += f" {default_year}"
        debug_print("Year appended:", date_str)
    try:
        dt = parser.parse(date_str, dayfirst=True, tzinfos=tzinfos, fuzzy=True)
        debug_print("parse_single_date success:", date_str, "->", dt)
        return dt
    except Exception as e:
        debug_print("parse_single_date failed:", date_str, "Error:", e)
        dt_manual = try_manual_date(date_str, default_year or datetime.now().year)
        if dt_manual:
            return dt_manual
    return None

def parse_date_range(date_str, org=None):
    """
    Parst einen Bereichs-Datum-String und gibt ihn als "start_iso - end_iso" zurück.
    
    Unterstützte Beispiele:
      • "April 28, 2025 9:00 AM - May 23, 2025 5:00 PM"
      • "23.–26.6." oder "25.6" (TUM)
      • "26. März – 28. März" (Social Startup hub)
      • "03 MAR 1:30 pm - 2:30 pm" bzw. "06 MAR 1:00 pm - 1:45 pm" (ForTe)
    """
    debug_print("parse_date_range input:", date_str)
    # Normalisieren: Ersetze En-Dash, "Uhr" etc.
    date_str = date_str.replace("–", "-").replace("Uhr", "").replace("·", " ")
    date_str = re.sub(r'\s+', ' ', date_str).strip()
    debug_print("Normalized range string:", date_str)
    
    # Sonderfall: Falls "@" vorhanden, separat behandeln
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
    
    # Zerlege an Bindestrichen (egal ob Leerzeichen vorhanden)
    parts = re.split(r'\s*-\s*', date_str)
    if len(parts) == 2:
        start_str, end_str = parts
        debug_print("Range parts:", start_str, "|", end_str)
        
        # Sonderfall TUM: Wenn der Startteil nur einen Tag enthält, den Monat aus dem Endteil übernehmen
        if re.fullmatch(r'\d{1,2}\.?', start_str):
            m = re.search(r'\d{1,2}\.(\d{1,2})\.?', end_str)
            if m:
                month = m.group(1)
                start_str = start_str.rstrip('.') + f".{month}"
                debug_print("Adjusted TUM start_str:", start_str)
        
        # Sonderfall ForTe: Falls der Endteil nur eine Uhrzeit enthält, Datum aus Start übernehmen
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

def parse_event_date(date_str, org=None):
    """
    Parst den Datum-String eines Events und gibt ihn im ISO8601-Format zurück.
    Wird ein Bindestrich (egal ob mit oder ohne Leerzeichen) oder ein "@" gefunden,
    wird der String als Bereich interpretiert.
    """
    debug_print("parse_event_date input:", date_str, "Org:", org)
    date_str = date_str.replace("Uhr", "").replace("·", " ").strip()
    if "-" in date_str or "–" in date_str or "@" in date_str:
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
    return date_str

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