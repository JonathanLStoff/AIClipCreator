import datetime
import json
import sqlite3

import pandas as pd


def create_database(db_name="aiclipcreator.db"):
    """Creates or updates the aiclipcreator database with videos, clips, clip_info, and error_log tables."""

    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(reddit_posts_clips)")
    existing_columns = {col[1]: col[2] for col in cursor.fetchall()}
    if "parent_post_id" not in existing_columns:
        cursor.execute("ALTER TABLE reddit_posts_clips ADD COLUMN parent_post_id TEXT")
    if "author" not in existing_columns:
        cursor.execute("ALTER TABLE reddit_posts_clips ADD COLUMN author TEXT")
    cursor.execute("PRAGMA table_info(reddit_coms_clips)")
    existing_columns = {col[1]: col[2] for col in cursor.fetchall()}
    if "author" not in existing_columns:
        cursor.execute("ALTER TABLE reddit_coms_clips ADD COLUMN author TEXT")
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reddit_posts_clips (
                post_id TEXT PRIMARY KEY,
                title TEXT,
                content TEXT,
                upvotes INTEGER,
                comments INTEGER,
                nsfw BOOLEAN,
                posted_at TEXT,
                url TEXT,
                tiktok_posted TEXT,
                insta_posted TEXT,
                yt_posted TEXT,
                transcript TEXT,
                length REAL,
                parent_post_id TEXT,
                author TEXT
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reddit_coms_clips (
                post_id TEXT PRIMARY KEY,
                title TEXT,
                content TEXT,
                upvotes INTEGER,
                comments INTEGER,
                nsfw BOOLEAN,
                posted_at TEXT,
                url TEXT,
                tiktok_posted TEXT,
                insta_posted TEXT,
                yt_posted TEXT,
                transcript TEXT,
                comments_json TEXT,
                length REAL,
                author TEXT
            );
        """)
        # Check and create/update videos table
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='videos'"
        )
        if cursor.fetchone() is None:
            cursor.execute("""
                CREATE TABLE videos (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    uploaded_at TEXT,
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
        else:
            # Check and add missing columns
            expected_columns = [
                ("id", "TEXT PRIMARY KEY"),
                ("name", "TEXT"),
                ("created_at", "TEXT"),
                ("updated_at", "TEXT"),
                ("uploaded_at", "TEXT"),
                ("transcript", "TEXT"),
                ("one_word_most_used", "TEXT"),
                ("one_word_count", "INTEGER"),
                ("two_word_most_used", "TEXT"),
                ("two_word_count", "INTEGER"),
                ("three_word_most_used", "TEXT"),
                ("three_word_count", "INTEGER"),
                ("views", "INTEGER"),
                ("likes", "INTEGER"),
                ("top_yt_comment", "TEXT"),
                ("top_reddit_comment", "TEXT"),
                ("reddit_url", "TEXT"),
                ("video_creator", "TEXT"),
            ]
            cursor.execute("PRAGMA table_info(videos)")
            existing_columns = {col[1]: col[2] for col in cursor.fetchall()}
            for col_name, col_type in expected_columns:
                if col_name not in existing_columns:
                    cursor.execute(
                        f"ALTER TABLE videos ADD COLUMN {col_name} {col_type}"
                    )

        # Check and create/update clips table
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='clips'"
        )
        if cursor.fetchone() is None:
            cursor.execute("""
                CREATE TABLE clips (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id TEXT,
                    start_time INTEGER,
                    end_time INTEGER,
                    clip_transcript TEXT,
                    post_tiktok TEXT,
                    tiktok_url TEXT,
                    post_instagram TEXT,
                    instagram_url TEXT,
                    post_youtube TEXT,
                    youtube_url TEXT,
                    FOREIGN KEY (video_id) REFERENCES videos(id)
                )
            """)
        else:
            expected_columns = [
                ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
                ("video_id", "TEXT"),
                ("start_time", "INTEGER"),
                ("end_time", "INTEGER"),
                ("clip_transcript", "TEXT"),
                ("post_tiktok", "TEXT"),
                ("tiktok_url", "TEXT"),
                ("post_instagram", "TEXT"),
                ("instagram_url", "TEXT"),
                ("post_youtube", "TEXT"),
                ("youtube_url", "TEXT"),
            ]
            cursor.execute("PRAGMA table_info(clips)")
            existing_columns = {col[1]: col[2] for col in cursor.fetchall()}
            for col_name, col_type in expected_columns:
                if col_name not in existing_columns:
                    cursor.execute(
                        f"ALTER TABLE clips ADD COLUMN {col_name} {col_type}"
                    )

        # Check and create/update clip_info table
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='clip_info'"
        )
        if cursor.fetchone() is None:
            cursor.execute("""
                CREATE TABLE clip_info (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id TEXT,
                    clip_path TEXT,
                    description TEXT,
                    true_transcript TEXT,
                    title TEXT,
                    FOREIGN KEY (video_id) REFERENCES videos(id)
                )
            """)
        else:
            expected_columns = [
                ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
                ("video_id", "TEXT"),
                ("clip_path", "TEXT"),
                ("description", "TEXT"),
                ("true_transcript", "TEXT"),
                ("title", "TEXT"),
            ]
            cursor.execute("PRAGMA table_info(clip_info)")
            existing_columns = {col[1]: col[2] for col in cursor.fetchall()}
            for col_name, col_type in expected_columns:
                if col_name not in existing_columns:
                    cursor.execute(
                        f"ALTER TABLE clip_info ADD COLUMN {col_name} {col_type}"
                    )

        # Check and create/update error_log table
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='error_log'"
        )
        if cursor.fetchone() is None:
            cursor.execute("""
                CREATE TABLE error_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id TEXT,
                    log TEXT,
                    datetime TEXT,
                    error_type TEXT
                )
            """)
        else:
            expected_columns = [
                ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
                ("video_id", "TEXT"),
                ("log", "TEXT"),
                ("datetime", "TEXT"),
                ("error_type", "TEXT"),
            ]
            cursor.execute("PRAGMA table_info(error_log)")
            existing_columns = {col[1]: col[2] for col in cursor.fetchall()}
            for col_name, col_type in expected_columns:
                if col_name not in existing_columns:
                    cursor.execute(
                        f"ALTER TABLE error_log ADD COLUMN {col_name} {col_type}"
                    )

        conn.commit()
        print(f"Database '{db_name}' created or updated successfully.")

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        conn.rollback()

    finally:
        conn.close()


