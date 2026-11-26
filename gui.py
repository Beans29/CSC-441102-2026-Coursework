"""
File Name: gui.py
Author: X9J77

"""
import os
import tkinter as tk
from datetime import date
from tkinter import ttk, messagebox, filedialog

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

FROM_FIELDS = (
    ("name", "Name", core.parse_name),
    ("plant_type", "Type", core.parse_type),
    ("location", "Location", core.parse_location),
    ("interval_days", "water every (days)", core.parse_interval_days),
    ("age_years", "Age: years", core.parse_age_years),
    ("age_months", "Age: months (0 to 11)", core.parse_age_months),
)
ERROR_RED = "red"

JSON_FILES = [("JSON files", "*.json"), ("All files", "*.*")]   #File types offered in the Import and Export
MAX_ERRORS_SHOWN = 12                                           #Import error box lists this many problems, then says how many more

# Text colour of a row for each colour name in nore.STATE_COLOUR
ROW_COLOURS = {"red": "red",
               "amber": "#b36b00",
               "blue": "blue"}

def run_modal(window: tk.Toplevel, parent) -> None:
    """
    Shows a window on top of its parent window and waits here until its closed.
    
    while its open the cannot click elsewere in the app
    """
    
    window.transient(parent)    #Keeps it infront of parent
    window.wait_visibility()    #Window must be on the screen before it can take the grab
    window.grab_set()           #Send all clicks and keys to this window
    parent.wait_window(window)  #Pasue here utll the window closes
    if isinstance(parent, tk.Toplevel) and parent.winfo_exists():
        parent.grab_set()       #A window opened from another window
    
    
class PlantForm(tk.Toplevel):
    """
    A form with a box for each field and an error line under each box.
    
    The form only checks what was typed, if everything is valid, 'result' holds
    the cleaned values, otherwise it stays None. the caller decides what to do 
    with them, so the same form can add or edit.
    """
    
    def __init__(self, parent, title: str, values: dict | None = None):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.result = None
        values = values or {}
        
        self.vars = {}      # field name -> the text in its box
        self.errors = {}    # field name -> the error line under its box
        self.boxes = {}     # field name -> the box itself
        for row, (field_name, label, parser) in enumerate(FROM_FIELDS):
            self.vars[field_name] = tk.StringVar(value=str(values.get(field_name, "")))
            self.errors[field_name] = tk.StringVar()
            tk.Label(self, text=label).grid(row=row * 2, column=0, sticky="w", padx=8, pady=(8 ,0))
            box = tk.Entry(self, textvariable=self.vars[field_name], width=24)
            box.grid(row= row * 2, column=1, padx=8, pady=(8, 0))
            self.boxes [field_name] = box
            tk.Label(self, textvariable=self.errors[field_name], fg=ERROR_RED).grid(
                row=row * 2 + 1, column= 1, sticky= "w", padx=8
            )
            
        buttons = tk.Frame(self)
        buttons.grid( row = len (FROM_FIELDS) * 2, column= 0, columnspan= 2, pady=8)
        ttk.Button( buttons, text="Save", command=self.on_save).pack( side="left", padx=4)
        ttk.Button( buttons, text="Cancel", command=self.destroy).pack(side="left", padx=4)
        self.bind("<Return>", lambda event: self.on_save())
        self.bind("<Escape>", lambda event: self.destroy())
        self.boxes[FROM_FIELDS[0][0]].focus_set()
        
    def on_save(self) -> None:
        """
        Checks every box and shows a message under each one
        """
        clean = {}
        first_bad = None
        for field_name, label, parser in FROM_FIELDS:
            try:
                clean[field_name] = parser( self.vars [field_name].get())
                self.errors[ field_name].set("")
            except core.ValidationError as error:
                self.errors[field_name].set(error.message)
                if first_bad is None:
                    first_bad = field_name
        if first_bad is not None:
            self.boxes[first_bad].focus_set()
            return
        self.result = clean
        self.destroy()
        
