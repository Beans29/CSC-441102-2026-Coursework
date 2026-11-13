"""File: cli.py
CSC-44102-2026-Coursework
Author: X9J77
"""

from datetime import date
import core

def print_table(plants: list[core.Plant], today: date) -> None:
    """Print the plants in table format"""
    heading = (f"{'ID':<4}  {'Name':<20}  {'Age':<9}  {'Type':<12}  "
               f"{'Location':<12}  {'Water every'}")    
    print()
    print(heading)
    print("-" * len(heading))
    if not plants:
        print("No plants yet, Type add to add a new plant.")
    for plant in plants:
        age = core.format_age(*core.age_of(plant.acquired, today)) 
        
        print(f"{plant.id:<4} {plant.name:<20} {plant.plant_type:<20} {age:<9} {plant.location:<20} {plant.interval_days:<15} Days")
    print()
    

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
    
def main() -> None:
    """Show the table, read a comment, repeat until the user types 'Quit'."""
    conn = core.connect()
    while True:
        print_table(core.get_all_plants(conn), date.today())
        command = input("Add or Quit > ").strip().lower()
        if command == "add":
            add_screen(conn)
        elif command == "quit":
            break
        else:
            print("Type Add or Quit.")    
    conn.close()
    
if __name__ == "__main__":
    main()