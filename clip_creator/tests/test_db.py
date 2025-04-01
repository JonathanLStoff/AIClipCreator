from unittest import main, TestCase, mock
from clip_creator.db.db import create_database, add_error_log
import sqlite3
import os
import json

class TestDB(TestCase):
    def setUp(self):
        self.db = 'test.db'
        create_database(db_path=self.db)
    def tearDown(self):
        if os.path.exists(self.db):
            try:
                os.remove(self.db)
            except Exception as e:
                print(f"Error deleting test database: {e}")
            
    def test_create_database(self):
        create_database(db_path=self.db)
        with sqlite3.connect(self.db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
        self.assertTrue(tables, msg="No tables found in the database")
        self.assertIn('reddit_coms_clips', tables, msg="Table 'reddit_coms_clips' not found in the database")
        
    def test_add_error_log_with_string(self):
        vid = "test_video"
        error_type = "string_error"
        error_data = "Something went wrong"
        add_error_log(vid, error_type, error_data, db_path=self.db)

        with sqlite3.connect(self.db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT video_id, log, error_type FROM error_log WHERE video_id=?", (vid,))
            row = cursor.fetchone()

        self.assertIsNotNone(row, msg="No row was inserted in error_log table")
        self.assertEqual(row[0], vid)
        self.assertEqual(row[1], error_data)
        self.assertEqual(row[2], error_type)

    def test_add_error_log_with_dict(self):
        vid = "test_video_dict"
        error_type = "dict_error"
        error_data = {"error": "Something went wrong"}
        add_error_log(vid, error_type, error_data, db_path=self.db)

        with sqlite3.connect(self.db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT video_id, log, error_type FROM error_log WHERE video_id=?", (vid,))
            row = cursor.fetchone()

        self.assertIsNotNone(row, msg="No row was inserted in error_log table")
        self.assertEqual(row[0], vid)
        # Parse JSON from the inserted log and compare with original dict.
        log = json.loads(row[1])
        self.assertEqual(log, error_data)
        self.assertEqual(row[2], error_type)

    def test_add_error_log_with_list(self):
        vid = "test_video_list"
        error_type = "list_error"
        error_data = ["Error1", "Error2"]
        add_error_log(vid, error_type, error_data, db_path=self.db)

        with sqlite3.connect(self.db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT video_id, log, error_type FROM error_log WHERE video_id=?", (vid,))
            row = cursor.fetchone()

        self.assertIsNotNone(row, msg="No row was inserted in error_log table")
        self.assertEqual(row[0], vid)
        log = json.loads(row[1])
        self.assertEqual(log, error_data)
        self.assertEqual(row[2], error_type)
    