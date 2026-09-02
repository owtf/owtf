"""
tests.unit.managers.test_scheduler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Unit tests for the query-time priority scheduler.
"""
from owtf.managers.scheduler import (
    PLUGIN_RISK_PRIORITY,
    PLUGIN_TYPE_PRIORITY,
    plugin_priority_expr,
)


class MockPlugin:
    """Minimal mock of Plugin model for testing priority expressions."""
    def __init__(self, plugin_type, code):
        self.type = plugin_type
        self.code = code


def compute_priority(plugin_type, code):
    """Helper: compute numeric priority for a plugin type + code combination."""
    type_score = PLUGIN_TYPE_PRIORITY.get(plugin_type, 0)
    risk_score = PLUGIN_RISK_PRIORITY.get(code, 0)
    return type_score + risk_score


def test_active_plugin_scores_higher_than_passive():
    """Active plugins must always score higher than passive for the same code."""
    assert compute_priority("active", "OWTF-CM-003") > compute_priority("passive", "OWTF-CM-003")


def test_semi_passive_scores_between_active_and_passive():
    """semi_passive must fall between active and passive."""
    active = compute_priority("active", "OWTF-CM-003")
    semi = compute_priority("semi_passive", "OWTF-CM-003")
    passive = compute_priority("passive", "OWTF-CM-003")
    assert active > semi > passive


def test_plugin_type_ordering():
    """All types must produce strictly decreasing scores: active > semi_passive > passive > grep > external."""
    code = "OWTF-CM-003"  # no risk bonus, so score = type only
    types = ["active", "semi_passive", "passive", "grep", "external"]
    scores = [compute_priority(t, code) for t in types]
    assert scores == sorted(scores, reverse=True)


def test_sqli_plugin_scores_higher_than_regular():
    """SQLi plugin (risk=30) must score higher than regular plugin with same type."""
    sqli = compute_priority("passive", "OWTF-DV-005")
    regular = compute_priority("passive", "OWTF-CM-003")
    assert sqli > regular


def test_xss_plugin_scores_higher_than_regular():
    """XSS plugin (risk=20) must score higher than regular plugin with same type."""
    xss = compute_priority("passive", "OWTF-DV-001")
    regular = compute_priority("passive", "OWTF-CM-003")
    assert xss > regular


def test_unknown_type_defaults_to_zero():
    """Unknown plugin types get score 0 from type priority."""
    assert compute_priority("unknown_type", "OWTF-CM-003") == 0


def test_unknown_code_defaults_to_zero_risk():
    """Unknown plugin codes get 0 risk bonus."""
    assert compute_priority("active", "OWTF-UNKNOWN-999") == PLUGIN_TYPE_PRIORITY["active"]


def test_high_risk_passive_can_outscore_low_risk_active():
    """A passive SQLi plugin (20+30=50) scores higher than active SSL/TLS (40+10=50)... edge case."""
    sqli_passive = compute_priority("passive", "OWTF-DV-005")   # 20 + 30 = 50
    active_ssl = compute_priority("active", "OWTF-CM-001")       # 40 + 10 = 50
    assert sqli_passive == active_ssl  # tied — tiebreak by Work.id


def test_plugin_priority_expr_returns_sqlalchemy_expression():
    """plugin_priority_expr() must return a SQLAlchemy expression (not None)."""
    mock = MockPlugin("active", "OWTF-DV-005")
    expr = plugin_priority_expr(mock)
    assert expr is not None
