# sql_utils
# Helper functions for managing and accessing SQL database

# Import Needed Libraries
import sqlite3

def get_db_path(data_path):
    return data_path / "data.db"

def get_plot_points(data_path, controller_name):
    # Returns list of unique point names logged for this controller
    try:
        conn = sqlite3.connect(get_db_path(data_path))
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
        return []

def get_plot_data(data_path, controller_name, n_rows=300):
    # Returns recent data as { point_name: [ {t, v}, ... ] }
    try:
        conn = sqlite3.connect(get_db_path(data_path))
        cur = conn.cursor()
        cur.execute("""
            SELECT timestamp, point_name, val
            FROM point_log
            WHERE cont_name = ?
            ORDER BY id DESC
            LIMIT ?
        """, (controller_name, n_rows))
        rows = cur.fetchall()
        conn.close()

        # Group by point name
        result = {}
        for timestamp, point_name, val in reversed(rows):  # reverse so oldest first
            if point_name not in result:
                result[point_name] = []
            result[point_name].append({ "t": timestamp, "v": val })

        return result
    except Exception as e:
        return {}