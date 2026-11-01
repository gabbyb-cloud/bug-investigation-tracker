"""Bug Investigation Tracker: a small, local SQLite-backed CLI."""
import argparse
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

STATUSES = ('open', 'investigating', 'resolved', 'closed')
SEVERITIES = ('low', 'medium', 'high', 'critical')


@contextmanager
def connect(path):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute('PRAGMA foreign_keys=ON')
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(path):
    with connect(path) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS bugs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL CHECK(length(trim(title)) BETWEEN 1 AND 120),
            description TEXT NOT NULL DEFAULT '',
            severity TEXT NOT NULL CHECK(severity IN ('low','medium','high','critical')),
            status TEXT NOT NULL DEFAULT 'open' CHECK(status IN ('open','investigating','resolved','closed')),
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bug_id INTEGER NOT NULL REFERENCES bugs(id) ON DELETE CASCADE,
            note TEXT NOT NULL CHECK(length(trim(note)) BETWEEN 1 AND 2000),
            created_at TEXT NOT NULL
        )''')


def require_text(value, name, limit):
    cleaned = value.strip()
    if not cleaned or len(cleaned) > limit:
        raise ValueError(f'{name} must contain 1–{limit} characters')
    return cleaned


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def add_bug(path, title, severity='medium', description=''):
    title = require_text(title, 'title', 120)
    if severity not in SEVERITIES:
        raise ValueError('severity must be one of: ' + ', '.join(SEVERITIES))
    if len(description) > 2000:
        raise ValueError('description must not exceed 2000 characters')
    now = utc_now()
    with connect(path) as conn:
        cursor = conn.execute('''INSERT INTO bugs (title, description, severity, created_at, updated_at)
                                  VALUES (?, ?, ?, ?, ?)''', (title, description, severity, now, now))
        return cursor.lastrowid


def list_bugs(path, status=None):
    if status is not None and status not in STATUSES:
        raise ValueError('invalid status')
    with connect(path) as conn:
        if status:
            rows = conn.execute('SELECT * FROM bugs WHERE status=? ORDER BY id', (status,))
        else:
            rows = conn.execute('SELECT * FROM bugs ORDER BY id')
        return [dict(row) for row in rows]


def get_bug(path, bug_id):
    with connect(path) as conn:
        row = conn.execute('SELECT * FROM bugs WHERE id=?', (bug_id,)).fetchone()
        if row is None:
            raise ValueError(f'bug #{bug_id} not found')
        notes = conn.execute('SELECT * FROM notes WHERE bug_id=? ORDER BY id', (bug_id,))
        return dict(row), [dict(note) for note in notes]


def update_status(path, bug_id, status):
    if status not in STATUSES:
        raise ValueError('status must be one of: ' + ', '.join(STATUSES))
    with connect(path) as conn:
        cursor = conn.execute('UPDATE bugs SET status=?, updated_at=? WHERE id=?', (status, utc_now(), bug_id))
        if cursor.rowcount != 1:
            raise ValueError(f'bug #{bug_id} not found')


def add_note(path, bug_id, note):
    note = require_text(note, 'note', 2000)
    with connect(path) as conn:
        if conn.execute('SELECT 1 FROM bugs WHERE id=?', (bug_id,)).fetchone() is None:
            raise ValueError(f'bug #{bug_id} not found')
        conn.execute('INSERT INTO notes (bug_id, note, created_at) VALUES (?, ?, ?)', (bug_id, note, utc_now()))
        conn.execute('UPDATE bugs SET updated_at=? WHERE id=?', (utc_now(), bug_id))


def main(argv=None):
    parser = argparse.ArgumentParser(description='Local bug investigation tracker')
    parser.add_argument('--db', default='bugs.db', help='SQLite file (default: bugs.db)')
    sub = parser.add_subparsers(dest='command', required=True)
    create = sub.add_parser('add', help='Add a bug')
    create.add_argument('title')
    create.add_argument('--severity', choices=SEVERITIES, default='medium')
    create.add_argument('--description', default='')
    listing = sub.add_parser('list', help='List bugs')
    listing.add_argument('--status', choices=STATUSES)
    show = sub.add_parser('show', help='Show a bug and its notes')
    show.add_argument('id', type=int)
    status = sub.add_parser('status', help='Change a bug status')
    status.add_argument('id', type=int)
    status.add_argument('value', choices=STATUSES)
    note = sub.add_parser('note', help='Add an investigation note')
    note.add_argument('id', type=int)
    note.add_argument('text')
    args = parser.parse_args(argv)
    try:
        init_db(args.db)
        if args.command == 'add':
            print(f'Created bug #{add_bug(args.db, args.title, args.severity, args.description)}')
        elif args.command == 'list':
            rows = list_bugs(args.db, args.status)
            for row in rows:
                print(f"#{row['id']} [{row['severity']}] [{row['status']}] {row['title']}")
            if not rows:
                print('No bugs found.')
        elif args.command == 'show':
            bug, notes = get_bug(args.db, args.id)
            print(f"#{bug['id']} {bug['title']}\nSeverity: {bug['severity']} | Status: {bug['status']}")
            print(f"Description: {bug['description']}")
            for item in notes:
                print(f"  Note #{item['id']}: {item['note']}")
        elif args.command == 'status':
            update_status(args.db, args.id, args.value)
            print(f'Updated bug #{args.id} to {args.value}')
        elif args.command == 'note':
            add_note(args.db, args.id, args.text)
            print(f'Added note to bug #{args.id}')
        return 0
    except (ValueError, sqlite3.Error, OSError) as exc:
        parser.exit(2, f'Error: {exc}\n')


if __name__ == '__main__':
    raise SystemExit(main())
