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

ALL_LOCATIONS = "All locations"

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
        
        self.sort_column = "id"
        self.descending = False
        self.today_only = False
        self.search_var = tk.StringVar()
        self.location_var = tk.StringVar(value=ALL_LOCATIONS)
        
        self.build_filter_bar()
        self.build_table()
        self.build_bottom_bar()
        self.refresh()
        
    def build_filter_bar(self) -> None:
        """
        Creates a row above the table: Find box, locations dropdown, due today and all
        """
        bar = tk.Frame(self)
        bar.pack(fill="x", padx=8, pady=(8, 0))
        
        tk.Label(bar, text="Find:").pack(side="left")
        box = tk.Entry(bar, textvariable=self.search_var, width=20)
        box.pack(side="left", padx=(4, 12))
        # Redraws the table every time a change occurs
        self.search_var.trace_add("write", lambda *args:self.refresh())
        
        tk.Label(bar, text="Locations:").pack(side="left")
        self.location_box = ttk.Combobox(
            bar, textvariable=self.location_var, values=[ALL_LOCATIONS],
            state="readonly", width=18)
        self.location_box.pack(side="left", padx=(4, 12))
        self.location_box.bind("<<ComboboxSelected>>", lambda event: self.refresh())
        
        ttk.Button(bar, text="Today", command=self.on_today).pack(side="left", padx=(0, 4))
        ttk.Button(bar, text="All", command=self.on_all).pack(side="left")
        
    
        

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
            """
            Clicking a heading sorts by that column.
            """
            self.tree.heading(name, text=heading, command=lambda name=name: self.on_heading(name))
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
        self.info = tk.StringVar()
        tk.Label(self, textvariable=self.info).pack(fill="x", padx=8, anchor="w")
        bar = tk.Frame(self)
        bar.pack(fill= "x", padx= 8, pady= (0, 8))
        self.status = tk.StringVar()
        tk.Label(bar, textvariable=self.status).pack(side="left")
        ttk.Button(bar, text= "Refresh", command= self.refresh).pack(side= "right")
        
    def on_heading(self, column: str) -> None:
        """
        When a heading is clicked sort by that column, or undo if it is already sorted by said column
        """
        if column == self.sort_column:
            self.descending = not self.descending
        else:
            self.sort_column = column
            self.descending = False
        if self.today_only:
            self.refresh(note="Today view is ranked by urgency")
        else:
            self.refresh()
        
    def on_today(self) -> None:
        """
        Today button: only shows plants that need attention
        """
        self.today_only = True
        self.refresh()
        
    def on_all(self) -> None:
        """
        All button: clear the find box, the location and today
        """
        self.today_only = False
        self.location_var.set(ALL_LOCATIONS)
        self.search_var.set("")
        self.refresh()
    
    
    def refresh(self, note: str = "") -> None:
        """
        Redraws the table and the status line from the database
        """
        today = date.today()
        plants = core.get_all_plants(self.conn)
        
        choices = [ALL_LOCATIONS] + core.known_locations(plants)
        self.location_box["values"] = choices
        if self.location_var.get() not in choices:
            self.location_var.set(ALL_LOCATIONS)
        chosen = self.location_var.get()
        location = "" if chosen == ALL_LOCATIONS else chosen
        search = " ".join(self.search_var.get().split())
        
        shown = core.visible_plants(
            plants, today,
            search = search,
            location = location,
            today_only = self.today_only,
            sort_column = self.sort_column,
            descending = self.descending
        )
        
        for row in self.tree.get_children():
            self.tree.delete(row)
        for plant in shown:
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

        self.show_headings()
        self.info.set(note or self.describe_view (len (shown), len (plants), search, location))
        self.status.set(f"{core.status_line(plants, today)}     |   {self.describe_order()}")
    
    def show_headings(self) -> None:
        """
        Puts an arrow on the headings of the column the table is sorted by.
        """
        for name, heading, width in COLUMNS:
            if name == self.sort_column and not self.today_only:
                arrow = " \u25bc" if self.descending else " \u25b2"     # down or up triangle
                self.tree.heading(name, text=heading + arrow)
            else:
                self.tree.heading(name, text=heading)
    
    def describe_order(self) -> str:
        """
        Says how the rows are ordered
        """
        if self.today_only:
            return "ranked by urgency"
        return f"sorted by: {self.sort_column} {' (desc) ' if self.descending else ''}"
    
    def describe_view(self, shown: int, total: int, search: str, location: str) -> str:
        """
        Line saying what is hidden, or why the table is empty
        """
        reasons = []
        if search:
            reasons.append(f'find "{search}"')
        if location:
            reasons.append(f"location {location}")
        if self.today_only:
            reasons.append("today view")
        if total == 0:
            return "No plants yet."
        if shown == 0:
            if self.today_only and not (search or location):
                return "Nothing needs attention today."
            return f"No plant match ({','.join(reasons)}). Click all to clear."
        if reasons:
            return f"Showing {shown} of {core.plural(total, 'plant')} ({', '.join(reasons)}). Click All to clear."
        return ""

def main() -> None:
    """
    Opens the database, shows the window and closes the databse after
    """
    conn = core.connect()
    PlantApp(conn).mainloop()
    conn.close()
    
if __name__ == "__main__":
    main()