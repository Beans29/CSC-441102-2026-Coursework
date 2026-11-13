"""File: cli.py
CSC-44102-2026-Coursework
Author: X9J77

"""

import core

def print_table(plants: list[core.Plant]) -> None:
    """Print the plants in table format"""
    print()
    print(f"{'ID':<5} {'Name':<20} {'Type':<15} {'Location':<15} {'Interval (Days)':<15}")
    print("-" * 80)
    
    if not plants:
        print("No plants found. Type 'add' to add a new plant.")
        
    for plant in plants:
        print(f"{plant.id:<5} {plant.name:<20} {plant.plant_type:<15} {plant.location:<15} {plant.interval_days:<15} Days")
        
    print()
    

def ask (prompt: str, parser):
    """Ask a question and parse the answer. Repeat until the answer is valid."""
    while True:
        try:
            return parser(input(prompt))
        except core.ValidationError as e:
            print(f"Invalid input for {e.field}: {e.message}")
            


def add_screen(conn) -> None:
    """Ask for the details of a new plant and add it to the database"""
    
    name = ask("Name: ", core.parse_name)
    plant_type = ask("Type: ", core.parse_type)
    location = ask("Location: ", core.parse_location)
    interval_days = ask("Water every how many days? ", core.parse_interval_days)
    plant = core.add_plant(conn, name, plant_type, location, interval_days)
    print(f"Added {plant.name}.")
    
    
    

def main() -> None:
    """Show the table, read a comment, repeat until the user types 'Quit'."""
    conn = core.connect()
    while True:
        print_table(core.get_all_plants(conn))
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



