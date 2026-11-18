"""Unit tests for backend/scripts/migrate.py migration runner."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from scripts.migrate import backup_sqlite_db, get_alembic_config, run_migration


def test_get_alembic_config():
    """Verify get_alembic_config loads valid alembic.ini configuration."""
    cfg = get_alembic_config()
    assert cfg is not None
    assert cfg.get_main_option("script_location") is not None


def test_backup_sqlite_db(tmp_path: Path):
    """Verify backup_sqlite_db creates a copy when SQLite file exists."""
    db_file = tmp_path / "test.db"
    db_file.write_text("dummy database content")

    mock_cfg = MagicMock()
    mock_cfg.get_main_option.return_value = f"sqlite:///{db_file}"

    with patch.dict(os.environ, {"DATABASE_URL": f"sqlite:///{db_file}"}):
        backup_path = backup_sqlite_db(mock_cfg)
        assert backup_path is not None
        assert backup_path.exists()
        assert "backup" in backup_path.name
        assert backup_path.read_text() == "dummy database content"


def test_run_migration_actions():
    """Verify run_migration dispatches upgrade, downgrade, current, and check."""
    with patch("scripts.migrate.command") as mock_command, patch("scripts.migrate.backup_sqlite_db"):
        # Upgrade
        res = run_migration("upgrade", "head", backup=False)
        assert res == 0
        mock_command.upgrade.assert_called_once()

        # Downgrade
        res = run_migration("downgrade", "-1", backup=False)
        assert res == 0
        mock_command.downgrade.assert_called_once()

        # Current
        res = run_migration("current", "head", backup=False)
        assert res == 0
        mock_command.current.assert_called_once()

        # Check
        res = run_migration("check", "head", backup=False)
        assert res == 0
        mock_command.check.assert_called_once()
