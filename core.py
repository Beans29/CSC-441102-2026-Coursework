"""File: core.py
CSC-44102-2026-Coursework
Author: X9J77

"""

import sqlite3
from dataclasses import dataclass
from pathlib import Path

DB_FILENAME = "plants.db"

@dataclass
class Plant:
    id: int | None
    name: str
    plant_type: str
    location: str
    interval_days: int
    
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

    



