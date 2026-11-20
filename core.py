"""File: core.py
CSC-44102-2026-Coursework
Author: X9J77
"""

import calendar
import sqlite3
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from enum import Enum
import json


DB_FILENAME = "plants.db"
DATE_FORMAT = "%d/%m/%Y"  # Day-Month-Year


MAX_NAME = 20               #Sets the max and minum length of the name, type, location and interval days
MAX_TYPE = 12
MAX_LOCATION = 20
MIN_INTERVAL_DAYS = 1
MAX_INTERVAL_DAYS = 365
MAX_AGE_YEARS = 999


FIELD_LABLES = {
    "name": "Name",
    "plant_type": "Type",
    "location": "Location",}


class WaterState(Enum):
    """The differnt watering states a plant can be in on a given day."""
    
    PENDING = "pending"         # No watering recorded yet
    OVERDUE = "overdue"         #The due date us before the current day
    TODAY = "today"             #Watering due date is today
    UPCOMING = "upcoming"       #Plant is due to be watered 

STATE_COLOUR = {
    WaterState.OVERDUE: "red",
    WaterState.TODAY: "amber",
    WaterState.PENDING: "blue",
    WaterState.UPCOMING: None,
}
@dataclass
class Plant:
    
    id: int | None                                       #Value set to None until the database assigns an ID to the plant
    name: str                                            #The name of the plant
    plant_type: str                                      #The type of the plant
    location: str                                        #The location of the plant
    interval_days: int                                   #The watering interval in days
    acquired: date                                       #The date the plant was acquired
    waterings: list[date] = field(default_factory=list)  #List of dates the plant was watered, defaulting to an empty list

class ValidationError(Exception):
    """ Raised when a value failes its rule
    
    'field' names the field that failed validation.
    'message' describes the problem.
    """
    
    def __init__(self, errors: list[str]):
        super().__init__(f"{len(errors)} problem(s) found")
        self.errors = errors
        
class PlantNotFound(Exception):
    """An ID was given that no plant has. Raised by get_plant_by_id()"""
    
class ImportFailed(Exception):
    """
    An import file had problems. 
    'errors' holds one line for each problem found
    """
    
    def __init__(self, errors: list[str]):
        super().__init__(f"{len(errors)} problem(s) found")
        self.errors = errors
        
        
#************************************************************
#   Validation Functions
#
# Each function takes the user input and returns the validated
# value or raises a ValidationError, with a message of what 
# went wrong.
#*************************************************************


def clean_text(raw: str, field_name: str, max_len: int) -> str:
    """Clean and validate a text field"""
    text = raw.strip()
    label = FIELD_LABLES[field_name]
    if not text:
        raise ValidationError(field_name, f"{label} cannot be empty.")
    if len(text) > max_len:
        raise ValidationError( field_name, f"{label} must be {max_len} characters or fewer (that was {len(text)}).",)
    return text
    
def parse_name(raw: str) -> str:
    """"Check a plant's name is valid"""
    return clean_text(raw, "name", MAX_NAME)


def parse_type(raw: str) -> str:
    """Check a plant's type is valid"""
    return clean_text(raw, "plant_type", MAX_TYPE)


def parse_location(raw: str) -> str:
    """Check a plant's location is valid"""
    return clean_text(raw, "location", MAX_LOCATION)


def parse_whole_number(raw: str, field_name: str, min_value: int, max_value: int, message: str) -> int:
    """Turn a string into a whole number and check it is within the given range"""
    try:
        number = int(raw.strip())
    except ValueError:
        raise ValidationError(field_name, message) from None
    if not min_value <= number <= max_value:
        raise ValidationError(field_name, message)
    return number

def parse_interval_days(raw: str) -> int:
    """Check a watering interval: a whole number of days between 1 and 365"""
    return parse_whole_number(
        raw, "interval_days", MIN_INTERVAL_DAYS, MAX_INTERVAL_DAYS,
        f"Watering interval must be a whole number of days between {MIN_INTERVAL_DAYS} and {MAX_INTERVAL_DAYS}."
    )
    
    
def parse_age_years(raw: str) -> int:
    """Check a plant's age: a whole number of years between 0 and 999"""
    return parse_whole_number(
        raw, "age_years", 0, MAX_AGE_YEARS,
        f"Age must be a whole number of years between 0 and {MAX_AGE_YEARS}."
    )
    