class DetailsWindow(tk.Toplevel):
    """
    Shows one plants details, watering history, and buttons to water or remove it
        
    The windo reloads the plant from the database after every change, so what is showed is 
    always saved. on_change is called after a watering so the table behind can redraw. If the plant
    is removed, 'message' holds a line for the main window
    """
    def __init__(self, parent, conn, plant_id: int, on_change):
        super().__init__(parent)
        self.conn = conn
        self.plant_id = plant_id
        self.on_change = on_change
        self.message = ""
        self.resizable(False, False)
        
        self.heading = tk.StringVar()
        tk.Label(self, textvariable=self.heading).pack(anchor="w", padx=8, pady=(8, 4))
        
        self.rows_frame = tk.Frame(self)
        self.rows_frame.pack(fill="x", padx=8)
        
        self.history_title = tk.StringVar()
        tk.Label(self, textvariable=self.history_title).pack(anchor="w", padx=8, pady=(8, 0))
        history_frame = tk.Frame(self)
        history_frame.pack(anchor="w", padx=8)
        self.history_list = tk.Listbox(history_frame, height=8, width=30)
        scroll = ttk.Scrollbar(history_frame, orient="vertical", command=self.history_list.yview)
        self.history_list.configure(yscrollcommand=scroll.set)
        self.history_list.pack(side="left", fill="x", expand=True)
        scroll.pack(side="right", fill="y")
        
        water = tk.Frame(self)
        water.pack(fill="x", padx=8, pady=(8, 0))
        tk.Label(water, text="Date (empty = today):").pack(side="left")
        self.date_var = tk.StringVar()
        tk.Entry(water, textvariable=self.date_var, width=12).pack(side="left", padx=8)
        ttk.Button(water, text="water", command=self.on_water).pack(side="left")
        self.error = tk.StringVar()
        self.feedback = tk.StringVar()
        tk.Label(self, textvariable=self.error, fg=ERROR_RED).pack(anchor="w", padx=8)
        tk.Label(self, textvariable=self.feedback).pack(anchor="w", padx=8)
        
        buttons = tk.Frame(self)
        buttons. pack(pady= 8)
        ttk.Button(buttons, text="Edit", command=self.on_edit).pack(side="left", padx=4)
        ttk.Button(buttons, text="Remove", command=self.on_remove).pack(side="left", padx=4)
        ttk.Button(buttons, text="Close", command=self.destroy).pack(side="left", padx=4)
        self.bind("<Escape>", lambda event: self.destroy())
        
        self.refresh()
        
    def refresh(self) -> None:
        """
        Relaods the plants and redraws the details and history
        """
        plant = core.get_plant(self.conn, self.plant_id)
        history = core.get_history(self.conn, self.plant_id)
        self.title(f"Plant {core.format_id(plant.id)}")
        self.heading.set(f"{core.format_id(plant.id)} - {plant.name}")
            
        for widget in self.rows_frame.winfo_children():
            widget.destroy()
        for row, (lable, value) in enumerate(core.details_rows(plant, date.today())):
            tk.Label(self.rows_frame, text=lable + ":").grid(row=row, column=0, sticky="w")
            tk.Label(self.rows_frame, text=value).grid(row=row, column=1, sticky="w", padx=(12, 0))
                
        self.history_title.set(f"History ({core.plural(len(history), 'waterings')})")
        self.history_list.delete(0, "end")
        for when in history:
            self.history_list.insert("end", core.format_date(when))
        
    def on_water(self) -> None:
        """
        Water button: Records a watering, the date typed, defaults to today if field is empty
        """
        today = date.today()
        text = self.date_var.get()
            
        try:
            when = core.parse_watering_date(text, today) if text.strip() else today
        except core.ValidationError as error:
            self.error.set(error.message)
            self.feedback.set("")
            return
        plant = core.get_plant(self.conn, self.plant_id)
        if core.add_watering(self.conn, self.plant_id, when):
            self.feedback.set(f"Watered {core.format_id(plant.id)} {plant.name} on {core.format_date(when)}.")
        else:
            self.feedback.set(f"Already recored for {core.format_date(when)}. Nothing was changed")
                
        self.error.set("")
        self.date_var.set("")
        self.refresh()
        self.on_change()
        
    def on_edit(self) -> None:
        """
        Edit button: shows the form with the plants values, then saves what was changed
        """
        today = date.today()
        plant = core.get_plant(self.conn, self.plant_id)
        orginal = core.plant_to_fields(plant, today)
        form = PlantForm(self, f"Edit plant {core.format_id(plant.id)}", values=orginal)
        run_modal(form, self)
        
        if form.result is None:     # Cancelled or window was closed
            return
        
        if form.result == orginal:
            self.error.set("")
            self.feedback.set("No changes were made.")
            return
        try:
            core.update_plant(self.conn, core.make_plant(form.result, today, original=plant))
        except core.PlantNotFound as error:
            messagebox.showerror("Plant Care", str(error), parent=self)
            self.destroy()
            return
        self.error.set("")
        self.feedback.set(f"Saved cahnges to {core.format_id(plant.id)} {form.result['name']}.")
        self.refresh()
        self.on_change()
        
    def on_remove(self) -> None:
        """
        Remove button: deletes the plant and its history after confirmation
        """
        plant = core.get_plant(self.conn, self.plant_id)
        count = len(core.get_history(self.conn, self.plant_id))
        question = (f"Delete {core.format_id(self.plant_id)} {plant.name} and its "
                    f"{core.plural(count, 'watering')}? This cannot be undone")
        if not messagebox.askyesno("Remove plant", question, parent=self):
            return
        core.delete_plant(self.conn, self.plant_id)
        self.message = f"Removed {core.format_id(plant.id)} {plant.name} and its history"
        self.destroy()
        
