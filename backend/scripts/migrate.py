"""Alembic Pre-Execution & Safe Migration Runner Script.

Usage:
    python scripts/migrate.py --action check
    python scripts/migrate.py --action upgrade [--revision head] [--backup]
    python scripts/migrate.py --action downgrade [--revision -1] [--backup]
    python scripts/migrate.py --action current
"""

import argparse
import logging
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from alembic import command
from alembic.config import Config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("migrate")


def get_alembic_config(config_path: Path | None = None) -> Config:
    """Resolve and load alembic.ini configuration."""
    if config_path is None:
        # Default to backend/alembic.ini
        base_dir = Path(__file__).resolve().parent.parent
        config_path = base_dir / "alembic.ini"

    if not config_path.exists():
        logger.error(f"Alembic configuration file not found at: {config_path}")
        sys.exit(1)

    cfg = Config(str(config_path))
    # Ensure script_location is absolute
    cfg.set_main_option("script_location", str(config_path.parent / "migrations"))
    return cfg


def backup_sqlite_db(cfg: Config) -> Path | None:
    """Create a timestamped backup of the local SQLite database if applicable."""
    sqlalchemy_url = os.getenv("DATABASE_URL") or cfg.get_main_option("sqlalchemy.url")
    if not sqlalchemy_url or "sqlite" not in sqlalchemy_url:
        return None

    # Extract SQLite path
    db_clean = sqlalchemy_url.split(":///")[-1].split("?")[0]
    db_path = Path(db_clean)
    if not db_path.is_absolute():
        base_dir = Path(__file__).resolve().parent.parent
        db_path = (base_dir / db_clean).resolve()

    if not db_path.exists():
        logger.info(f"SQLite database file {db_path} does not exist yet. Skipping backup.")
        return None

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_path = db_path.with_name(f"{db_path.stem}.backup_{timestamp}{db_path.suffix}")

    try:
        shutil.copy2(db_path, backup_path)
        logger.info(f"Successfully created SQLite backup at: {backup_path}")
        return backup_path
    except Exception as exc:
        logger.warning(f"Could not create database backup: {exc}")
        return None


def run_migration(action: str, revision: str, backup: bool, config_path: Path | None = None) -> int:
    """Execute the requested migration lifecycle action."""
    cfg = get_alembic_config(config_path)

    if action in ("upgrade", "downgrade") and backup:
        backup_sqlite_db(cfg)

    try:
        if action == "upgrade":
            logger.info(f"Applying Alembic migrations up to revision '{revision}'...")
            command.upgrade(cfg, revision)
            logger.info("Upgrade completed successfully.")
        elif action == "downgrade":
            logger.info(f"Rolling back Alembic migrations to revision '{revision}'...")
            command.downgrade(cfg, revision)
            logger.info("Downgrade completed successfully.")
        elif action == "current":
            logger.info("Current database revision:")
            command.current(cfg, verbose=True)
        elif action == "check":
            logger.info("Checking database migration status...")
            command.check(cfg)
            logger.info("Database schema is fully in sync with current Alembic revision head.")
        return 0
    except Exception as exc:
        logger.error(f"Migration action '{action}' failed: {exc}")
        return 1


def main() -> None:
    parser = argparse.ArgumentParser(description="SE IntelliPlatform Migration Runner")
    parser.add_argument(
        "--action",
        choices=["upgrade", "downgrade", "current", "check"],
        default="upgrade",
        help="Alembic action to perform (default: upgrade)",
    )
    parser.add_argument(
        "--revision",
        default="head",
        help="Target revision identifier (default: head)",
    )
    parser.add_argument(
        "--no-backup",
        dest="backup",
        action="store_false",
        help="Disable automatic backup of SQLite database before migration",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Custom path to alembic.ini",
    )

    args = parser.parse_args()
    if args.action == "downgrade" and args.revision == "head":
        args.revision = "-1"

    sys.exit(run_migration(action=args.action, revision=args.revision, backup=args.backup, config_path=args.config))


if __name__ == "__main__":
    main()