def parse_age_months(raw: str) -> int:
    """Check the months part of a plant's age: a whole number of months between 0 and 11"""
    return parse_whole_number(
        raw, "age_months", 0, 11,
        "Months must be a whole number between 0 and 11."
    )

def parse_plant_id(raw: str) -> int:
    """Read a plant ID typed with or without leading 0's, and check it is a positive whole number"""
    return parse_whole_number(
        raw, "plant_id", 1, 9999,
        f"Plant ID must be a positive whole number between 1 and 9999."
    )
    
def parse_date(raw: str, field_name: str= "date") -> date:
    """Read a date typed as DD/MM/YYYY and check it is a valid date"""
    try:
        #strptime() will raise a ValueError if the string is not a valid date
        return datetime.strptime(raw.strip(), DATE_FORMAT).date()
    except ValueError:
        raise ValidationError(field_name, f"Date must be in the format DD/MM/YYYY and be a valid date.") from None
    
def parse_watering_date(raw: str, today: date) -> date:
    """Read a watering date typed as DD/MM/YYYY and check it is a valid date, not in the future"""
    when = parse_date(raw, "watering_date")
    if when > today:
        raise ValidationError("watering_date", "Watering date cannot be in the future.")
    return when


#****************************************************
# Dates & Age Functions
#****************************************************


def plural (count: int, word: str) -> str:
    """Join a count and a word, adding an 's' if the count is not 1"""
    return f"{count} {word}" + ("s" if count != 1 else "")

def acquired_from_age(years: int, months: int, today: date) -> date:
    """Work out the date a plant was acquired from its age in years and months
    
    Checks the whole number of months, if that month is shorter than the current day,
    it uses the last day of that month.
    """
    months_since_year_zero = today.year * 12  + (today.month - 1) - (years * 12 + months)
    year, month_index = divmod(months_since_year_zero, 12)
    month = month_index + 1
    last_day_of_month = calendar.monthrange(year, month)[1]
    return date(year, month, min(today.day, last_day_of_month))

def age_of (acquired: date, today: date) -> tuple[int, int]:
    """Retrun a plants age as completed (years, months)"""
    months = (today.year - acquired.year) * 12 + (today.month - acquired.month)
    if today.day < acquired.day:
        months -= 1                                             #Month not completed yet
    return divmod(max(months, 0), 12)

def format_age(years: int, months: int) -> str:
    """Shows an age in one uniyt, either years or months, with pluralisation"""
    if years >= 1:
        return plural(years, "year")
    if months >= 1:
        return plural(months, "month")
    return "< 1 month"

def format_date(d: date) -> str:
    """Format a date as DD-MM-YYYY"""
    return f"{d.day:02d}/{d.month:02d}/{d.year:04d}"

def plant_to_fields(plant: Plant, today: date) -> dict:
    """Return a plant's editable values: the shape the edit screen works on."""
    years, months = age_of(plant.acquired, today)
    return {
        "name": plant.name,
        "plant_type": plant.plant_type,
        "location": plant.location,
        "interval_days": plant.interval_days,
        "age_years": years,
        "age_months": months,
    }

def make_plant(clean: dict, today: date, original: Plant) -> Plant:
    """Build the edited Plant from checked values.

    The stored acquired date is kept unless the age was actually changed. An
    age is only precise to the month, so recalculating the date on every save
    would slowly shift it. The ID and the watering history carry over.
    """
    age = (clean["age_years"], clean["age_months"])
    if age == age_of(original.acquired, today):
        acquired = original.acquired
    else:
        acquired = acquired_from_age(age[0], age[1], today)
    return Plant(
        id=original.id,
        name=clean["name"],
        plant_type=clean["plant_type"],
        location=clean["location"],
        interval_days=clean["interval_days"],
        acquired=acquired,
        waterings=list(original.waterings),
    )

#************************************************************
# Calculations for watering
#************************************************************


def last_watered(plant: Plant) -> date | None:
    """Return the last date the plant was watered, or None if it has never been watered"""
    return max(plant.waterings) if plant.waterings else None

def next_due(plant: Plant) -> date | None:
    """Return the next date the plant is due to be watered, or None if it has never been watered"""
    last = last_watered(plant)
    if last is None:
        return None
    return last + timedelta(days=plant.interval_days) 

def days_until_due(plant: Plant, today: date) -> int | None:
    """Days until the plant is due to be watered, or None if it has never been watered"""
    due = next_due(plant)
    if due is None:
        return None
    return (due - today).days


