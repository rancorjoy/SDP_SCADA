# sql_utils
# Helper functions for managing and accessing SQL database

# Import Needed Libraries
import sqlite3
import pathlib

def get_db_path(data_path):
    return data_path / "data.db"

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

def _get_read_conn(data_path):
    conn = sqlite3.connect(str(get_db_path(data_path)), check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def get_plot_points(data_path, controller_name):
    # Returns list of unique point names logged for this controller
    try:
        conn = _get_read_conn(data_path)
        cur = conn.cursor()
        cur.execute("""
            SELECT DISTINCT point_name 
            FROM point_log 
            WHERE cont_name = ?
            ORDER BY point_name
        """, (controller_name,))
        points = [row[0] for row in cur.fetchall()]
        conn.close()
        return points
    except Exception as e:
        print(f"[sql_utils] get_plot_points error: {e}")
        return []

def get_plot_data(data_path, controller_name, window_sec=60):
    try:
        conn = _get_read_conn(data_path)
        cur = conn.cursor()
        cur.execute("""
            SELECT id, timestamp, point_name, val
            FROM point_log
            WHERE cont_name = ?
              AND timestamp >= datetime('now', 'localtime', ? || ' seconds')
            ORDER BY id ASC
        """, (controller_name, f'-{int(window_sec)}'))
        rows = cur.fetchall()

        result = {}
        last_id = 0
        for row_id, timestamp, point_name, val in rows:
            if point_name not in result:
                result[point_name] = []
            result[point_name].append({"t": timestamp, "v": val})
            if row_id > last_id:
                last_id = row_id

        # If window returned no rows, still get the global max id
        # so we don't re-fetch old data on the next poll
        if last_id == 0:
            cur.execute("SELECT MAX(id) FROM point_log WHERE cont_name = ?", (controller_name,))
            row = cur.fetchone()
            last_id = row[0] or 0

        conn.close()
        return {"data": result, "last_id": last_id}
    except Exception as e:
        print(f"[sql_utils] get_plot_data error: {e}")
        return {"data": {}, "last_id": 0}

def get_plot_data_range(data_path, controller_name, from_timestamp, to_timestamp):
    """
    Returns all rows between from_timestamp and to_timestamp inclusive.
    Both timestamps must be SQLite format: "YYYY-MM-DD HH:MM:SS"
    """
    try:
        conn = _get_read_conn(data_path)
        cur = conn.cursor()
        cur.execute("""
            SELECT timestamp, point_name, val
            FROM point_log
            WHERE cont_name = ?
              AND timestamp >= ?
              AND timestamp <= ?
            ORDER BY id ASC
        """, (controller_name, from_timestamp, to_timestamp))
        rows = cur.fetchall()
        conn.close()

        result = {}
        for timestamp, point_name, val in rows:
            if point_name not in result:
                result[point_name] = []
            result[point_name].append({"t": timestamp, "v": val})
        return result
    except Exception as e:
        print(f"[sql_utils] get_plot_data_range error: {e}")
        return {}

def get_plot_data_since(data_path, controller_name, since_id):
    try:
        conn = _get_read_conn(data_path)
        cur = conn.cursor()
        cur.execute("""
            SELECT id, timestamp, point_name, val
            FROM point_log
            WHERE cont_name = ?
              AND id > ?
            ORDER BY id ASC
        """, (controller_name, int(since_id)))
        rows = cur.fetchall()
        conn.close()

        result = {}
        last_id = int(since_id)
        for row_id, timestamp, point_name, val in rows:
            if point_name not in result:
                result[point_name] = []
            result[point_name].append({"t": timestamp, "v": val})
            if row_id > last_id:
                last_id = row_id
        return {"data": result, "last_id": last_id}
    except Exception as e:
        print(f"[sql_utils] get_plot_data_since error: {e}")
        return {"data": {}, "last_id": since_id}