class SummaryWindow(tk.Toplevel):
    """
    The location sumary: for each location, its plants, how many are due today and overdue
    """
            
    def __init__(self, parent, plants: list, today: date):
        super().__init__(parent)
        self.title("Locations")
        self.resizable(False, False)
                
        rows = core.location_summary(plants, today)
        columns = (("location", "Location", 160), ("plants", "Plants", 70), ("due", "Due today", 80), ("overdue", "Overdue", 70))
        self.tree = ttk.Treeview(self, columns=tuple(c[0] for c in columns), show="headings",
                                 height=min(max(len(rows) + 1, 3), 15))                
        for name, heading, width in columns:
            self.tree.heading(name, text=heading)
            self.tree.column(name, width=width, anchor="w" if name == "location" else "e")
                    
        for row in rows:
            self.tree.insert("", "end", values=(row.location, row.plants, row.due_today, row.overdue))
        self.tree.insert("", "end", values=(
            "Total",
            sum(row.plants for row in rows),
            sum(row.due_today for row in rows),
            sum(row.overdue for row in rows)))
        self.tree.pack(padx=8, pady=8)
                
        ttk.Button(self, text="Close", command=self.destroy).pack(pady=(0, 8))
        self.bind("<Escape>", lambda event: self.destroy())
        
              
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
        ttk.Button(bar, text="Add Plant", command=self.on_add).pack(side="right")
        
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
        self.tree.bind("<Double-1>", self.on_double_click)        
        
    
    def build_bottom_bar(self) -> None:
        """
        Creates the lines under the table (whats hidden, the counts) and the row of buttons
        """
        self.info = tk.StringVar()
        tk.Label(self, textvariable=self.info).pack(fill="x", padx=8, anchor="w")
        self.status = tk.StringVar()
        tk.Label(self, textvariable=self.status).pack(fill="x", padx=8, anchor="w")
        
        bar = tk.Frame(self)
        bar.pack(fill="x", padx=8, pady=8)
        
        ttk.Button(bar, text="Open", command=self.on_open_selected).pack(side="left")
        ttk.Button(bar, text="Locations", command=self.on_locations).pack(side="left", padx=4)
        ttk.Button(bar, text="Import", command=self.on_import).pack(side="left")
        ttk.Button(bar, text="Export", command=self.on_export).pack(side="left", padx=4)
        ttk.Button(bar, text="Refresh", command=self.refresh).pack(side="right")
        
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
    
    def on_add(self) -> None:
        """
        Adds plant button, Shows the form, then saves the plant if the form was filled in
        """
        form = PlantForm(self, "Add plant", values={"age_years": "0", "age_months": "0"})
        run_modal(form, self)
        if form.result is None:
            return
        new = form.result
        acquired = core.acquired_from_age(new["age_years"], new["age_months"], date.today())
        plant = core.add_plant(
            
            self.conn, new["name"],
            new["plant_type"],
            new["location"],
            new["interval_days"],
            acquired
        )
        
    def on_locations(self) -> None:
        """
        Locations button: Shows the summary window
        """
        window = SummaryWindow(self, core.get_all_plants(self.conn), date.today())
        run_modal(window, self)
            
    def on_import(self) -> None:
        """
        Import button: pick a JSON file, check all of it, then add its plants after a yes
        """
        path = filedialog.askopenfilename(parent=self, title="Import plants", filetypes=JSON_FILES)
        if not path:
            return
        try:
            plants = core.read_import_file(path, date.today())
        except core.ImportFailed as failure:
            lines = failure.errors[:MAX_ERRORS_SHOWN]
            if len(failure.errors) > MAX_ERRORS_SHOWN:
                lines.append(f"... and {len(failure.errors) - MAX_ERRORS_SHOWN} more.")
            messagebox.showerror("Nothing was imported", "\n".join(lines), parent=self)
            return
        question = f"{core.plural(len(plants), 'plant')} found in {os.path.basename(path)}. Import them?"
        if messagebox.askyesno("Import plants", question, parent=self):
            count = core.import_plants(self.conn, plants)
            self.refresh(note=f"Imported {core.plural(count, 'plant')}.")
        else:
            self.refresh(note="Nothing was imported.")
        
    def on_export(self) -> None:
        """
        Export button: picks a file name, then writes every plant and its history to it.
        """
        path = filedialog.asksaveasfilename(
            parent=self, title="Export plants", defaultextension=".json",
            initialfile="my_plants.json", filetypes=JSON_FILES)
        if not path:                    # the file window was cancelled
            return
        try:
            count = core.export_plants(self.conn, path)
        except core.ValidationError as error:
            messagebox.showerror("Nothing was exported", error.message, parent=self)
            return
        self.refresh(note=f"Exported {core.plural(count, 'plant')} to {path}.")
    
    def on_double_click(self, event) -> None:
        """
        Double-click on a row: opens that plant.
        """
        row = self.tree.identify_row(event.y)
        if row:
            self.open_plant(int(row))
    
    def on_open_selected(self) -> None:
        """
        Open button: Opens the highlighted plant
        """
        selected = self.tree.selection()
        if not selected:
            self.refresh(note="Click a plant first, then open")
            return
        self.open_plant(int(selected[0]))
        
    def open_plant(self, plant_id: int) -> None:
        """
        Shows the details window and waits until its closed, then redraws the table.
        """
        try: 
            core.get_plant(self.conn, plant_id)
        except core.PlantNotFound as error:
            messagebox.showerror("Plant Care", str(error), parent=self)
            self.refresh()
            return
        window = DetailsWindow(self, self.conn, plant_id, on_change=self.refresh)
        run_modal(window, self)
        self.refresh(note=window.message)
        self.select_plant(plant_id)
        
        
    def select_plant(self, plant_id: int) -> None:
        """
        highlughts a plant's row and scroll to it, if the current view shows it
        """
        row = str (plant_id)
        if self.tree.exists(row):
            self.tree.selection_set(row)
            self.tree.see(row)
        
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
        return f"sorted by: {self.sort_column}{' (desc)' if self.descending else ''}"
    
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
            return f"No plant match ({', '.join(reasons)}). Click all to clear."
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