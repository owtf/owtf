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


def test_demote_revokes_admin_even_when_email_is_in_allow_list(db, capsys, monkeypatch):
    """After demote, user_is_admin (the auth path admin_required uses) must
    return False even if the email is still in OWTF_ADMIN_EMAILS."""
    from owtf.api.handlers.jwtauth import user_is_admin

    monkeypatch.setattr("owtf.settings.ADMIN_EMAILS", ["reg@example.com"])

    cli_admin.main(["promote", "reg@example.com"])
    session = db()
    try:
        user = session.query(User).filter(User.email == "reg@example.com").one()
        assert user_is_admin(user) is True
    finally:
        session.close()

    cli_admin.main(["demote", "reg@example.com"])
    session = db()
    try:
        user = session.query(User).filter(User.email == "reg@example.com").one()
        assert user_is_admin(user) is False, "demoted user must lose admin access even when email is in ADMIN_EMAILS"
    finally:
        session.close()


def test_login_handler_never_reads_admin_emails(db, monkeypatch):
    """Regression guard for the bug viyatb flagged on PR 1458.

    LogInHandler used to re-apply OWTF_ADMIN_EMAILS on every successful
    login, silently reverting any admin demotion on the next sign-in.
    The allow-list is a one-time seed at registration only; the login
    path must never touch users.is_admin. This test enforces that
    invariant at the source level so a future regression fails loudly.
    """
    import inspect

    from owtf.api.handlers import auth

    src = inspect.getsource(auth.LogInHandler.post)
    assert "ADMIN_EMAILS" not in src, (
        "LogInHandler.post must not read ADMIN_EMAILS; the allow-list is a "
        "registration-time seed only. Re-applying it here would silently "
        "revert admin demotions on the next login."
    )
    assert "is_admin" not in src, (
        "LogInHandler.post must not assign users.is_admin; admin changes flow through owtf-admin, not the login path."
    )


def test_demote_then_simulated_login_leaves_is_admin_false(db, monkeypatch):
    """End-to-end regression: seed admin via ADMIN_EMAILS, demote via CLI,
    look the user up the way LogInHandler does, and assert is_admin stays
    False. Together with test_login_handler_never_reads_admin_emails this
    covers both the invariant and its practical outcome."""
    monkeypatch.setattr("owtf.settings.ADMIN_EMAILS", ["reg@example.com"])

    # Simulate registration-time seed: promote reg@example.com so the row
    # starts life as an admin (this is what User.add_user would do when
    # the email is in ADMIN_EMAILS).
    cli_admin.main(["promote", "reg@example.com"])
    assert _read_admin_flag(db, "reg@example.com") is True

    # Admin demotes them via owtf-admin.
    cli_admin.main(["demote", "reg@example.com"])
    assert _read_admin_flag(db, "reg@example.com") is False

    # Simulate the login path: LogInHandler.post does User.find_by_email
    # and, after the fix, must not touch is_admin at all. Read the row
    # back the same way and confirm nothing flipped.
    session = db()
    try:
        user = User.find_by_email(session, "reg@example.com")
        assert user is not None
        assert user.is_admin is False, "login must not re-apply ADMIN_EMAILS; demoted user should stay non-admin"
    finally:
        session.close()
