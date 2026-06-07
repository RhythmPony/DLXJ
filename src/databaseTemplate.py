import logging
from sqlite3 import Connection, Cursor


def init_database_with_template(database: Connection, cursor: Cursor):
    try:
        database.execute(
            "CREATE TABLE IF NOT EXISTS A(id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE, line_name TEXT NOT NULL, line_code TEXT NOT NULL, inspection_method TEXT NOT NULL, defects_parts TEXT NOT NULL, defects_level TEXT NOT NULL, inspection_date TEXT NOT NULL, defects_type TEXT NOT NULL, defects_description TEXT NOT NULL, img_count INTEGER NOT NULL, source_image TEXT, img_path_1 TEXT, img_path_2 TEXT)")
        database.execute(
            "CREATE TABLE IF NOT EXISTS B(id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE, line_name TEXT NOT NULL, line_code TEXT NOT NULL, inspection_method TEXT NOT NULL, defects_parts TEXT NOT NULL, defects_level TEXT NOT NULL, inspection_date TEXT NOT NULL, defects_type TEXT NOT NULL, defects_description TEXT NOT NULL, img_count INTEGER NOT NULL, source_image TEXT, img_path_1 TEXT, img_path_2 TEXT)")
        database.execute(
            "CREATE TABLE IF NOT EXISTS C(id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE, line_name TEXT NOT NULL, line_code TEXT NOT NULL, inspection_method TEXT NOT NULL, defects_parts TEXT NOT NULL, defects_level TEXT NOT NULL, inspection_date TEXT NOT NULL, defects_type TEXT NOT NULL, defects_description TEXT NOT NULL, img_count INTEGER NOT NULL, source_image TEXT, img_path_1 TEXT, img_path_2 TEXT)")
        database.execute(
            "CREATE TABLE IF NOT EXISTS D(id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE, line_name TEXT NOT NULL, line_code TEXT NOT NULL, inspection_method TEXT NOT NULL, defects_parts TEXT NOT NULL, defects_level TEXT NOT NULL, inspection_date TEXT NOT NULL, defects_type TEXT NOT NULL, defects_description TEXT NOT NULL, img_count INTEGER NOT NULL, source_image TEXT, img_path_1 TEXT, img_path_2 TEXT)")
        database.commit()
    except Exception as e:
        logging.warning(str(e))
    finally:
        return database, cursor
