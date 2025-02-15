import sqlite3
import datetime

def create_database(db_name="aiclipcreator.db"):
    """Creates the aiclipcreator database with videos and clips tables."""

    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    try:
        # Create videos table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                id TEXT PRIMARY KEY,
                name TEXT,
                created_at TEXT,  -- Store as ISO 8601 string for datetime
                transcript TEXT
            )
        """)

        # Create clips table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT,
                start_time INTEGER,
                end_time INTEGER,
                clip_transcript TEXT,
                post_tiktok TEXT, -- Store as ISO 8601 string for datetime or NULL
                tiktok_url TEXT,
                post_instagram TEXT, -- Store as ISO 8601 string for datetime or NULL
                instagram_url TEXT,
                post_youtube TEXT, -- Store as ISO 8601 string for datetime or NULL
                youtube_url TEXT,
                FOREIGN KEY (video_id) REFERENCES videos(id)
            )
        """)

        conn.commit()
        print(f"Database '{db_name}' created successfully.")

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        conn.rollback()  # Rollback changes in case of error

    finally:
        conn.close()


def insert_video(video_id, name, transcript):
    """Inserts a new video into the videos table."""
    db_name = "aiclipcreator.db"
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    try:
        created_at = datetime.datetime.now().isoformat()  # ISO 8601 format
        cursor.execute("INSERT INTO videos (id, name, created_at, transcript) VALUES (?, ?, ?, ?)",
                       (video_id, name, created_at, transcript))
        conn.commit()
        print(f"Video '{name}' inserted successfully.")

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        conn.rollback()

    finally:
        conn.close()



def insert_clip(video_id, start_time, end_time, clip_transcript, tiktok_url=None, instagram_url=None, youtube_url=None):
        """Inserts a new clip into the clips table."""

        db_name = "aiclipcreator.db"
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO clips (video_id, start_time, end_time, clip_transcript, tiktok_url, instagram_url, youtube_url)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (video_id, start_time, end_time, clip_transcript, tiktok_url, instagram_url, youtube_url))

            conn.commit()
            print(f"Clip for video '{video_id}' inserted successfully.")

        except sqlite3.Error as e:
            print(f"An error occurred: {e}")
            conn.rollback()

        finally:
            conn.close()



# Example usage:
# create_database()  # Creates the database if it doesn't exist

# insert_video("video_123", "My First Video", "This is the transcript of my first video.")
# insert_clip("video_123", 10, 20, "This is the first clip.", tiktok_url="tiktok.com/clip1")
# insert_clip("video_123", 30, 40, "This is the second clip.", instagram_url="instagram.com/clip2")