# sql_thread
# This software thread asynchronously manages the SQL database

# Import Needed Libraries
import sqlite3
import queue
import threading
import pathlib
import datetime
import time

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
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_point_log_lookup
        ON point_log (cont_name, timestamp)
    """)
    conn.commit()
    return conn

def sql_worker(data_path, sql_queue):
    conn = init_sql(data_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=OFF")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA cache_size=10000")
    last_commit = time.time()
    pending = 0

    while True:
        # Block until at least one entry arrives
        try:
            entry = sql_queue.get(timeout=0.05)
        except queue.Empty:
            continue

        # Drain everything else currently queued
        batch = [entry]
        while True:
            try:
                batch.append(sql_queue.get_nowait())
            except queue.Empty:
                break

        now = time.time()
        conn.executemany(
            "INSERT INTO point_log (port, cont_name, point_name, val, timestamp) VALUES (?, ?, ?, ?, ?)",
            [(e["port"], e["cont_name"], e["point_name"], e["val"],
              datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")) for e in batch]
        )
        if now - last_commit >= 0.05:
            conn.commit()
            last_commit = now