def days_since_watered(plant: Plant, today: date) -> int | None:
    """The days since the last watering, or none if never watered"""
    last = last_watered(plant)
    if last is None:
        return None
    return (today - last).days

def days_overdue(plant: Plant, today: date) -> int:
    """How many days late the watering is, will display 0 if it is not late"""
    days = days_until_due(plant, today)
    if days is None or days >= 0:
        return 0 
    return -days

def water_state(plant: Plant, today: date) -> WaterState:
    """ Decides which of the four states a plant is in today """
    
    days = days_until_due(plant, today)
    if days is None:
        return WaterState.PENDING
    if days < 0:
        return WaterState.OVERDUE
    if days == 0:
        return WaterState.TODAY
    return WaterState.UPCOMING

#********************************************************
# Display
#********************************************************


def format_id(plant_id: int) -> str:
    """Format a plant ID as a 4 digit number with leading 0's"""
    return f"{plant_id:04d}"

def format_next_water(plant: Plant, today: date) -> str:
    """The next water column: "in X days" or "Overdue by X days" or "Pending" """
    days = days_until_due(plant, today)
    if days is None:
        return "Pending"
    if days == 0:
        return "Today"
    if days > 0:
        return f"in {plural(days, 'day')}"
    return f"Overdue by {plural(-days, 'day')}"

def status_line(plants: list[Plant], today: date) -> str:
    """ Quick view status line that displays below CLI table"""
    counts = {state: 0 for state in WaterState}
    for plant in plants:
        counts[water_state(plant, today)] += 1
    return ( 
        f"{plural(len(plants), 'plant')} | {counts[WaterState.OVERDUE]} overdue"
        f" | {counts[WaterState.TODAY]} due today | {counts[WaterState.PENDING]} pending"
    )

def details_rows(plant: Plant, today: date) -> list[tuple[str, str]]:
    """Lines of the details page, as (lable, value) pairs"""
    years, months = age_of(plant.acquired, today)
    last = last_watered(plant)
    if last is None:
        last_text = "Never"
        due_text = "Pending"
    else:
        since = days_since_watered(plant, today)
        ago = "today" if since == 0 else f"{plural(since, 'day')} ago"
        last_text = f"{format_date(last)} ({ago})"
        due_text = f"{format_date(next_due(plant))} ({format_next_water(plant, today)})"
    return [
        ("Type", plant.plant_type),
        ("Location", plant.location),
        ("Age", format_age(years, months)),
        ("Water every", plural(plant.interval_days, "day")),
        ("Last watered", last_text),
        ("Next water", due_text),
        ("Days overdue", str(days_overdue(plant, today))),
    ]

#************************************************************
#  Lists
#************************************************************ 

SORT_KEYS = {
    "id": lambda plant, today: plant.id,
    "name": lambda plant, today: plant.name.casefold(),
    "age": lambda plant, today: (today - plant.acquired).days,
    "type": lambda plant, today: plant.plant_type.casefold(),
    "location": lambda plant, today: plant.location.casefold(),
    "last": lambda plant, today: last_watered(plant),
    "next": lambda plant, today: next_due(plant),
}

def sort_plants(plants: list[Plant], column: str, today: date, descending: bool = False) -> list[Plant]:
    """ Returns the plants sorted by one column.
    
        plants with equal keys keep the order they came in.
        plants with no valure for the column come last in the sorted list
    """
    if column not in SORT_KEYS:
        raise ValidationError("sort", f"Sort by one of: {', '.join(SORT_KEYS)}.")
    key = SORT_KEYS[column]
    with_value = [plant for plant in plants if key(plant, today) is not None]
    without_value = [plant for plant in plants if key(plant, today) is None]
    ordered = sorted(with_value, key=lambda plant: key(plant, today), reverse=descending)
    return ordered + without_value

def search_plants(plants: list [Plant], term: str) -> list[Plant]:
    """ Linear search: the plants who's name or location contains 'term'
    
    Every plant is checked once. case is ignored
    """
    wanted = " ".join(term.split()).casefold()
    if not wanted:
        return list(plants)
    matches = []
    for plant in plants:
        if wanted in plant.name.casefold() or wanted in plant.location.casefold():
            matches.append(plant)
    return matches

