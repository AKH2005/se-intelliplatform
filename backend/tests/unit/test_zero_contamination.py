import pytest
from app.models.project import Project
from app.services.application_developer_service import ApplicationDeveloperService
from app.runtime.preview_server import get_app_html_for_project

def test_auth_context_isolation():
    """Verify each project archetype gets strictly isolated, domain-authentic authentication credentials."""
    # 1. Enterprise Inventory
    inv_proj = Project(name="Enterprise Inventory & Warehouse Management System", description="SKU tracking and warehouse stock management")
    inv_ctx = ApplicationDeveloperService._get_project_auth_context(inv_proj)
    assert inv_ctx["demo_email"] == "admin@inventory.local"
    assert inv_ctx["demo_role"] == "Warehouse Admin"
    assert inv_ctx["action_button"] == "Sign In to Inventory Portal"
    assert "ninja" not in str(inv_ctx).lower()
    assert "arena" not in str(inv_ctx).lower()
    assert "shadow" not in str(inv_ctx).lower()

    # 2. Carrom Master
    carrom_proj = Project(name="Carrom Master", description="Realistic carrom board physics simulation")
    carrom_ctx = ApplicationDeveloperService._get_project_auth_context(carrom_proj)
    assert carrom_ctx["demo_email"] == "player@carrommaster.local"
    assert carrom_ctx["demo_role"] == "Pro Striker"
    assert carrom_ctx["action_button"] == "Sign In to Carrom Master"
    assert "ninja" not in str(carrom_ctx).lower()
    assert "shadow" not in str(carrom_ctx).lower()

    # 3. Executive Analytics
    analytics_proj = Project(name="Executive Analytics Dashboard", description="KPI metrics and revenue analytics")
    analytics_ctx = ApplicationDeveloperService._get_project_auth_context(analytics_proj)
    assert analytics_ctx["demo_email"] == "executive@analytics.local"
    assert analytics_ctx["demo_role"] == "VP Operations"
    assert "ninja" not in str(analytics_ctx).lower()

    # 4. Shadow Duel
    shadow_proj = Project(name="Shadow Duel", description="2D arena fighting game with shadow warriors")
    shadow_ctx = ApplicationDeveloperService._get_project_auth_context(shadow_proj)
    assert shadow_ctx["demo_email"] == "ninja@shadowduel.com"
    assert shadow_ctx["demo_role"] == "Grandmaster"
    assert shadow_ctx["action_button"] == "Sign In to Arena"

def test_login_injection_zero_contamination():
    """Verify HTML login injection never introduces foreign project branding or auto-open modal."""
    inv_proj = Project(name="Enterprise Inventory & Warehouse Management System", description="SKU tracking and warehouse stock management")
    service = ApplicationDeveloperService(None, None, None)
    
    sample_html = "<!DOCTYPE html><html><head><style></style></head><body><div class='header'><h1>Inventory</h1></div></body></html>"
    injected = service._inject_login_into_html(sample_html, inv_proj.name, inv_proj)

    # Must contain domain credentials
    assert "admin@inventory.local" in injected
    assert "Sign In to Inventory Portal" in injected
    assert "Quick Fill Inventory Admin" in injected

    # Must NOT contain Shadow Duel markers
    assert "ninja@shadowduel.com" not in injected
    assert "Sign In to Arena" not in injected
    assert "Quick Fill Demo Ninja" not in injected
    assert "Shadow Slayer" not in injected
    assert "Master Shadow" not in injected

    # Must NOT force-open modal on page load
    assert "openAuthModal();\n    }" not in injected

def test_preview_pipeline_zero_contamination():
    """Verify preview server serves authentic project content without cross-contamination."""
    # Enterprise Inventory
    inv_id = "555c5336-f1da-4183-adc3-c1616e48359c"
    html_inv = get_app_html_for_project(project_id=inv_id)
    assert "ninja@shadowduel.com" not in html_inv
    assert "Sign In to Arena" not in html_inv
    assert "Quick Fill Demo Ninja" not in html_inv
    assert any(k in html_inv for k in ["Enterprise Inventory", "Warehouse", "SKU"])

    # Carrom Master
    carrom_id = "63d85665-67dd-48c0-8625-e81bded66426"
    html_carrom = get_app_html_for_project(project_id=carrom_id)
    assert "ninja@shadowduel.com" not in html_carrom
    assert any(k in html_carrom.lower() for k in ["carrom", "striker"])

    # Shadow Duel
    sd_id = "68289eab-12f4-4602-a4b7-143f29c52c58"
    html_sd = get_app_html_for_project(project_id=sd_id)
    assert any(k in html_sd for k in ["Shadow Duel", "CombatArena", "combatCanvas", "Katana"])