def add_error_log(vid, error_type, error, db_name="aiclipcreator.db"):
    """
    Adds a new row to the error_log table.

    Args:
        db_name (str): The name of the database file.
        video_id (str): The ID of the video associated with the error.
        log_data (dict or str): The error log data (can be a dictionary or a string).
    """
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    try:
        current_datetime = datetime.datetime.now().isoformat()
        if isinstance(error, dict):
            log_json = json.dumps(error)  # Serialize dictionary to JSON string
        elif isinstance(error, list):
            log_json = json.dumps(error)
        elif isinstance(error, str):
            log_json = error
        else:
            log_json = json.dumps({"error": "log_data must be dict or str"})

        cursor.execute(
            """
            INSERT INTO error_log (video_id, log, datetime, error_type)
            VALUES (?, ?, ?, ?)
            """,
            (vid, log_json, current_datetime, error_type),
        )

        conn.commit()
        print("Error log added successfully.")

    except sqlite3.Error as e:
        print(f"An error occurred while adding error log: {e}")
        conn.rollback()

    finally:
        conn.close()


def add_clip_info(info_data, db_name="aiclipcreator.db"):
    """
    Inserts a new row into the clip_info table.

    Args:
        info_data: A dictionary with the following keys:
            - video_id: (str) the associated video ID.
            - clip_path: (str) path to the clip file.
            - description: (str) description of the clip.
            - true_transcript: (str) the verified transcript.
            - title: (str) title of the clip.
        db_name: Name of the SQLite database file.

    Returns:
        The ID of the newly inserted row if successful, or None otherwise.
    """
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        required_keys = [
            "video_id",
            "clip_path",
            "description",
            "true_transcript",
            "title",
        ]
        if not all(key in info_data for key in required_keys):
            raise ValueError("Missing required keys in info_data")

        # Check if an entry for the given video_id and clip_path exists
        cursor.execute(
            """
            SELECT id FROM clip_info WHERE video_id = ? AND clip_path = ?
            """,
            (info_data["video_id"], info_data["clip_path"]),
        )
        existing = cursor.fetchone()

        if existing:
            clip_info_id = existing[0]
            cursor.execute(
                """
                UPDATE clip_info
                SET description = ?, true_transcript = ?, title = ?
                WHERE id = ?
                """,
                (
                    info_data["description"],
                    info_data["true_transcript"],
                    info_data["title"],
                    clip_info_id,
                ),
            )
        else:
            cursor.execute(
                """
                INSERT INTO clip_info (video_id, clip_path, description, true_transcript, title)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    info_data["video_id"],
                    info_data["clip_path"],
                    info_data["description"],
                    info_data["true_transcript"],
                    info_data["title"],
                ),
            )
            clip_info_id = cursor.lastrowid

        conn.commit()
        return clip_info_id

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        conn.rollback()
        return None

    except ValueError as e:
        print(f"Input error: {e}")
        return None

    finally:
        if conn:
            conn.close()


def get_all_video_ids(db_name="aiclipcreator.db"):
    """
    Retrieves all video IDs from the videos table.

    Args:
        db_name: Name of the SQLite database file.

    Returns:
        A list of video IDs.
    """
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT video_id FROM clips")
        rows = cursor.fetchall()
        return [row[0] for row in rows]
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []
    finally:
        if conn:
            conn.close()


def get_all_videos_df(db_name="aiclipcreator.db"):
    """
    Retrieves all rows from the videos table into a pandas DataFrame.

    Args:
        db_name: Name of the SQLite database file.

    Returns:
        A pandas DataFrame containing all rows from the videos table.
    """
    try:
        conn = sqlite3.connect(db_name)
        df = pd.read_sql_query("SELECT * FROM videos", conn)
        return df
    except Exception as e:
        print(f"Error: {e}")
        return pd.DataFrame()
    finally:
        if conn:
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
        now = datetime.datetime.now(datetime.UTC)

        # Ensure all required keys are present (you might want more thorough validation)
        required_keys = [
            "id",
            "name",
            "transcript",
            "one_word_most_used",
            "one_word_count",
            "two_word_most_used",
            "two_word_count",
            "three_word_most_used",
            "three_word_count",
            "views",
            "likes",
            "top_yt_comment",
            "top_reddit_comment",
            "reddit_url",
            "video_creator",
        ]
        if not all(key in video_data for key in required_keys):
            raise ValueError("Missing required keys in video_data")

        # Check if the video id already exists
        cursor.execute("SELECT 1 FROM videos WHERE id = ?", (video_data["id"],))
        exists = cursor.fetchone()

        if exists:
            # Update the existing video entry (keeping created_at unchanged)
            cursor.execute(
                """
                UPDATE videos
                SET name = ?, updated_at = ?, transcript = ?, one_word_most_used = ?, one_word_count = ?,
                    two_word_most_used = ?, two_word_count = ?, three_word_most_used = ?, three_word_count = ?,
                    views = ?, likes = ?, top_yt_comment = ?, top_reddit_comment = ?, reddit_url = ?, video_creator = ?
                WHERE id = ?
            """,
                (
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
                ),
            )
        else:
            # Insert new video entry
            cursor.execute(
                """
                INSERT INTO videos (id, name, created_at, updated_at, uploaded_at, transcript, one_word_most_used, one_word_count, two_word_most_used, two_word_count, three_word_most_used, three_word_count, views, likes, top_yt_comment, top_reddit_comment, reddit_url, video_creator)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    video_data["id"],
                    video_data["name"],
                    now,  # created_at
                    now,  # updated_at (initially same as created_at)
                    None,  # uploaded_at (can be set later)
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
                ),
            )

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