def filter_by_location(plants: list[Plant], location: str) -> list[Plant]:
    """Fileters plants by location """
    wanted = " ".join(location.split()).casefold()
    return [plant for plant in plants if plant.location.casefold() == wanted]

def known_locations(plants: list[Plant]) -> list[str]:
    """Lists every location in use in alphabetical order"""
    spelling_by_key: dict[str, str] = {}
    for plant in plants:
        spelling_by_key.setdefault(plant.location.casefold(), plant.location)
    return [spelling_by_key[key] for key in sorted(spelling_by_key)]

@dataclass
class LocationSummary:
    """
    One row of location summery>
    """
    
    location: str
    plants: int
    due_today: int
    overdue: int
    
def location_summary(plants: list[Plant], today: date) -> list[LocationSummary]:
    """
    Counts the plants, the ones that are due today and the overdue ones in each location.
    
    One pass over the plants, while a dictionary holds one row per location, allowing
    finding of a loaction's row to be quick depending on the number of plants.
    Case is ignored for locations so Kitchen and kitchen are the same.
    """
    summaries: dict[str, LocationSummary] = {}
    for plant in plants:
        key = " ".join(plant.location.split()).casefold()
        if key not in summaries:
            summaries[key] = LocationSummary(plant.location, 0, 0, 0)
        summary = summaries[key]
        summary.plants += 1
        state = water_state(plant, today)
        if state is WaterState.TODAY:
            summary.due_today +=1
        elif state is WaterState.OVERDUE:
            summary.overdue += 1
    return [summaries[key] for key in sorted(summaries)]

def today_view(plants: list[Plant], today: date) -> list[Plant]:
    """Picks the plants and orders them by urgency
    
    1: Keep the overdue, due-today and never-watered plants
    2: overdue dirst (most overdue at the top), then due today,
    then never watered. Ties are broken by name"""
    
    needs_attention = []
    for plant in plants:
        if water_state(plant, today) is not WaterState.UPCOMING:
            needs_attention.append(plant)
            
    group_order = {WaterState.OVERDUE: 0, WaterState.TODAY: 1, WaterState.PENDING: 2}
    
    def rank(plant: Plant) -> tuple[int, int, str]:
        """Tuples compare item by item: group friat, then days overdue, then name """
        return (
            group_order[water_state(plant, today)],
            -days_overdue(plant, today),
            plant.name.casefold(),
        )
        
    return sorted(needs_attention, key=rank)

def visible_plants(
    plants: list[Plant],
    today: date,
    search: str = "",
    location: str = "",
    today_only: bool = False,
    sort_column: str = "id",
    descending: bool = False,
) -> list [Plant]:
    
    """ Applys what the table is currently showinf: search, then filter, then order.
        Today view has its own ranking, so that column is ignored
    """
    shown = search_plants(plants, search)
    if location:
        shown = filter_by_location(shown, location)
    if today_only:
        return today_view(shown, today)
    return sort_plants(shown, sort_column, today, descending)
    

#************************************************************
#   Database Functions
#************************************************************
   

def connect(path=None) -> sqlite3.Connection:
    """Connect to the database, creating the file and tables if they do not exist"""
    if path is None:
        path = Path(__file__).resolve().parent / DB_FILENAME
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    create_tables(conn)
    return conn

def create_tables(conn: sqlite3.Connection) -> None:
    """Create two tables if they are not there already"""    
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS plants (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT    NOT NULL,
            plant_type    TEXT    NOT NULL,
            location      TEXT    NOT NULL,
            interval_days INTEGER NOT NULL,
            acquired      DATE    NOT NULL
        )
        """
    )
    
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS care_log (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            plant_id  INTEGER NOT NULL REFERENCES plants(id) ON DELETE CASCADE,
            care_date TEXT    NOT NULL,
            UNIQUE (plant_id, care_date)
        )
        """
    )
    conn.commit()

def _row_to_plant(row: sqlite3.Row, waterings: list[date]) -> Plant:
    """Turn a database row into a Plant object"""
    return Plant(
        row["id"],
        row["name"],
        row["plant_type"],
        row["location"],
        row["interval_days"],
        date.fromisoformat(row["acquired"]), waterings,
    )
    
def _require_plant(conn: sqlite3.Connection, plant_id: int) -> None:
    """Raise PlantNotFound unless a plant with this ID exists."""
    found = conn.execute("SELECT 1 FROM plants WHERE id = ?", (plant_id,)).fetchone()
    if found is None:
        raise PlantNotFound(f"No plant with ID {format_id(plant_id)}.")

