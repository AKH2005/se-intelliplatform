"""Domain Templates for SE IntelliPlatform Archetypes.

Provides production-grade, multi-file source implementations for all core enterprise archetypes:
- Inventory & Warehouse Management (inventory)
- Learning Management System (lms)
- E-Commerce Storefront & Cart (ecommerce)
- Conference & Event Hub (eventhub)
- Kanban Taskflow Management (taskflow)
"""

from typing import Optional


def get_domain_file_content(
    archetype: str,
    norm_path: str,
    project_name: str,
    project_desc: str,
) -> Optional[str]:
    """Route file request to authoritative domain template implementation."""
    if archetype == "inventory":
        from .inventory_domain import get_inventory_file
        return get_inventory_file(norm_path, project_name, project_desc)

    if archetype in ("lms", "educational"):
        from .lms_domain import get_lms_file
        return get_lms_file(norm_path, project_name, project_desc)

    if archetype == "ecommerce":
        from .ecommerce_domain import get_ecommerce_file
        return get_ecommerce_file(norm_path, project_name, project_desc)

    if archetype == "eventhub":
        from .eventhub_domain import get_eventhub_file
        return get_eventhub_file(norm_path, project_name, project_desc)

    if archetype in ("taskflow", "management"):
        from .taskflow_domain import get_taskflow_file
        return get_taskflow_file(norm_path, project_name, project_desc)

    return None
