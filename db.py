"""
==================================================================
 DB.PY
 MySQL database helper. Users + History (badha tools ni history
 ek j table ma, tool column thi alag padे che).

 MySQL connection details .env file mathi aave che (jo .env
 file na hoy, to config.py na defaults vaparay - localhost,
 root user, khali password, database name "mytools_db".
 Aa XAMPP / local MySQL setup mate default che).

 IMPORTANT: MySQL server chalu hovo jarrori che. init_db()
 function database + tables automatically banavi de che
 (CREATE DATABASE IF NOT EXISTS), pan MySQL server run
 thayelu hovu jarrori che - README.md ma pagla che.
==================================================================
"""

import pymysql
import pymysql.cursors
from datetime import datetime, timezone

from config import Config


def get_connection(with_db=True):
    """
    Open a new MySQL connection. Returns rows as dictionaries
    (so existing code like row["email"] keeps working exactly
    like it did with sqlite3.Row).
    """
    return pymysql.connect(
    host=Config.MYSQL_HOST,
    port=Config.MYSQL_PORT,
    user=Config.MYSQL_USER,
    password=Config.MYSQL_PASSWORD,
    database=Config.MYSQL_DATABASE if with_db else None,
    charset="utf8mb4",
    cursorclass=pymysql.cursors.DictCursor,
    autocommit=False,
    ssl={"ssl": {}}
)


def init_db():
    """
    Creates the database (if missing) and both tables
    (if missing). Safe to call every time the app starts.
    """

    # Step 1: make sure the database itself exists.
    conn = get_connection(with_db=False)
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{Config.MYSQL_DATABASE}` "
                f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        conn.commit()
    finally:
        conn.close()

    # Step 2: create tables inside that database.
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    first_name VARCHAR(100) NOT NULL,
                    last_name VARCHAR(100) NOT NULL,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    is_verified TINYINT(1) NOT NULL DEFAULT 0,
                    profile_image VARCHAR(255),
                    created_at VARCHAR(64) NOT NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS history (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    tool VARCHAR(50) NOT NULL,
                    operation VARCHAR(100) NOT NULL,
                    original_filename VARCHAR(255),
                    processed_filename VARCHAR(255) NOT NULL,
                    file_size INT,
                    batch_id VARCHAR(64),
                    created_at VARCHAR(64) NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
        conn.commit()
    finally:
        conn.close()


def _now():
    return datetime.now(timezone.utc).isoformat()


# =========================================================
# USERS
# =========================================================

def create_user(first_name, last_name, email, password_hash):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (first_name, last_name, email, password_hash, is_verified, created_at)
                VALUES (%s, %s, %s, %s, 0, %s)
                """,
                (first_name, last_name, email.lower().strip(), password_hash, _now())
            )
            conn.commit()
            return cur.lastrowid
    finally:
        conn.close()


def get_user_by_email(email):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM users WHERE email = %s", (email.lower().strip(),)
            )
            return cur.fetchone()
    finally:
        conn.close()


def get_user_by_id(user_id):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            return cur.fetchone()
    finally:
        conn.close()


def mark_user_verified(user_id):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET is_verified = 1 WHERE id = %s", (user_id,)
            )
        conn.commit()
    finally:
        conn.close()


def update_user_password(user_id, new_password_hash):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET password_hash = %s WHERE id = %s",
                (new_password_hash, user_id)
            )
        conn.commit()
    finally:
        conn.close()


def update_profile_image(user_id, filename):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET profile_image = %s WHERE id = %s",
                (filename, user_id)
            )
        conn.commit()
    finally:
        conn.close()


def update_profile_names(user_id, first_name, last_name):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET first_name = %s, last_name = %s WHERE id = %s",
                (first_name, last_name, user_id)
            )
        conn.commit()
    finally:
        conn.close()


# =========================================================
# HISTORY
# =========================================================

def add_history(user_id, tool, operation, processed_filename,
                 original_filename=None, file_size=None, batch_id=None):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO history
                    (user_id, tool, operation, original_filename,
                     processed_filename, file_size, batch_id, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (user_id, tool, operation, original_filename,
                 processed_filename, file_size, batch_id, _now())
            )
            conn.commit()
            return cur.lastrowid
    finally:
        conn.close()


def get_history_for_user(user_id):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM history WHERE user_id = %s ORDER BY id DESC",
                (user_id,)
            )
            return cur.fetchall()
    finally:
        conn.close()


def get_history_record(record_id, user_id):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM history WHERE id = %s AND user_id = %s",
                (record_id, user_id)
            )
            return cur.fetchone()
    finally:
        conn.close()


def get_history_by_batch(batch_id, user_id):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM history WHERE batch_id = %s AND user_id = %s ORDER BY id ASC",
                (batch_id, user_id)
            )
            return cur.fetchall()
    finally:
        conn.close()


def delete_history_record(record_id, user_id):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM history WHERE id = %s AND user_id = %s",
                (record_id, user_id)
            )
        conn.commit()
    finally:
        conn.close()


def clear_history_for_user(user_id):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM history WHERE user_id = %s", (user_id,)
            )
        conn.commit()
    finally:
        conn.close()
