# Game-Sales-Explorer
Game Sales Explorer is a Python desktop application built with PyQt6 and SQLite that allows users to query, filter, sort, and analyze video game sales data through an interactive graphical interface.

## How to Launch

1. Download or clone this project to your computer.

2. Install the required dependencies:

```bash
pip install PyQt6 pandas
```

3. Run the application:

```bash
python main.py
```

### Requirements
- Python 3.10+
- PyQt6
- pandas
SQLite is included through Python's built-in sqlite3 module and does not require a separate installation.

### Required Files
Make sure these files are included in the project folder:

- main.py  
- sqlGames.py  
- vgsales.csv  

The SQLite database (`games.db`) will be created automatically on first launch if it does not already exist.