def create_or_update_clip(clip_data, db_path="aiclipcreator.db"):
    """
    Creates a new clip record or updates an existing one.

    Args:
        clip_data: A dictionary containing the clip data.  Must include 'video_id', 'start_time', 'end_time', and 'clip_transcript'.
            May optionally include 'post_tiktok', 'tiktok_url', 'post_instagram', 'instagram_url', 'post_youtube', 'youtube_url', and 'id'.
        db_path: Path to the SQLite database file.

    Returns:
        The ID of the created or updated clip. Returns None on error.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        required_keys = ["video_id", "start_time", "end_time", "clip_transcript"]
        if not all(key in clip_data for key in required_keys):
            raise ValueError(
                "clip_data must contain 'video_id', 'start_time', 'end_time', and"
                " 'clip_transcript'"
            )

        video_id = clip_data["video_id"]
        start_time = clip_data["start_time"]
        end_time = clip_data["end_time"]
        clip_transcript = clip_data["clip_transcript"]

        # Construct the SET and VALUES parts of the SQL query dynamically
        set_values = []
        values = []
        data_to_execute = []

        for key, value in clip_data.items():
            if key not in (
                "id",
                "video_id",
                "start_time",
                "end_time",
            ):  # Exclude these from SET/VALUES
                set_values.append(f"{key} = ?")
                values.append(key)
                data_to_execute.append(value)

        data_to_execute.extend([
            clip_transcript, None, None, None, None, None, None
        ])  # Fill out the rest of the values in the correct order
        set_values_string = ", ".join(set_values)

        # Check if an ID is provided. If so, it's an update.
        if "id" in clip_data:
            clip_id = clip_data["id"]
            cursor.execute(
                f"""
                UPDATE clips SET {set_values_string}
                WHERE id = ?
            """,
                (*data_to_execute[:-7], clip_id),
            )  # Exclude transcript and social media fields from set_values
        else:
            # Check if a clip with the given video_id, start_time, and end_time already exists
            cursor.execute(
                """
                SELECT id FROM clips
                WHERE video_id = ? AND start_time = ? AND end_time = ?
            """,
                (video_id, start_time, end_time),
            )
            existing_clip = cursor.fetchone()

            if existing_clip:
                clip_id = existing_clip[0]  # Get the existing clip ID
                cursor.execute(
                    f"""
                    UPDATE clips SET {set_values_string}
                    WHERE id = ?
                """,
                    (*data_to_execute[:-7], clip_id),
                )  # Exclude transcript and social media fields from set_values
            else:
                # Create a new clip
                columns = ", ".join(clip_data.keys())
                placeholders = ", ".join(["?"] * len(clip_data))
                cursor.execute(
                    f"""
                    INSERT INTO clips ({columns})
                    VALUES ({placeholders})
                """,
                    tuple(clip_data.values()),
                )
                clip_id = cursor.lastrowid  # Get the ID of the newly inserted row

        conn.commit()
        conn.close()
        return clip_id

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        if conn:
            conn.close()  # Close connection in case of error
        return None
    except ValueError as e:
        print(f"Value Error: {e}")
        return None


def find_clip(video_id, start_time, db_path="aiclipcreator.db"):
    """
    Finds a clip in the database based on video_id and start_time.

    Args:
        video_id: The video ID to search for.
        start_time: The start time to search for.
        db_path: Path to the SQLite database file.

    Returns:
        A dictionary containing the clip data if found, or None if not found.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM clips
            WHERE video_id = ? AND start_time = ?
        """,
            (video_id, start_time),
        )

        clip_data = cursor.fetchone()
        conn.close()

        if clip_data:
            # Get column names from the cursor description
            column_names = [description[0] for description in cursor.description]

            # Create a dictionary mapping column names to values
            clip_dict = dict(zip(column_names, clip_data))
            return clip_dict
        else:
            return None

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        if conn:
            conn.close()
        return None


def get_all_clips_df(db_name="aiclipcreator.db"):
    """
    Retrieves all rows from the clips table into a pandas DataFrame.

    Args:
        db_name: Name of the SQLite database file.

    Returns:
        A pandas DataFrame containing all rows from the clips table.
    """
    try:
        conn = sqlite3.connect(db_name)
        df = pd.read_sql_query("SELECT * FROM clips", conn)
        return df
    except Exception as e:
        print(f"Error: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()


def update_post_status(video_id, platform, status, db_path="aiclipcreator.db"):
    """
    Updates the post status (post_tiktok, post_instagram, post_youtube) for a given video_id.

    Args:
        db_path (str): Path to the SQLite database file.
        video_id (str): The video_id to identify the row.
        platform (str): The platform to update ('tiktok', 'instagram', or 'youtube').
        status (str): The new status ('True' or 'False' or other values as needed).
    Returns:
        bool: True if the update was successful, False otherwise.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        platform_column = f"post_{platform}"

        cursor.execute(
            f"""
                UPDATE clips
                SET {platform_column} = ?
                WHERE video_id = ?
            """,
            (status, video_id),
        )

        conn.commit()
        return True

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        return False

    finally:
        if conn:
            conn.close()
