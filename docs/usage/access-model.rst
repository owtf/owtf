Access Model
============

OWTF now runs without built-in user account management in the web UI.

- No local signup/login flow
- No password-reset or OTP flow
- No per-user dashboard state in the frontend runtime

This keeps local development and scanning workflows simpler and removes legacy account-management code paths.

If your deployment requires authentication, place OWTF behind a reverse proxy that enforces identity and access control (for example `oauth2-proxy <https://github.com/oauth2-proxy/oauth2-proxy>`_).
