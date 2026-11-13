"""File: core.py
CSC-44102-2026-Coursework
Author: X9J77
"""

import sqlite3
from dataclasses import dataclass
from pathlib import Path


DB_FILENAME = "plants.db"


MAX_NAME = 20
MAX_TYPE = 20
MAX_LOCATION = 20
MIN_INTERVAL_DAYS = 1
MAX_INTERVAL_DAYS = 365


FIELD_LABLES = {
    "name": "Name",
    "plant_type": "Type",
    "location": "Location",}


@dataclass
class Plant:
    id: int | None
    name: str
    plant_type: str
    location: str
    interval_days: int
    

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


def parse_interval_days(raw: str) -> int:
    """Check a watering interval: a whole number of days between 1 and 365"""
    message = f"Watering interval must be a whole number of days between {MIN_INTERVAL_DAYS} and {MAX_INTERVAL_DAYS}."
    try:
        days = int(raw.strip())
    except ValueError:
        raise ValidationError("interval_days", message) from None
    if not MIN_INTERVAL_DAYS <= days <= MAX_INTERVAL_DAYS:
        raise ValidationError("interval_days", message)
    return days


#************************************************************
#   Database Functions
#************************************************************
   

def connect(path=None) -> sqlite3.Connection:
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
            interval_days INTEGER NOT NULL
        )
        """
    )
    return conn

def add_plant(conn,
              name: str,
              plant_type: str,
              location: str,
              interval_days: int
              ) -> Plant:
    
    cursor = conn.execute(
        "INSERT INTO plants (name, plant_type, location, interval_days) VALUES (?, ?, ?, ?)",
        (name,
         plant_type,
         location,
         interval_days
         )
    )
    conn.commit()
    return Plant(cursor.lastrowid, 
                 name,
                 plant_type,
                 location,
                 interval_days)


def get_all_plants(conn) -> list[Plant]:
    """Retrun every plant"""
    rows = conn.execute("SELECT id, name, plant_type, location, interval_days FROM plants ORDER BY id").fetchall()
    return [Plant(row["id"], row["name"], row["plant_type"], row["location"], row["interval_days"]) 
            for row in rows]

    



