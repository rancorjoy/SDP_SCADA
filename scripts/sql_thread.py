# sql_thread
# This software thread asynchronously manages the SQL database

# Import Needed Libraries
import sqlite3
import queue
import threading
import pathlib

def init_sql(data_path):
    conn = sqlite3.connect(pathlib.Path(data_path) / "data.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS point_log (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            port        TEXT,
            cont_name   Text,
            point_name  TEXT,
            val         TEXT
        )
    """)
    conn.commit()
    return conn

def sql_worker(data_path, sql_queue):
    conn = init_sql(data_path)
    while True:
        entry = sql_queue.get()
        conn.execute(
            "INSERT INTO point_log (port, cont_name, point_name, val) VALUES (?, ?, ?, ?)",
            (entry["port"], entry["cont_name"], entry["point_name"], entry["val"])
        )
        conn.commit()