def get_rows_where_tiktok_null_or_empty(db_name="aiclipcreator.db"):
    """
    Retrieves a list of rows (as dictionaries) where tiktok_posted is NULL, empty, or not set.
    """
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM reddit_posts_clips
            WHERE tiktok_posted IS NULL OR tiktok_posted = '';
        """)

        rows = cursor.fetchall()
        column_names = [description[0] for description in cursor.description]  # Get column names

        result = []
        for row in rows:
            row_dict = dict(zip(column_names, row))
            result.append(row_dict)

        return result

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        return []  # Return an empty list in case of an error

    finally:
        if conn:
            conn.close()
def add_reddit_post_clip(post_id, title, content, upvotes, comments, nsfw, posted_at, url, parent_id=None, author=None, db_path="aiclipcreator.db"):
    """Adds a new Reddit post clip to the database."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        if parent_id:
            cursor.execute("""
                INSERT INTO reddit_posts_clips (post_id, title, content, upvotes, comments, nsfw, posted_at, url, author, parent_post_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (post_id, title, content, upvotes, comments, nsfw, posted_at, url, author, parent_id))
        else:
            cursor.execute("""
                INSERT INTO reddit_posts_clips (post_id, title, content, upvotes, comments, nsfw, posted_at, url, author)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (post_id, title, content, upvotes, comments, nsfw, posted_at, url, author))

        conn.commit()
        print(f"Post clip with post_id '{post_id}' added successfully.")

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")

    finally:
        if conn:
            conn.close()
