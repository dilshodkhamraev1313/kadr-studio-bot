import sqlite3
from contextlib import contextmanager

DB_PATH = "bookings.db"


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room TEXT NOT NULL,
                booking_date TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                tg_user_id INTEGER NOT NULL,
                tg_username TEXT,
                tg_fullname TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                receipt_file_id TEXT,
                group_chat_id INTEGER,
                group_message_id INTEGER,
                admin_name TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.commit()


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def _overlaps(a_start, a_end, b_start, b_end):
    return a_start < b_end and b_start < a_end


def find_conflicts(room: str, booking_date: str, start_time: str, end_time: str):
    """Return active (pending/confirmed) bookings for the same room/date that overlap the given range."""
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT * FROM bookings
               WHERE room = ? AND booking_date = ? AND status IN ('pending', 'confirmed')""",
            (room, booking_date),
        ).fetchall()
    return [r for r in rows if _overlaps(start_time, end_time, r["start_time"], r["end_time"])]


def list_busy_ranges(room: str, booking_date: str):
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT start_time, end_time FROM bookings
               WHERE room = ? AND booking_date = ? AND status IN ('pending', 'confirmed')
               ORDER BY start_time""",
            (room, booking_date),
        ).fetchall()
    return [(r["start_time"], r["end_time"]) for r in rows]


def create_booking(room, booking_date, start_time, end_time, tg_user_id, tg_username, tg_fullname):
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO bookings (room, booking_date, start_time, end_time, tg_user_id, tg_username, tg_fullname)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (room, booking_date, start_time, end_time, tg_user_id, tg_username, tg_fullname),
        )
        conn.commit()
        return cur.lastrowid


def attach_receipt(booking_id, receipt_file_id, group_chat_id, group_message_id):
    with get_conn() as conn:
        conn.execute(
            """UPDATE bookings SET receipt_file_id = ?, group_chat_id = ?, group_message_id = ?
               WHERE id = ?""",
            (receipt_file_id, group_chat_id, group_message_id, booking_id),
        )
        conn.commit()


def get_booking(booking_id):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,)).fetchone()
    return row


def set_status(booking_id, status, admin_name=None):
    with get_conn() as conn:
        conn.execute(
            "UPDATE bookings SET status = ?, admin_name = ? WHERE id = ?",
            (status, admin_name, booking_id),
        )
        conn.commit()
