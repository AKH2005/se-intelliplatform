import os
from alembic.config import Config
from alembic.script import ScriptDirectory
from app.models import Base


def test_alembic_script_directory_and_head():
    """Verify that Alembic script directory exists and head is 0010_users_table."""
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ini_path = os.path.join(backend_dir, "alembic.ini")
    
    alembic_cfg = Config(ini_path)
    script = ScriptDirectory.from_config(alembic_cfg)
    
    heads = script.get_heads()
    assert len(heads) == 1
    assert heads[0] == "0010_users_table"
    
    head_rev = script.get_revision("0010_users_table")
    assert head_rev is not None
    assert "users_table" in head_rev.doc or "users" in head_rev.doc.lower()
    assert head_rev.down_revision == "0009_preview_tasks_and_scores"


def test_alembic_metadata_table_coverage():
    """Verify all 16 platform tables are registered in Base.metadata."""
    table_names = set(Base.metadata.tables.keys())
    expected_tables = {
        "projects",
        "requirements",
        "project_context_snapshots",
        "workflow_executions",
        "agent_execution_audits",
        "development_versions",
        "development_changes",
        "environments",
        "preview_tasks",
        "preview_scores",
        "assistant_conversations",
        "assistant_messages",
        "assistant_action_audits",
        "assistant_confirmation_tokens",
        "deployment_records",
        "users",
    }
    assert expected_tables.issubset(table_names), f"Missing tables: {expected_tables - table_names}"
    assert "users" in table_names