def _insert_plant(conn: sqlite3.Connection, plant: Plant) -> int:
    """
    Inserts a plant and its waterins without committing, returns the new ID
    
    the caller commits, so several plants can be saved in one action
    """
    cursor = conn.execute(
        "INSERT INTO plants (name, plant_type, location, interval_days, acquired)"
        " VALUES (?, ?, ?, ?, ?)",
        (plant.name,
         plant.plant_type,
         plant.location,
         plant.interval_days,
         plant.acquired.isoformat())
    )
    plant_id = cursor.lastrowid
    for when in plant.waterings:
        conn.execute(
          "INSERT OR IGNORE INTO care_log (plant_id, care_date) VALUES (?, ?)",
          (plant_id, when.isoformat())  
        )
    return plant_id
    
def add_plant(conn,
              name: str,
              plant_type: str,
              location: str,
              interval_days: int,
              acquired: date
              ) -> Plant:
    """ Add a new plant to the database and return the Plant object"""
    cursor = conn.execute(
        "INSERT INTO plants (name, plant_type, location, interval_days, acquired) VALUES (?, ?, ?, ?, ?)",
        (name,
         plant_type,
         location,
         interval_days,
         acquired.isoformat()
         ),
    )
    conn.commit()
    return Plant(cursor.lastrowid, name, plant_type, location, interval_days, acquired)

def get_history(conn: sqlite3.Connection, plant_id: int) -> list[date]:
    """Every watering date for one plant, newest frist."""
    rows = conn.execute(
        "SELECT care_date FROM care_log WHERE plant_id = ? ORDER BY care_date DESC",
        (plant_id,),
    ).fetchall()
    return [date.fromisoformat(row["care_date"]) for row in rows]

def get_plant(conn: sqlite3.Connection, plant_id: int) -> Plant:
    """Load one plant with its waterings. Raises PLantNotFound for unknown IDs."""
    _require_plant(conn, plant_id)
    row = conn.execute("SELECT * FROM plants WHERE id = ?", (plant_id,)).fetchone()
    return _row_to_plant(row, get_history(conn, plant_id))

def get_all_plants(conn: sqlite3.Connection) -> list[Plant]:
    """Load every plant with its waterings, in ID order."""
    plant_rows = conn.execute("SELECT * FROM plants ORDER BY id").fetchall()
    # One pass over the care log, grouping the dates by plant ID.
    dates_by_plant: dict[int, list[date]] = {}
    for row in conn.execute("SELECT plant_id, care_date FROM care_log ORDER BY care_date"):
        dates_by_plant.setdefault(row["plant_id"], []).append(date.fromisoformat(row["care_date"]))
    return [_row_to_plant(row, dates_by_plant.get(row["id"], [])) for row in plant_rows]

def update_plant(conn: sqlite3.Connection, plant: Plant) -> None:
    """Saves the edited details of an existing plant"""
    _require_plant(conn, plant.id)
    conn.execute(
        "UPDATE plants SET name = ?, plant_type = ?, location = ?, interval_days = ?,"
        " acquired = ? WHERE id = ?",
        (plant.name, plant.plant_type, plant.location, plant.interval_days, plant.acquired.isoformat(), plant.id),
    )
    conn.commit()
    
def delete_plant(conn: sqlite3.Connection, plant_id: int) -> None:
    """Delete a plant"""
    _require_plant(conn, plant_id)
    conn.execute("DELETE FROM plants WHERE id = ?", (plant_id,))
    conn.commit()
    
        
def add_watering(conn: sqlite3.Connection, plant_id: int, when: date) -> bool:
    """Record True if a new entry was stored, or False if that date was already recored
    allowing for multiple waterings on the same plant on the same day"""
    _require_plant(conn, plant_id)
    cursor = conn.execute(
    "INSERT OR IGNORE INTO care_log (plant_id, care_date) VALUES (?, ?)",
    (plant_id, when.isoformat()),
)
    conn.commit()
    return cursor.rowcount == 1

#******************************************************
# Imports and Exports
#******************************************************

# Describes how each JSON value type is in a import error

JSON_TYPE_NAMES = {str: "text in quotes", int: "a whole number", list: "a list"}

