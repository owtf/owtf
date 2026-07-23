"""
owtf.cli_admin
~~~~~~~~~~~~~~

Small command-line tool for promoting or demoting OWTF users to the
platform admin role, without having to touch the database by hand or
edit ``OWTF_ADMIN_EMAILS``.

Registered as the ``owtf-admin`` console script in ``pyproject.toml``.

Examples
--------
    owtf-admin promote reviewer@example.com
    owtf-admin demote  reviewer@example.com
    owtf-admin list

The tool flips the ``users.is_admin`` column directly. It intentionally
does NOT modify the ``OWTF_ADMIN_EMAILS`` allow-list, because that env
var is meant for pre-seeded/bootstrap access and should not be treated
as the ongoing source of truth for who is an admin.
"""

import argparse
import sys


def _get_session():
    """Open a scoped DB session. Imported lazily so ``--help`` works
    without a running database."""
    from owtf.db.session import get_scoped_session

    return get_scoped_session()


def _find_user(session, email):
    """Return the user with this email, or None. Email match is
    case-insensitive because that is how the allow-list normalises."""
    from owtf.models.user import User

    target = (email or "").strip().lower()
    if not target:
        return None
    return session.query(User).filter(User.email.ilike(target)).first()


def _set_admin(email, value):
    """Flip is_admin for the user with this email. Returns an exit code
    suitable for sys.exit."""
    session = _get_session()
    try:
        user = _find_user(session, email)
        if user is None:
            print("No user found with email {!r}. Ask them to register first.".format(email))
            return 1
        if bool(user.is_admin) == bool(value):
            print("{} is already {}.".format(user.email, "an admin" if value else "not an admin"))
            return 0
        user.is_admin = bool(value)
        session.commit()
        print("{} is now {}.".format(user.email, "an admin" if value else "a regular user"))
        return 0
    finally:
        session.close()


def _cmd_promote(args):
    return _set_admin(args.email, True)


def _cmd_demote(args):
    return _set_admin(args.email, False)


def _cmd_list(_args):
    """Print every user with is_admin=True, plus the ADMIN_EMAILS
    allow-list, so an operator can see who currently has admin access."""
    from owtf.settings import ADMIN_EMAILS

    session = _get_session()
    try:
        from owtf.models.user import User

        admins = session.query(User).filter(User.is_admin.is_(True)).order_by(User.email).all()
        if admins:
            print("Users with is_admin=True:")
            for u in admins:
                print("  {}  ({})".format(u.email, u.name or ""))
        else:
            print("Users with is_admin=True: (none)")

        print()
        if ADMIN_EMAILS:
            print("OWTF_ADMIN_EMAILS allow-list (auto-promoted on login):")
            for email in ADMIN_EMAILS:
                print("  {}".format(email))
        else:
            print("OWTF_ADMIN_EMAILS allow-list: (empty)")
        return 0
    finally:
        session.close()


def _build_parser():
    parser = argparse.ArgumentParser(
        prog="owtf-admin",
        description="Manage OWTF admin roles without editing the database by hand.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_promote = sub.add_parser("promote", help="Give a user the admin role.")
    p_promote.add_argument("email", help="The user's email address.")
    p_promote.set_defaults(func=_cmd_promote)

    p_demote = sub.add_parser("demote", help="Remove the admin role from a user.")
    p_demote.add_argument("email", help="The user's email address.")
    p_demote.set_defaults(func=_cmd_demote)

    p_list = sub.add_parser("list", help="Show every current admin (DB flag + allow-list).")
    p_list.set_defaults(func=_cmd_list)

    return parser


def main(argv=None):
    parser = _build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
