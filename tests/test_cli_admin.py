"""Tests for the owtf-admin CLI (in-memory SQLite, no real DB)."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Register sibling models so create_all(tables=[...]) can resolve FKs.
import owtf.models.email_confirmation  # noqa: F401
import owtf.models.user_login_token  # noqa: F401
from owtf import cli_admin
from owtf.models.user import User


@pytest.fixture()
def db(monkeypatch):
    """In-memory SQLite session wired into cli_admin.get_scoped_session."""
    engine = create_engine("sqlite:///:memory:")
    User.metadata.create_all(engine, tables=[User.__table__])
    Session = sessionmaker(bind=engine)
    # cli_admin opens a fresh session per command; reuse the same bound
    # factory so the underlying data is shared across calls.
    monkeypatch.setattr(cli_admin, "_get_session", lambda: Session())

    seed = Session()
    seed.add(User(name="Reg User", email="reg@example.com", password="x", is_admin=False, otp_secret_key="s1"))
    seed.add(User(name="Existing Admin", email="admin@example.com", password="x", is_admin=True, otp_secret_key="s2"))
    seed.commit()
    seed.close()

    yield Session


def _read_admin_flag(Session, email):
    s = Session()
    try:
        u = s.query(User).filter(User.email == email).one()
        return bool(u.is_admin)
    finally:
        s.close()


def test_promote_flips_is_admin(db, capsys):
    rc = cli_admin.main(["promote", "reg@example.com"])
    assert rc == 0
    assert _read_admin_flag(db, "reg@example.com") is True
    assert "is now an admin" in capsys.readouterr().out


def test_promote_is_idempotent(db, capsys):
    """Promoting an existing admin should succeed and say so."""
    rc = cli_admin.main(["promote", "admin@example.com"])
    assert rc == 0
    assert "already an admin" in capsys.readouterr().out


def test_promote_unknown_email_exits_nonzero(db, capsys):
    rc = cli_admin.main(["promote", "ghost@example.com"])
    assert rc == 1
    assert "No user found" in capsys.readouterr().out


def test_demote_flips_is_admin(db, capsys):
    rc = cli_admin.main(["demote", "admin@example.com"])
    assert rc == 0
    assert _read_admin_flag(db, "admin@example.com") is False
    assert "regular user" in capsys.readouterr().out


def test_demote_is_idempotent(db, capsys):
    rc = cli_admin.main(["demote", "reg@example.com"])
    assert rc == 0
    assert "already not an admin" in capsys.readouterr().out


def test_list_shows_db_admins_and_allow_list(db, capsys, monkeypatch):
    monkeypatch.setattr("owtf.settings.ADMIN_EMAILS", ["seeded@example.com"])
    rc = cli_admin.main(["list"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "admin@example.com" in out
    assert "seeded@example.com" in out


def test_email_lookup_is_case_insensitive(db, capsys):
    rc = cli_admin.main(["promote", "REG@Example.COM"])
    assert rc == 0
    assert _read_admin_flag(db, "reg@example.com") is True
