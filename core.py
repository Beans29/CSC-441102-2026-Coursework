"""File: core.py
CSC-44102-2026-Coursework
Author: X9J77
"""

import calendar
import sqlite3
from dataclasses import dataclass
from datetime import date
from pathlib import Path


DB_FILENAME = "plants.db"


MAX_NAME = 20               #Sets the max and minum length of the name, type, location and interval days
MAX_TYPE = 20
MAX_LOCATION = 20
MIN_INTERVAL_DAYS = 1
MAX_INTERVAL_DAYS = 365
MAX_AGE_YEARS = 100


FIELD_LABLES = {
    "name": "Name",
    "plant_type": "Type",
    "location": "Location",}


@dataclass
class Plant:
    id: int | None          #Value set to None until the database assigns an ID to the plant
    name: str               #The name of the plant
    plant_type: str         #The type of the plant
    location: str           #The location of the plant
    interval_days: int      #The watering interval in days
    acquired: date          #The date the plant was acquired


class ValidationError(Exception):
    """ Raised when a value failes its rule
    
    'field' names the field that failed validation.
    'message' describes the problem.
    """
    
    def __init__(self, field_name: str, message: str):
        super().__init__(message)
        self.field = field_name
        self.message = message
        
        
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
        raise ValidationError( field_name,
                               f"{label} cannot be longer than {max_len} characters or fewer (That was {len(text)} characters).")
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


#************************************************************
#   Database Functions
#************************************************************
   

def connect(path=None) -> sqlite3.Connection:
    """Connect to the database, creating the file and tables if they do not exist"""
    if path is None:
        path = Path(__file__).resolve().parent / DB_FILENAME
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
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
    return conn

def _row_to_plant(row: sqlite3.Row) -> Plant:
    """Turn a database row into a Plant object"""
    return Plant(
        row["id"],
        row["name"],
        row["plant_type"],
        row["location"],
        row["interval_days"],
        date.fromisoformat(row["acquired"])
    )

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
    
def get_all_plants(conn) -> list[Plant]:
    """Retrun every plant, oldest first"""
    rows = conn.execute(
        "SELECT id, name, plant_type, location, interval_days, acquired FROM plants ORDER BY id"
        ).fetchall()
    return [_row_to_plant(row) for row in rows]

    



