# sql_utils
# Helper functions for managing and accessing SQL database

# Import Needed Libraries
import sqlite3

def get_db_path(data_path):
    return data_path / "data.db"

_read_conn = {}
def _get_read_conn(data_path):
    key = str(data_path)
    if key not in _read_conn:
        conn = sqlite3.connect(str(get_db_path(data_path)), check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA read_uncommitted=1")
        _read_conn[key] = conn
    return _read_conn[key]

def get_plot_points(data_path, controller_name):
    # Returns list of unique point names logged for this controller
    try:
        conn = _get_read_conn(data_path)
        cur = conn.cursor()
        conn.execute("BEGIN")
        cur.execute("""
            SELECT DISTINCT point_name 
            FROM point_log 
            WHERE cont_name = ?
            ORDER BY point_name
        """, (controller_name,))
        conn.execute("ROLLBACK")
        points = [row[0] for row in cur.fetchall()]
        conn.close()
        return points
    except Exception as e:
        print(f"[sql_utils] get_plot_points error: {e}")
        return []

def get_plot_data(data_path, controller_name, window_sec=60):
    """
    Returns data for every logged point within the last window_sec seconds.
    Result: { point_name: [ {"t": "YYYY-MM-DD HH:MM:SS", "v": "value"}, ... ] }
    Ordered oldest-first within each point so the frontend can append directly.
    Uses a per-point subquery so no point starves another of rows.
    """
    try:
        conn = _get_read_conn(data_path)
        cur = conn.cursor()
        conn.execute("BEGIN")
        cur.execute("""
            SELECT timestamp, point_name, val
            FROM point_log
            WHERE cont_name = ?
              AND timestamp >= datetime('now', 'localtime', ? || ' seconds')
            ORDER BY id ASC
        """, (controller_name, f'-{int(window_sec)}'))
        conn.execute("ROLLBACK")
        rows = cur.fetchall()
        conn.close()

        result = {}
        for timestamp, point_name, val in rows:
            if point_name not in result:
                result[point_name] = []
            result[point_name].append({"t": timestamp, "v": val})
        return result
    except Exception as e:
        print(f"[sql_utils] get_plot_data error: {e}")
        return {}

def get_plot_data_range(data_path, controller_name, from_timestamp, to_timestamp):
    """
    Returns all rows between from_timestamp and to_timestamp inclusive.
    Both timestamps must be SQLite format: "YYYY-MM-DD HH:MM:SS"
    """
    try:
        conn = _get_read_conn(data_path)
        cur = conn.cursor()
        conn.execute("BEGIN")
        cur.execute("""
            SELECT timestamp, point_name, val
            FROM point_log
            WHERE cont_name = ?
              AND timestamp >= ?
              AND timestamp <= ?
            ORDER BY id ASC
        """, (controller_name, from_timestamp, to_timestamp))
        conn.execute("ROLLBACK")
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

def get_plot_data_since(data_path, controller_name, since_timestamp):
    """
    Returns all rows strictly newer than since_timestamp for this controller.
    since_timestamp: "YYYY-MM-DD HH:MM:SS" (SQLite format).
    Used by the live-poll incremental update — no row cap, no missed data.
    """
    try:
        conn = _get_read_conn(data_path)
        cur = conn.cursor()
        conn.execute("BEGIN")
        cur.execute("""
            SELECT timestamp, point_name, val
            FROM point_log
            WHERE cont_name = ?
              AND timestamp > ?
            ORDER BY id ASC
        """, (controller_name, since_timestamp))
        conn.execute("ROLLBACK")
        rows = cur.fetchall()
        conn.close()

        result = {}
        for timestamp, point_name, val in rows:
            if point_name not in result:
                result[point_name] = []
            result[point_name].append({"t": timestamp, "v": val})
        return result
    except Exception as e:
        print(f"[sql_utils] get_plot_data_since error: {e}")
        return {}