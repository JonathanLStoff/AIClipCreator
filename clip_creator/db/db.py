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
                updated_at TEXT, -- Store as ISO 8601 string for datetime
                uploaded_at TEXT, -- Store as ISO 8601 string for datetime
                transcript TEXT,
                one_word_most_used TEXT,
                one_word_count INTEGER,
                two_word_most_used TEXT,
                two_word_count INTEGER,
                three_word_most_used TEXT,
                three_word_count INTEGER,
                views INTEGER,
                likes INTEGER,
                top_yt_comment TEXT,
                top_reddit_comment TEXT,
                reddit_url TEXT,
                video_creator TEXT
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

def add_video_entry(video_data, db_name="aiclipcreator.db"):
    """Adds a new video entry to the database.

    Args:
        db_name: The name of the database file.
        video_data: A dictionary containing the video data:
            {
                "id": (str, primary key),  # MUST be unique
                "name": (str),
                "transcript": (str),
                "one_word_most_used": (str),
                "one_word_count": (int),
                "two_word_most_used": (str),
                "two_word_count": (int),
                "three_word_most_used": (str),
                "three_word_count": (int),
                "views": (int),
                "likes": (int),
                "top_yt_comment": (str),
                "top_reddit_comment": (str),
                "reddit_url": (str),
                "video_creator": (str),
            }

    Returns:
        True if the video entry was added successfully, False otherwise.
    """

    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        # Get current datetime in ISO 8601 format
        now = datetime.datetime.now(datetime.timezone.utc)

        # Ensure all required keys are present (you might want more thorough validation)
        required_keys = ["id", "name", "transcript", "one_word_most_used", "one_word_count", "two_word_most_used", "two_word_count", "three_word_most_used", "three_word_count", "views", "likes", "top_yt_comment", "top_reddit_comment", "reddit_url", "video_creator"]
        if not all(key in video_data for key in required_keys):
            raise ValueError("Missing required keys in video_data")

        # Check if the video id already exists
        cursor.execute("SELECT 1 FROM videos WHERE id = ?", (video_data["id"],))
        exists = cursor.fetchone()

        if exists:
            # Update the existing video entry (keeping created_at unchanged)
            cursor.execute("""
                UPDATE videos
                SET name = ?, updated_at = ?, transcript = ?, one_word_most_used = ?, one_word_count = ?,
                    two_word_most_used = ?, two_word_count = ?, three_word_most_used = ?, three_word_count = ?,
                    views = ?, likes = ?, top_yt_comment = ?, top_reddit_comment = ?, reddit_url = ?, video_creator = ?
                WHERE id = ?
            """, (
                video_data["name"],
                now,  # updated_at
                video_data["transcript"],
                video_data["one_word_most_used"],
                video_data["one_word_count"],
                video_data["two_word_most_used"],
                video_data["two_word_count"],
                video_data["three_word_most_used"],
                video_data["three_word_count"],
                video_data["views"],
                video_data["likes"],
                video_data["top_yt_comment"],
                video_data["top_reddit_comment"],
                video_data["reddit_url"],
                video_data["video_creator"],
                video_data["id"],
            ))
        else:
            # Insert new video entry
            cursor.execute("""
                INSERT INTO videos (id, name, created_at, updated_at, uploaded_at, transcript, one_word_most_used, one_word_count, two_word_most_used, two_word_count, three_word_most_used, three_word_count, views, likes, top_yt_comment, top_reddit_comment, reddit_url, video_creator)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                video_data["id"],
                video_data["name"],
                now,  # created_at
                now,  # updated_at (initially same as created_at)
                None, # uploaded_at (can be set later)
                video_data["transcript"],
                video_data["one_word_most_used"],
                video_data["one_word_count"],
                video_data["two_word_most_used"],
                video_data["two_word_count"],
                video_data["three_word_most_used"],
                video_data["three_word_count"],
                video_data["views"],
                video_data["likes"],
                video_data["top_yt_comment"],
                video_data["top_reddit_comment"],
                video_data["reddit_url"],
                video_data["video_creator"],
            ))

        conn.commit()
        return True

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        conn.rollback()
        return False

    except ValueError as e:
        print(f"Input error: {e}")
        return False

    finally:
        if conn:
            conn.close()