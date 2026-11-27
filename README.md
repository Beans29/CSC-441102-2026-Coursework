# CSC-441102-2026-Coursework
By 23008858 / X9J77
# Plant Water Monitor

A plant care tracker written in python for CSC-44102. It keeps a list of your plants, remembers when each one was last watered, and shows which ones need watering today. there are two wats to use it: a CLI text version and window GUI version built with Tkinter. both working from the same database.

# Features:

* Add, edit and remove plants (name, type, location, watering intervals and age)
* Record waterings, today or back dating, and keeps a full history of every individual plant
* Every plant is in one of four states, indicated by a colour
      * Overdue (Red): The watering due date has passed
      * Due Today (Amber)
      * Pending (Blue): No watering data, so there is no due date
      * Upcoming (no colour): Not due yet

* Sort by any column, search by name, filter by location, or show only the plants that need attention today (ranked by how overdue they are)
* Location summary with plants, due today and overdue for each location
* Import & Export from a JSON file: includes every piece of data about the plant (name, type, location, watering intervals, age and due date)
* Plants are stored in a SQLite database, so they are non-volatile and there next time the app is opened

# Requirements:

* Python 3.10 or newer
* No external packages to install. the app only uses Python standard libraries
* The GUI version required Tkinter. Will need to be installed if using homebrew python install it with
      'brew install python-tk@3.14'

# Running it:

Python 3 gui.py or Python3 cli.py 
Depending on what version you want to use

On first run of either version, a plants.db file is created next to core.py.
To clear the database you can delete the file and re-run the app to generate a new empty database

# Sample Data:

Included in the repository is a sample_plants.json file.
this can be imported in to the app to give you a database of 50 plants in various locations and varying water dates

To import:

gui.py - click the 'import' button, and select the sample file, and click yes

cli.py - type 'import sample_plants.json and then type yes to confirm

# Using the gui Version

| Control | What it does |
| --- | --- |
| Find box | Shows only plants whose name matches what you typed |
| Locations dropdown | Shows only the plants in one location |
| Today | Shows plants that need attention, most overdue first |
| All | Clears the search, the location and the Today view |
| Column headings | Click to sort by that column; click again to reverse |
| Add Plant | Opens the form for a new plant |
| Open (or double-click a row) | Opens a plant's details: water it, edit it, remove it, and see its history |
| Locations | Opens the summary for each location |
| Import / Export | Loads plants from a JSON file, or saves them all to one |
| Refresh | Redraws the table |

# Using the text version

| Command | What it does |
| --- | --- |
| `add` | Asks for the details of a new plant |
| `<number>` | Opens that plant's details screen (for example `3`) |
| `water <number> [date]` | Records a watering, today by default; dates are DD/MM/YYYY |
| `sort <column> [desc]` | Sorts by `id`, `name`, `age`, `type`, `location`, `last` or `next` |
| `find <text>` | Shows plants whose name matches |
| `location <name>` | Shows only one location |
| `locations` | Shows the summary for each location |
| `today` | Shows plants that need attention, most overdue first |
| `all` | Clears the search, location and today views |
| `import <file>` | Checks a JSON file, then adds its plants after you type `yes` |
| `export <file>` | Writes every plant and its history to a JSON file |
| `quit` | Leaves the program |

# Import File Format

An import file is a JSON with a plants list. Dates are written in DD/MM/YYYY, and waterings can be empty:

```json
{
  "plants": [
    {
      "name": "Bonsai",
      "type": "Tree",
      "location": "Living room",
      "interval_days": 3,
      "acquired": "12/11/2020",
      "waterings": ["01/11/2026", "04/11/2026", "07/11/2026"]
    }
  ]
}
```
The whole file is checked before anything is saved to the database. if any plant has a problem, nothing is imported and every problem is listed.
Exported files use the same format, so an export can be imported again

Limits: 
- Names can only be up to 20 characters
- Types and locations can be up to 12 characters
- Watering values must be between 1 - 365 days

# File Organisation

| File | What it does |
| --- | --- |
| `core.py` | All the rules, calculations and database code |
| `cli.py` | The text version: reads input and prints, nothing else |
| `gui.py` | The window version: shows what `core.py` gives it |
| `tests/` | Automated tests for `core.py` |
| `sample_plants.json` | 50 sample plants to try the import with |
| `plants.db` | The database, created the first time you run the app |

core.py never prints, asks the user anything or reads the clock, the caller passes in today's date. allowing the cli and gui version to share the same rules.
