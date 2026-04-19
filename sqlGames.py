import os
import sqlite3
import pandas as pd

DB_FILE = "games.db"
CSV_FILE = "vgsales.csv"


def initialize_database():
    """
    Ensures the database exists.
    If not, creates it from the CSV file.
    """
    if not os.path.exists(DB_FILE):
        print("Database not found. Creating from CSV...")
        create_database_from_csv()
    else:
        print("Database already exists.")

DB_FILE = "games.db"
CSV_FILE = "vgsales.csv"


def create_database_from_csv():
    #Read CSV File
    df = pd.read_csv(CSV_FILE)

    #Create Database
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("PRAGMA foreign_keys = ON")

    #Rename Columns as SQL does not like capital letters
    df = df.rename(columns={
        "Rank": "rank",
        "Name": "name",
        "Platform": "platform",
        "Year": "year",
        "Genre": "genre",
        "Publisher": "publisher",
        "NA_Sales": "na_sales",
        "EU_Sales": "eu_sales",
        "JP_Sales": "jp_sales",
        "Other_Sales": "other_sales",
        "Global_Sales": "global_sales"
    })

    #Replace NaN with None
    df = df.where(pd.notnull(df), None)
    df["year"] = df["year"].apply(lambda x: int(x) if pd.notnull(x) else None)

    #Drop Tables if they exist
    cursor.execute("DROP TABLE IF EXISTS game_sales")
    cursor.execute("DROP TABLE IF EXISTS games")
    cursor.execute("DROP TABLE IF EXISTS publishers")
    cursor.execute("DROP TABLE IF EXISTS genres")
    cursor.execute("DROP TABLE IF EXISTS platforms")

    #Create Tables
    cursor.execute("""
        CREATE TABLE publishers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    """)

    cursor.execute("""
        CREATE TABLE genres (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    """)

    cursor.execute("""
        CREATE TABLE platforms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    """)

    cursor.execute("""
        CREATE TABLE games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rank INTEGER,
            name TEXT NOT NULL,
            year INTEGER,
            publisher TEXT,
            genre TEXT,
            platform TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE game_sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id INTEGER NOT NULL,
            na_sales REAL,
            eu_sales REAL,
            jp_sales REAL,
            other_sales REAL,
            global_sales REAL,
            FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE
        )
    """)

    #Insert Publishers

    unique_publishers = sorted([p for p in df["publisher"].dropna().unique()])
    cursor.executemany(
        "INSERT INTO publishers (name) VALUES (?)",
        [(publisher,) for publisher in unique_publishers]
    )

    #Insert Genres
    unique_genres = sorted([g for g in df["genre"].dropna().unique()])
    cursor.executemany(
        "INSERT INTO genres (name) VALUES (?)",
        [(genre,) for genre in unique_genres]
    )

    #Insert Platforms
    unique_platforms = sorted([p for p in df["platform"].dropna().unique()])
    cursor.executemany(
        "INSERT INTO platforms (name) VALUES (?)",
        [(platform,) for platform in unique_platforms]
    )

    #Insert Games
    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO games (rank, name, year, publisher, genre, platform)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            row["rank"],
            row["name"],
            row["year"],
            row["publisher"],
            row["genre"],
            row["platform"]
        ))

        game_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO game_sales (
                game_id, na_sales, eu_sales, jp_sales, other_sales, global_sales
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            game_id,
            row["na_sales"],
            row["eu_sales"],
            row["jp_sales"],
            row["other_sales"],
            row["global_sales"]
        ))

    conn.commit()
    conn.close()


def get_connection():
    """
    Returns a connection to the database (after ensuring it exists)
    """
    initialize_database()
    return sqlite3.connect(DB_FILE)


#Database Searches

def get_genres():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM genres")
    names = [row[0] for row in cursor.fetchall()]
    conn.close()
    return ["--None--"] + names

def get_publishers():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM publishers")
    names = [row[0] for row in cursor.fetchall()]
    conn.close()
    return ["--None--"] + names

def get_platforms():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM platforms")
    names = [row[0] for row in cursor.fetchall()]
    conn.close()
    return ["--None--"] + names

def run_query(limit, title, genre, publisher, platform):
    query = """
        SELECT
            g.rank,
            g.name,
            g.platform,
            g.year,
            g.publisher,
            g.genre,
            s.na_sales,
            s.eu_sales,
            s.jp_sales,
            s.other_sales,
            s.global_sales
        FROM games g
        JOIN game_sales s ON g.id = s.game_id
    """

    filters = []
    params = []

    if title != "":
        filters.append("g.name LIKE ?")
        params.append(f"%{title}%")

    if genre != "--None--":
        filters.append("g.genre = ?")
        params.append(genre)

    if publisher != "--None--":
        filters.append("g.publisher = ?")
        params.append(publisher)

    if platform != "--None--":
        filters.append("g.platform = ?")
        params.append(platform)

    if filters:
        query += " WHERE " + " AND ".join(filters)

    query += " LIMIT ?"
    params.append(limit)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()

    return results