def _read_key(record: dict, key: str, kind: type, parse, problems: list[str]):
    """
    Checks one key of an import record
    
    The key must be there, and hold the right type of JSON valur=e, and pass the
    same rule as the forms. returns a cleaned value or none after adding a line to problems
    """
    if key not in record:
        problems.append(f"{key}: is missing.")
        return None
    value = record[key]
    """
    type() was chosen over isinstance(), as python counts true and false as 1's & 0's,
    and we need an interval to not be accespted as a 1 or 0
    """
    if type(value) is not kind:
        problems.append(f"{key}: must be {JSON_TYPE_NAMES[kind]}.")
        return None
    try:
        return parse(value)
    except ValidationError as error:
        problems.append(f"{key}: {error.message}")
        return None

def _plant_from_record(record, today: date) -> tuple[Plant | None, list[str]]:
    """
    Check one plant from an import file. Returns (plant, problems).
    """
    if not isinstance(record, dict):
        return None, ["must be an object in curly brakcets"]
    problems: list[str] = []
    name = _read_key(record, "name", str, parse_name, problems)
    plant_type = _read_key(record, "type", str, parse_type, problems)
    location = _read_key(record, "location", str, parse_location, problems)
    interval = _read_key(record, "interval_days", int, lambda number: parse_interval_days(str(number)), problems)
    acquired = _read_key(record, "acquired", str, parse_date, problems)
    if acquired is not None:
        if acquired > today:
            problems.append("acquired: cannot be in the future.")
        elif age_of(acquired, today)[0] > MAX_AGE_YEARS:
            problems.append(f"acquired: cannot be more than {MAX_AGE_YEARS} years ago.")
    
    waterings: set[date] = set()
    entires = record.get("waterings", [])
    if type(entires) is not list:
        problems.append("waterings: must be a list of dates.")
    else:
        for position, entry in enumerate(entires, start=1):
            if type(entry) is not str:
                problems.append(f"waterings, entry {position}: must be a date in quotes.")
                continue
            try:
                waterings.add(parse_watering_date(entry, today))
            except ValidationError as error:
                problems.append(f"waterings, entry {position}: {error.message}")
            
    if problems:
        return None, problems
    return Plant(None, name, plant_type, location, interval, acquired, sorted(waterings)), []

def read_import_file(path, today: date) -> list[Plant]:
    """
    Reads and checks a JSON import file
    
    returns the plants ready to import. if anything is wrong, it raises 
    ImportFailed listing the problem, so one bad record means nothing is imported
    allowing the user to fix the broken file
    """
    try: 
        with open(path, encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        raise ImportFailed([f"The file was not found: {path}"]) from None
    except OSError as error:
        raise ImportFailed([f"The file could not be opened ({error.strerror})"]) from None
    except ValueError as error:
        raise ImportFailed([f"The file is not valid JSON ({error})"]) from None
    
    if not isinstance(data, dict) or type(data.get("plants")) is not list:
        raise ImportFailed(['The file must be a JSON object holding a plant list'])
    if not data["plants"]:
        raise ImportFailed(["The file has no plants in it"])
    
    plants: list[Plant] = []
    errors: list[str] = []
    for number, record in enumerate(data["plants"], start=1):
        plant, problems = _plant_from_record(record, today)
        errors.extend(f"Plant {number}, {problem}" for problem in problems)
        if plant is not None:
            plants.append(plant)
    if errors:
        raise ImportFailed(errors)
    return plants

def import_plants(conn: sqlite3.Connection, plants: list[Plant]) -> int:
    """
    Save plants returned by read_import_file. returns how many were added.
    
    All the inserts share one transaction, so either every plant is added or,
    if anything goes wrong half wat through, no plants are effected
    """
    with conn:
        for plant in plants:
            _insert_plant(conn, plant)
    return len(plants)

def export_plants(conn: sqlite3.Connection, path) -> int:
    """
    Writes every plant and its history to a JSON file, and retuns how many
    """
    plants = get_all_plants(conn)
    data = {
        "plants": [
            {
                "name": plant.name,
                "type": plant.plant_type,
                "location": plant.location,
                "interval_days": plant.interval_days,
                "acquired": format_date(plant.acquired),
                "waterings": [format_date(when) for when in sorted(plant.waterings)],
            }
            for plant in plants
        ]
    }
    try:
        with open(path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
            file.write("\n")
    except OSError as error:
        raise ValidationError("path", f"That file could not be written ({error.strerror}).") from None
    return len(plants)

        
        