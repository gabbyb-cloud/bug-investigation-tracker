import sqlite3
from contextlib import closing
import tempfile
import unittest
from pathlib import Path

from tracker import add_bug, add_note, get_bug, init_db, list_bugs, update_status


class TrackerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / 'test.db'
        init_db(self.db)

    def tearDown(self):
        self.temp.cleanup()

    def test_add_and_list(self):
        bug_id = add_bug(self.db, '  Login fails  ', 'high', 'Regression')
        bugs = list_bugs(self.db)
        self.assertEqual((bug_id, bugs[0]['title'], bugs[0]['severity']), (1, 'Login fails', 'high'))

    def test_filter_by_status(self):
        bug_id = add_bug(self.db, 'Login fails')
        update_status(self.db, bug_id, 'investigating')
        self.assertEqual(len(list_bugs(self.db, 'open')), 0)
        self.assertEqual(len(list_bugs(self.db, 'investigating')), 1)

    def test_add_note(self):
        bug_id = add_bug(self.db, 'Unexpected response')
        add_note(self.db, bug_id, 'Reproduced with malformed JSON')
        _, notes = get_bug(self.db, bug_id)
        self.assertEqual(notes[0]['note'], 'Reproduced with malformed JSON')

    def test_invalid_title_or_severity_does_not_write(self):
        for title, severity in [('', 'high'), ('x' * 121, 'low'), ('Fine', 'urgent')]:
            with self.assertRaises(ValueError):
                add_bug(self.db, title, severity)
        self.assertEqual(list_bugs(self.db), [])

    def test_invalid_status_does_not_update(self):
        bug_id = add_bug(self.db, 'Broken link')
        with self.assertRaises(ValueError):
            update_status(self.db, bug_id, 'deleted')
        self.assertEqual(get_bug(self.db, bug_id)[0]['status'], 'open')

    def test_missing_bug_does_not_create_orphan_notes(self):
        with self.assertRaises(ValueError):
            add_note(self.db, 999, 'Investigation note')
        with closing(sqlite3.connect(self.db)) as conn:
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM notes').fetchone()[0], 0)

    def test_missing_bug_status_rejected(self):
        with self.assertRaises(ValueError):
            update_status(self.db, 999, 'closed')

    def test_sql_injection_stored_as_text(self):
        payload = "x'); DROP TABLE bugs; --"
        add_bug(self.db, payload)
        self.assertEqual(list_bugs(self.db)[0]['title'], payload)
        add_bug(self.db, 'Still available')
        self.assertEqual(len(list_bugs(self.db)), 2)

    def test_reject_empty_note(self):
        bug_id = add_bug(self.db, 'Failed sync')
        with self.assertRaises(ValueError):
            add_note(self.db, bug_id, '   ')
        self.assertEqual(get_bug(self.db, bug_id)[1], [])

    def test_database_persists_across_connections(self):
        bug_id = add_bug(self.db, 'Persistent bug')
        self.assertEqual(get_bug(self.db, bug_id)[0]['title'], 'Persistent bug')


if __name__ == '__main__':
    unittest.main()
