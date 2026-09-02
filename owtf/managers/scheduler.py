"""Scheduler ordering policy for queued work."""
from sqlalchemy import case

PLUGIN_TYPE_PRIORITY = {
    "active": 40,
    "semi_passive": 30,
    "passive": 20,
    "grep": 10,
    "external": 0,
}

PLUGIN_RISK_PRIORITY = {
    "OWTF-DV-005": 30,  # SQL injection
    "OWTF-DV-012": 30,  # Code injection
    "OWTF-DV-013": 30,  # Command injection
    "OWTF-DV-001": 20,  # Reflected XSS
    "OWTF-DV-002": 20,  # Stored XSS
    "OWTF-AZ-002": 20,  # Auth bypass
    "OWTF-ST-001": 20,  # Subdomain takeover
    "OWTF-CM-001": 10,  # SSL/TLS
}


def plugin_priority_expr(plugin_model):
    """Return a SQLAlchemy expression used to order queued work."""
    type_priority = case(
        PLUGIN_TYPE_PRIORITY,
        value=plugin_model.type,
        else_=0,
    )
    risk_priority = case(
        PLUGIN_RISK_PRIORITY,
        value=plugin_model.code,
        else_=0,
    )
    return type_priority + risk_priority