def get_reddit_post_clip_by_id(post_id, db_name="aiclipcreator.db"):
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM reddit_posts_clips WHERE post_id = ?", (post_id,))
        row = cursor.fetchone()
        if row:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
        return None
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return None
    finally:
        if conn:
            conn.close()
def update_reddit_post_clip(post_id, tiktok_posted=None, insta_posted=None, yt_posted=None, transcript=None, length=None, db_path="aiclipcreator.db"):
    """Updates a Reddit post clip in the database."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        update_fields = []
        update_values = []

        if tiktok_posted is not None:
            update_fields.append("tiktok_posted = ?")
            update_values.append(tiktok_posted)
        if insta_posted is not None:
            update_fields.append("insta_posted = ?")
            update_values.append(insta_posted)
        if yt_posted is not None:
            update_fields.append("yt_posted = ?")
            update_values.append(yt_posted)
        if transcript is not None:
            update_fields.append("transcript = ?")
            update_values.append(transcript)
        if length is not None:
            update_fields.append("length = ?")
            update_values.append(length)

        if not update_fields:
            print("No fields to update.")
            return

        update_query = "UPDATE reddit_posts_clips SET " + ", ".join(update_fields) + " WHERE post_id = ?"
        update_values.append(post_id)

        cursor.execute(update_query, update_values)

        if cursor.rowcount > 0:
            conn.commit()
            print(f"Post clip with post_id '{post_id}' updated successfully.")
        else:
            print(f"Post clip with post_id '{post_id}' not found.")

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")

    finally:
        if conn:
            conn.close()
def get_all_post_ids_red(db_path="aiclipcreator.db"):
    """Retrieves a list of all post_ids from the reddit_posts_clips table."""
    post_ids = []
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT post_id FROM reddit_posts_clips")
        rows = cursor.fetchall()

        for row in rows:
            post_ids.append(row[0])  # Append the first element (post_id) of each row

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")

    finally:
        if conn:
            conn.close()

    return post_ids
def get_rows_where_tiktok_null_or_empty_com(db_name="aiclipcreator.db"):
    """
    Retrieves a list of rows (as dictionaries) where tiktok_posted is NULL, empty, or not set.
    """
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM reddit_coms_clips
            WHERE tiktok_posted IS NULL OR tiktok_posted = '';
        """)

        rows = cursor.fetchall()
        column_names = [description[0] for description in cursor.description]  # Get column names

        result = []
        for row in rows:
            row_dict = dict(zip(column_names, row))
            result.append(row_dict)

        return result

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        return []  # Return an empty list in case of an error

    finally:
        if conn:
            conn.close()
