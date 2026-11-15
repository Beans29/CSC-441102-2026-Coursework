"""File: cli.py
CSC-44102-2026-Coursework
Author: X9J77
"""

import os
import sys
import core

from datetime import date

ANSI_CODES = {"red": "\033[31m", "amber": "\033[33m", "blue": "\033[34m"}
ANSI_RESET = "\033[0m"

def colour(text: str, state: core.WaterState) -> str:
    """Terminal text state colour"""
    name = core.STATE_COLOUR[state]
    if name is None or not sys.stdout.isatty() or "NO_COLOR" in os.environ:
        return text
    return f"{ANSI_CODES[name]}{text}{ANSI_RESET}"


def print_table(plants: list[core.Plant], today: date) -> None:
    """Print the plants in table format"""
    heading = (f"{'ID':<4}  {'Name':<20}  {'Age':<9}  {'Type':<12}  "
               f"{'Location':<12}  {'Next Water'}")    
    print()
    print(heading)
    print("-" * len(heading))
    if not plants:
        print("No plants yet, Type add to add a new plant.")
    for plant in plants:
        age = core.format_age(*core.age_of(plant.acquired, today)) 
        row = (f"{core.format_id(plant.id):<4}  {plant.name:<20}  {age:<9}  "
              f"{plant.plant_type:<12}  {plant.location:<12}  "
              f"{core.format_next_water(plant, today)}")
        print(colour(row, core.water_state(plant, today)))
    print("-" * len(heading))
    print(core.status_line(plants, today))
    print()
    
def parse_command(line: str) -> tuple[str, str]:
    """Split what the user typed into a command word and the rest. 
    E.g "water 1" gives ("water", "1")."""
    parts = line.strip().split(None, 1)
    word = parts[0].lower() if parts else ""
    rest = parts[1] if len(parts) > 1 else ""
    return word, rest
    

def ask (prompt: str, parser):
    """Ask a question and parse the answer. Repeat until the answer is valid."""
    while True:
        try:
            return parser(input(prompt))
        except core.ValidationError as e:
            print(f" {e.message}")
            

def add_screen(conn) -> None:
    """Ask for the details of a new plant and add it to the database"""
    
    name = ask("Name: ", core.parse_name)
    plant_type = ask("Type: ", core.parse_type)
    location = ask("Location: ", core.parse_location)
    interval_days = ask("Water every how many days? ", core.parse_interval_days)
    years = ask("How many years old is the plant? ", core.parse_age_years)
    months = ask("How many months old is the plant? ", core.parse_age_months)
    acquired = core.acquired_from_age(years, months, date.today())
    plant = core.add_plant(conn, name, plant_type, location, interval_days, acquired)
    print(f"Added {plant.name}.")
    
def water_command(conn, rest: str) -> str:
    """Handle water <ID> [date]. 
    No date means today"""
    id_text, _, date_text = rest.strip().partition(" ")
    plant = core.get_plant(conn, core.parse_plant_id(id_text))
    today = date.today()
    when = core.parse_watering_date(date_text, today) if date_text.strip() else today
    if core.add_watering(conn, plant.id, when):
        return f"Watered {core.format_id(plant.id)} {plant.name} on {core.format_date(when)}."
    return f"Already recorded for {core.format_date(when)}. Nothing was changed."

def main() -> None:
    """Show the table, read a comment, repeat until the user types 'Quit'."""
    conn = core.connect()
    while True:
        print_table(core.get_all_plants(conn), date.today())
        word, rest = parse_command(input("add, water <ID> <date>, or quit > "))
        try:
            if word == "add":
                add_screen(conn)
            elif word == "water":
                print(water_command(conn, rest))
            elif word == "quit":
                break
            elif word:
                print("Type add, water or quit.")
        except (core.ValidationError, core.PlantNotFound) as error:
            print(f"  ! {error}")
    conn.close()
    
if __name__ == "__main__":
    main()