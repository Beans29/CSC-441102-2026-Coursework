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

HISTORY_SHOWN = 10

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
    
def water_plant(conn, plant: core.Plant, date_text: str) -> str:
    """Marks a plant as watered and returns the line to show"""   
    today = date.today()
    when = core.parse_watering_date(date_text, today) if date_text.strip() else today
    if core.add_watering(conn, plant.id, when):
        return f"Watered {core.format_id(plant.id)} {plant.name} on {core.format_date(when)}."
    return f"Already recorded for {core.format_date(when)}. Nothing was changed."
    
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

def confirm(prompt: str) -> bool:
    """Ask yes or no, only yes counts"""
    return input(prompt).strip().lower() == "yes"

#*************************************************
# Details Scrren
#*************************************************

def draw_details_screen(plant: core.Plant, history: list[date], today: date) -> None:
    """Show one plant's details and its most recent waterings."""
    print()
    print(f"PLANT {core.format_id(plant.id)} - {plant.name}")
    print()
    for label, value in core.details_rows(plant, today):
        print(f"{label:<14}{value}")
    print()
    print(f"History ({core.plural(len(history), 'watering')})")
    for when in history[:HISTORY_SHOWN]:
        print(f"  {core.format_date(when)}")
    if len(history) > HISTORY_SHOWN:
        print(f"  ... and {len(history) - HISTORY_SHOWN} earlier. Type history to list them all.")
    print("-" * 60)
    print("edit   water [date]   history   remove   back")

def show_history(plant: core.Plant, history: list[date]) -> None:
    """List watering history of one plant"""
    print()
    print(f"HISTORY {core.format_id(plant.id)} - {plant.name} ({core.plural(len(history), 'watering')})")
    for when in history:
        print(f" {core.format_date(when)}")

def remove_plant(conn, plant: core.Plant, history: list[date]) -> bool:
    """Delete a plant after a typed yes. Return true if deleted"""
    print (f" This permanently deletes {core.format_id(plant.id)} {plant.name}"
           f" and its {core.plural(len(history), 'watering')}.")
    if not confirm("Type yes to delete it: "):
        return False
    core.delete_plant(conn, plant.id)
    return True

def details_screen(conn, plant_id: int) -> str:
    """Show one plant until the user goes back.""" 
    message = "" 
    while True:
        """ Reloaded each time, so edits appear without refresh"""
        plant = core.get_plant(conn, plant_id)
        history = core.get_history(conn, plant_id)
        draw_details_screen(plant, history, date.today())
        if message:
            print(message)
            message = ""
        word, rest = parse_command(input(f"plant {core.format_id(plant_id)}> "))
        try:
            if word == "edit":
                message = edit_screen(conn, plant)
            elif word == "water":
                message = water_plant(conn, plant, rest)
            elif word == "history":
                show_history(plant, history)
            elif word == "remove":
                if remove_plant(conn, plant, history):
                    return f"Removed {core.format_id(plant.id)} {plant.name} and its history."
                message = "Nothing was changed."
            elif word == "back":
                return ""
            elif word:
                message = "Type edit, water, history, remove or back."
        except core.ValidationError as error:
            message = f"  ! {error}"

#******************************************************
# Edit Screen
#******************************************************

EDIT_FIELDS = {
    "1": (("name", "New name: ", core.parse_name),),
    "2": (("plant_type", "New type: ", core.parse_type),),
    "3": (("location", "New location: ", core.parse_location),),
    "4": (("interval_days", "Water every how many days? ", core.parse_interval_days),),
    "5": (("age_years", "Age, whole years (0 if under a year): ", core.parse_age_years),
          ("age_months", "Age, extra months (0 - 11): ", core.parse_age_months)), 
}

def field_lines(fields: dict) -> list[tuple[str, str]]:
    """The five lines of the edit screen"""
    age = f"{core.plural(fields['age_years'], 'year')} {core.plural(fields['age_months'], 'month')}"
    return [
        ("Name", fields["name"]),
        ("Type", fields["plant_type"]),
        ("Location", fields["location"]),
        ("Water every", core.plural(fields["interval_days"], "days")),
        ("Age", age),
    ]

def draw_edit_screen(plant: core.Plant, original: dict, working: dict) -> None:
    """Shows the fields, making each change as 'old -> new' ."""
    print()
    print(f"EDIT {core.format_id(plant.id)} - {plant.name}")
    print()
    lines = zip(field_lines(original), field_lines(working))
    for number, ((label, before), (_, after)) in enumerate(lines, start=1):
        value = before if before == after else f"{before}  ->  {after} *"
        print(f"{number}  {label:<14}{value}")
    print("-" * 60)
    print("<number> change that field   save   cancel")

        
def edit_screen(conn, plant: core.Plant) -> str:
    """ Edit one plant, and retruns a message for the details screen 
    
        The screen works on a copy of the plant's values. No database changes
        happen ultil it is saced
        """
    today = date.today()
    original = core.plant_to_fields(plant, today)
    working = dict(original)
    while True:
        draw_edit_screen(plant, original, working)
        word, _ = parse_command(input(f"edit {core.format_id(plant.id)}> "))
        if word in EDIT_FIELDS:
            answers = {field: ask(prompt, parser) for field, prompt, parser in EDIT_FIELDS[word]}
            working.update(answers)
        elif word == "save":
            if working == original:
                return "No changes were made."
            core.update_plant(conn, core.make_plant(working, today, original=plant))
            return f"Saved changes to {core.format_id(plant.id)} {working['name']}."
        elif word == "cancel":
            return "Cancelled. nothing was changed"
        elif word:
            print("Type a number, save or cancel")
    
def main() -> None:
    """Show the table, read a comment, repeat until the user types 'Quit'."""
    if os.name == "nt":
        os.system("")   #Windows terminal colour support
    conn = core.connect()
    while True:
        print_table(core.get_all_plants(conn), date.today())
        word, rest = parse_command(input("<ID> to open, add, water <ID> <date>, or quit > "))
        try:
            if word.isdigit():
                message = details_screen(conn, core.parse_plant_id(word))
                if message:
                    print(message)
            elif word == "add":
                add_screen(conn)
            elif word == "water":
                print(water_command(conn, rest))
            elif word == "quit":
                break
            elif word:
                print("Type an ID, water or quit.")
        except (core.ValidationError, core.PlantNotFound) as error:
            print(f"  ! {error}")
    conn.close()
    
if __name__ == "__main__":
    main()