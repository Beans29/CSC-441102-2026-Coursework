"""
File Name: gui.py
Author: X9J77

"""
import tkinter as tk
from datetime import date
from tkinter import ttk

import core

COLUMNS = (
    ("id", "ID", 55),
    ("name", "Name", 160),
    ("age", "Age", 90),
    ("type", "Type", 110),
    ("location", "Location", 150),
    ("next", "Next Water", 140),
)

# Text colour of a row for each colour name in nore.STATE_COLOUR
ROW_COLOURS = {"red": "red",
               "amber": "#b36b00",
               "blue": "blue"}

class PlantApp(tk.Tk):
    """
    The main window: Plant table, Status line and refresh button
    """
    
    def __init__(self, conn):
        super().__init__()
        self.conn = conn
        self.title("Plant Care")
        self.build_table()
        self.build_bottom_bar()
        self.refresh()
        
    def build_table(self) -> None:
        """
        Creates the table that lists all the plants, with the addtion of a scroll bar for eaier navigation =
        """
        frame = tk.Frame(self)
        frame.pack(fill="both",
                   expand=True,
                   padx=8,
                   pady=8)
        
        names = tuple(name for name, heading, width in COLUMNS)
        self.tree = ttk.Treeview(frame, columns=names, show="headings", height=15)
        for name, heading, width in COLUMNS:
            self.tree.heading(name, text=heading)
            self.tree.column(name, width=width)
        for colour_name, text_colour, in ROW_COLOURS.items():
            self.tree.tag_configure(colour_name, foreground=text_colour)
            
        scroll = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
    
    def build_bottom_bar(self) -> None:
        """
        Creates status line and the refresh button under the table
        """
        bar = tk.Frame(self)
        bar.pack(fill="x", padx=8, pady=(0, 8))
        self.status = tk.StringVar()
        tk.Label(bar, textvariable=self.status).pack(side="left")
        ttk.Button(bar, text="Refresh", command=self.refresh).pack(side="right")
    
    def refresh(self) -> None:
        """
        Redraws the table and the status line from the database
        """
        today = date.today()
        plants = core.get_all_plants(self.conn)
        
        for row in self.tree.get_children():
            self.tree.delete(row)
        for plant in plants:
            age = core.format_age(*core.age_of(plant.acquired, today))
            colour_name = core.STATE_COLOUR[core.water_state(plant,today)]
            self.tree.insert(
                "", "end",
                iid=str(plant.id),
                values=(
                    core.format_id(plant.id),
                    plant.name,
                    age,
                    plant.plant_type,
                    plant.location,
                    core.format_next_water(plant, today),
                ),
                tags=(colour_name,) if colour_name else (),
            )
        self.status.set(core.status_line(plants, today))

def main() -> None:
    """
    Opens the database, shows the window and closes the databse after
    """
    conn = core.connect()
    PlantApp(conn).mainloop()
    conn.close()
    
if __name__ == "__main__":
    main()