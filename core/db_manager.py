import sqlite3
import os
import time
from utils.logger import get_logger

logger = get_logger(__name__)

class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        """Database Table မရှိသေးပါက ဆောက်ပေးခြင်း"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        url TEXT NOT NULL UNIQUE,
                        title TEXT,
                        uploader TEXT,
                        duration INTEGER,
                        status TEXT DEFAULT 'Fetched',
                        file_path TEXT,
                        error_msg TEXT,
                        created_at INTEGER,
                        updated_at INTEGER
                    )
                """)
                conn.commit()
                logger.info("Database initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")

    def save_or_update_fetch(self, url: str, info: dict):
        """Fetch Info ပြီးသွားချိန်တွင် URL နှင့် Data သိမ်းဆည်းခြင်း"""
        try:
            title = info.get("fulltitle") or info.get("title", "Unknown Title")
            uploader = info.get("uploader") or info.get("channel", "Unknown")
            duration = info.get("duration", 0)
            now = int(time.time())

            with self.get_connection() as conn:
                cursor = conn.cursor()
                # URL ရှိပြီးသားဖြစ်ပါက Data များကို Update လုပ်မည်၊ မရှိပါက အသစ်ထည့်မည်
                cursor.execute("""
                    INSERT INTO history (url, title, uploader, duration, status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, 'Fetched', ?, ?)
                    ON CONFLICT(url) DO UPDATE SET
                        title=excluded.title,
                        uploader=excluded.uploader,
                        duration=excluded.duration,
                        status='Fetched',
                        updated_at=excluded.updated_at
                """, (url, title, uploader, duration, now, now))
                conn.commit()
                logger.info(f"DB: Fetch info saved/updated for URL: {url}")
        except Exception as e:
            logger.error(f"DB: Error saving fetch info: {e}")

    def update_download_status(self, url: str, status: str, file_path: str = "", error_msg: str = ""):
        """Download Success / Error / Cancelled ဖြစ်သွားချိန်တွင် Status Update ပြုလုပ်ခြင်း"""
        try:
            now = int(time.time())
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE history 
                    SET status = ?, 
                        file_path = ?, 
                        error_msg = ?, 
                        updated_at = ?
                    WHERE url = ?
                """, (status, file_path, error_msg, now, url))
                
                # အကယ်၍ Fetch မလုပ်ဘဲ Direct Download ဆွဲ၍ Database ထဲ URL မရှိသေးပါက
                if cursor.rowcount == 0:
                    cursor.execute("""
                        INSERT INTO history (url, status, file_path, error_msg, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (url, status, file_path, error_msg, now, now))

                conn.commit()
                logger.info(f"DB: Download status updated to '{status}' for URL: {url}")
        except Exception as e:
            logger.error(f"DB: Error updating download status: {e}")

    def get_all_history(self):
        """History စာရင်းအပြည့်အစုံ ရယူရန် (UI မှာ ပြသရန်)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT url, title, status FROM history ORDER BY updated_at DESC")
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"DB: Error fetching history: {e}")
            return []

    def delete_history_by_url(self, url: str):
        """URL တစ်ခုချင်းစီကို Database မှ ဖျက်ခြင်း"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM history WHERE url = ?", (url,))
                conn.commit()
                logger.info(f"DB: Deleted history item for URL: {url}")
        except Exception as e:
            logger.error(f"DB: Error deleting item: {e}")

    def clear_all_history(self):
        """History အားလုံးကို Database မှ ဖျက်ခြင်း"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM history")
                conn.commit()
                logger.info("DB: Cleared all history.")
        except Exception as e:
            logger.error(f"DB: Error clearing history: {e}")