def add_reddit_post_clip_com(post_id, title, content, upvotes, comments, comments_json, nsfw, posted_at, url, db_path="aiclipcreator.db"):
    """Adds a new Reddit post clip to the database."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO reddit_coms_clips (post_id, title, content, upvotes, comments, comments_json, nsfw, posted_at, url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (post_id, title, content, upvotes, comments, json.dumps(comments_json), nsfw, posted_at, url))

        conn.commit()
        print(f"Post clip with post_id '{post_id}' added successfully.")

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")

    finally:
        if conn:
            conn.close()

def update_reddit_post_clip_com(post_id, tiktok_posted=None, insta_posted=None, yt_posted=None, transcript=None, length=None, db_path="aiclipcreator.db"):
    """Updates a Reddit post clip in the database."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        update_fields = []
        update_values = []

        if tiktok_posted is not None:
            update_fields.append("tiktok_posted = ?")
            update_values.append(tiktok_posted)
        if insta_posted is not None:
            update_fields.append("insta_posted = ?")
            update_values.append(insta_posted)
        if yt_posted is not None:
            update_fields.append("yt_posted = ?")
            update_values.append(yt_posted)
        if transcript is not None:
            update_fields.append("transcript = ?")
            update_values.append(transcript)
        if length is not None:
            update_fields.append("length = ?")
            update_values.append(length)

        if not update_fields:
            print("No fields to update.")
            return

        update_query = "UPDATE reddit_coms_clips SET " + ", ".join(update_fields) + " WHERE post_id = ?"
        update_values.append(post_id)

        cursor.execute(update_query, update_values)

        if cursor.rowcount > 0:
            conn.commit()
            print(f"Post clip with post_id '{post_id}' updated successfully.")
        else:
            print(f"Post clip with post_id '{post_id}' not found.")

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")

    finally:
        if conn:
            conn.close()
def get_all_post_ids_red_com(db_path="aiclipcreator.db"):
    """Retrieves a list of all post_ids from the reddit_coms_clips table."""
    post_ids = []
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT post_id FROM reddit_coms_clips")
        rows = cursor.fetchall()

        for row in rows:
            post_ids.append(row[0])  # Append the first element (post_id) of each row

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")

    finally:
        if conn:
            conn.close()

    return post_ids