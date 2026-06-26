"""Data migration: create user system tables and migrate existing data.

Run this script ONCE after adding the user system models.
It will:
1. Create the users table
2. Add user_id columns to courses and chat_messages
3. Create a test user
4. Assign all existing data to the test user

Usage: python -m app.scripts.migrate_user_system
"""

from __future__ import annotations

import logging
from pathlib import Path
from sqlalchemy import text

from app.core.database import SessionLocal

logger = logging.getLogger(__name__)

# Test user credentials
TEST_USER_USERNAME = "demo"
TEST_USER_EMAIL = "demo@sitp.local"
TEST_USER_PASSWORD = "demo123"

# Database path
DB_PATH = Path(__file__).resolve().parents[2] / "data" / "smart_teaching.db"


def _column_exists(db, table: str, column: str) -> bool:
    """Check if a column exists in a SQLite table."""
    rows = db.execute(text(f"PRAGMA table_info({table})")).fetchall()
    return any(row[1] == column for row in rows)


def _table_exists(db, table: str) -> bool:
    """Check if a table exists in SQLite."""
    rows = db.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' AND name=:name"),
        {"name": table},
    ).fetchall()
    return len(rows) > 0


def migrate():
    """Run the user system migration."""
    db = SessionLocal()
    try:
        logger.info("=== User System Migration ===")

        # Step 1: Create users table
        if not _table_exists(db, "users"):
            logger.info("Creating users table...")
            db.execute(text("""
                CREATE TABLE users (
                    id INTEGER NOT NULL,
                    username VARCHAR(50) NOT NULL,
                    email VARCHAR(200) NOT NULL,
                    hashed_password VARCHAR(200) NOT NULL,
                    created_at DATETIME NOT NULL,
                    PRIMARY KEY (id),
                    UNIQUE (username),
                    UNIQUE (email)
                )
            """))
            db.commit()
            logger.info("Users table created.")
        else:
            logger.info("Users table already exists.")

        # Step 2: Add user_id to courses
        if not _column_exists(db, "courses", "user_id"):
            logger.info("Adding user_id column to courses...")
            db.execute(text("ALTER TABLE courses ADD COLUMN user_id INTEGER"))
            db.commit()
            logger.info("Added user_id to courses.")
        else:
            logger.info("courses.user_id already exists.")

        # Step 3: Add user_id to chat_messages
        if not _column_exists(db, "chat_messages", "user_id"):
            logger.info("Adding user_id column to chat_messages...")
            db.execute(text("ALTER TABLE chat_messages ADD COLUMN user_id INTEGER"))
            db.commit()
            logger.info("Added user_id to chat_messages.")
        else:
            logger.info("chat_messages.user_id already exists.")

        # Step 4: Check if test user already exists
        existing = db.execute(
            text("SELECT id FROM users WHERE username = :uname"),
            {"uname": TEST_USER_USERNAME},
        ).fetchone()

        if existing:
            test_user_id = existing[0]
            logger.info("Test user already exists: id=%d", test_user_id)
        else:
            # Create test user
            from app.core.security import hash_password

            now = __import__("datetime").datetime.now().replace(microsecond=0)
            hashed = hash_password(TEST_USER_PASSWORD)
            db.execute(
                text(
                    "INSERT INTO users (username, email, hashed_password, created_at) "
                    "VALUES (:uname, :email, :hpwd, :now)"
                ),
                {
                    "uname": TEST_USER_USERNAME,
                    "email": TEST_USER_EMAIL,
                    "hpwd": hashed,
                    "now": now,
                },
            )
            db.commit()

            test_user_id = db.execute(
                text("SELECT id FROM users WHERE username = :uname"),
                {"uname": TEST_USER_USERNAME},
            ).fetchone()[0]
            logger.info("Test user created: id=%d, username=%s", test_user_id, TEST_USER_USERNAME)

        # Step 5: Update existing courses to belong to test user
        null_courses = db.execute(
            text("SELECT COUNT(*) FROM courses WHERE user_id IS NULL")
        ).fetchone()[0]
        if null_courses > 0:
            logger.info("Assigning %d courses to test user...", null_courses)
            db.execute(
                text("UPDATE courses SET user_id = :uid WHERE user_id IS NULL"),
                {"uid": test_user_id},
            )
            db.commit()
            logger.info("Courses updated.")
        else:
            logger.info("All courses already have user_id set.")

        # Step 6: Update existing chat messages to belong to test user
        null_msgs = db.execute(
            text("SELECT COUNT(*) FROM chat_messages WHERE user_id IS NULL")
        ).fetchone()[0]
        if null_msgs > 0:
            logger.info("Assigning %d chat messages to test user...", null_msgs)
            db.execute(
                text("UPDATE chat_messages SET user_id = :uid WHERE user_id IS NULL"),
                {"uid": test_user_id},
            )
            db.commit()
            logger.info("Chat messages updated.")
        else:
            logger.info("All chat messages already have user_id set.")

        logger.info("=== Migration completed successfully! ===")
        logger.info("Test user credentials:")
        logger.info("  Email:    %s", TEST_USER_EMAIL)
        logger.info("  Password: %s", TEST_USER_PASSWORD)
        logger.info("  User ID:  %d", test_user_id)

    except Exception as e:
        logger.exception("Migration failed!")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    migrate()
