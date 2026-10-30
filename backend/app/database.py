import sqlite3
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from app.config import settings
from app.models import FileMetadata, SceneMetadata, QueueTask

def get_db_connection():
    conn = sqlite3.connect(settings.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Files table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS files (
        file_id TEXT PRIMARY KEY,
        file_name TEXT NOT NULL,
        file_type TEXT NOT NULL,
        storage_url TEXT NOT NULL,
        duration_seconds REAL DEFAULT 0.0,
        thumbnail_url TEXT,
        parent_folder TEXT,
        created_at TEXT,
        analyzed_at TEXT
    )
    """)
    
    # Scenes table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS scenes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_id TEXT NOT NULL,
        start_time REAL NOT NULL,
        end_time REAL NOT NULL,
        location TEXT,
        visual_description TEXT,
        tags TEXT, -- JSON string
        mood TEXT,
        pacing TEXT,
        suitability TEXT, -- JSON string
        FOREIGN KEY (file_id) REFERENCES files (file_id) ON DELETE CASCADE
    )
    """)
    
    # Queue Tasks table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS queue_tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_id TEXT UNIQUE NOT NULL,
        file_name TEXT NOT NULL,
        file_type TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'PENDING',
        error_message TEXT,
        created_at TEXT,
        updated_at TEXT
    )
    """)
    
    # App Settings key-value table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS app_settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_scenes_file_id ON scenes(file_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_queue_status ON queue_tasks(status)")
    
    conn.commit()
    conn.close()

# Database Helper Functions
def save_file_metadata(file_meta: FileMetadata):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    cursor.execute("""
    INSERT INTO files (file_id, file_name, file_type, storage_url, duration_seconds, thumbnail_url, parent_folder, created_at, analyzed_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(file_id) DO UPDATE SET
        file_name=excluded.file_name,
        file_type=excluded.file_type,
        storage_url=excluded.storage_url,
        duration_seconds=excluded.duration_seconds,
        thumbnail_url=excluded.thumbnail_url,
        parent_folder=excluded.parent_folder,
        analyzed_at=excluded.analyzed_at
    """, (
        file_meta.file_id,
        file_meta.file_name,
        file_meta.file_type,
        file_meta.storage_url,
        file_meta.duration_seconds,
        file_meta.thumbnail_url,
        file_meta.parent_folder,
        file_meta.created_at or now,
        file_meta.analyzed_at or now
    ))
    
    # Delete old scenes if re-analyzing
    cursor.execute("DELETE FROM scenes WHERE file_id = ?", (file_meta.file_id,))
    
    for scene in file_meta.scenes:
        cursor.execute("""
        INSERT INTO scenes (file_id, start_time, end_time, location, visual_description, tags, mood, pacing, suitability)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            file_meta.file_id,
            scene.start_time,
            scene.end_time,
            scene.location,
            scene.visual_description,
            json.dumps(scene.tags),
            scene.mood,
            scene.pacing,
            json.dumps(scene.suitability)
        ))
        
    conn.commit()
    conn.close()

def get_all_files(limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM files ORDER BY analyzed_at DESC LIMIT ? OFFSET ?", (limit, offset))
    rows = cursor.fetchall()
    files = []
    for r in rows:
        f = dict(r)
        cursor.execute("SELECT * FROM scenes WHERE file_id = ? ORDER BY start_time ASC", (f["file_id"],))
        scene_rows = cursor.fetchall()
        scenes = []
        for s in scene_rows:
            sd = dict(s)
            sd["tags"] = json.loads(sd["tags"]) if sd["tags"] else []
            sd["suitability"] = json.loads(sd["suitability"]) if sd["suitability"] else []
            scenes.append(sd)
        f["scenes"] = scenes
        files.append(f)
    conn.close()
    return files

def get_file_by_id(file_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM files WHERE file_id = ?", (file_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    f = dict(row)
    cursor.execute("SELECT * FROM scenes WHERE file_id = ? ORDER BY start_time ASC", (file_id,))
    scene_rows = cursor.fetchall()
    scenes = []
    for s in scene_rows:
        sd = dict(s)
        sd["tags"] = json.loads(sd["tags"]) if sd["tags"] else []
        sd["suitability"] = json.loads(sd["suitability"]) if sd["suitability"] else []
        scenes.append(sd)
    f["scenes"] = scenes
    conn.close()
    return f

def get_all_scenes() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT s.*, f.file_name, f.storage_url, f.file_type 
    FROM scenes s
    JOIN files f ON s.file_id = f.file_id
    ORDER BY s.id ASC
    """)
    rows = cursor.fetchall()
    scenes = []
    for r in rows:
        sd = dict(r)
        sd["tags"] = json.loads(sd["tags"]) if sd["tags"] else []
        sd["suitability"] = json.loads(sd["suitability"]) if sd["suitability"] else []
        scenes.append(sd)
    conn.close()
    return scenes

# Queue Operations
def enqueue_file(file_id: str, file_name: str, file_type: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute("""
    INSERT INTO queue_tasks (file_id, file_name, file_type, status, created_at, updated_at)
    VALUES (?, ?, ?, 'PENDING', ?, ?)
    ON CONFLICT(file_id) DO UPDATE SET
        file_name=excluded.file_name,
        file_type=excluded.file_type,
        updated_at=excluded.updated_at
    """, (file_id, file_name, file_type, now, now))
    conn.commit()
    conn.close()

def update_queue_status(file_id: str, status: str, error_message: Optional[str] = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute("""
    UPDATE queue_tasks 
    SET status = ?, error_message = ?, updated_at = ?
    WHERE file_id = ?
    """, (status, error_message, now, file_id))
    conn.commit()
    conn.close()

def get_pending_tasks(limit: int = 10) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM queue_tasks WHERE status = 'PENDING' ORDER BY id ASC LIMIT ?", (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_all_queue_tasks() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM queue_tasks ORDER BY id DESC LIMIT 100")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

# Settings Store
def get_setting(key: str, default: Optional[str] = None) -> Optional[str]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM app_settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row["value"] if row else default

def set_setting(key: str, value: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO app_settings (key, value) VALUES (?, ?)
    ON CONFLICT(key) DO UPDATE SET value = excluded.value
    """, (key, value))
    conn.commit()
    conn.close()

def get_all_settings() -> Dict[str, str]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM app_settings")
    rows = cursor.fetchall()
    conn.close()
    return {r["key"]: r["value"] for r in rows}
