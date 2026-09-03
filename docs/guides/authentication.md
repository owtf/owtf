# Authentication

OWTF accounts protect access to sessions, targets, proxy traffic, and reports. Treat the local OWTF instance as sensitive even when it is only bound to a development workstation.

## Sign up and verify an account

Create an account from the sign-up page. OWTF sends an email-verification link when SMTP is configured. In a development environment without SMTP, the verification link is written to backend output instead.

After verification, sign in with the registered email address and password.

## Reset a password

Use the forgot-password flow to request a one-time code, verify it, and choose a new password. The code is delivered by email when SMTP is configured or appears in development output otherwise.

## Configure email delivery

Production-like environments should configure an SMTP provider so verification and recovery data is not exposed in logs.

[Configure email →](../configuration/email.md)

## Administrator accounts

There is no default community-plugin administrator. Initial administrators can be seeded with the `OWTF_ADMIN_EMAILS` environment variable before registration. Existing accounts are managed with the separate administrative command:

```bash
owtf-admin promote reviewer@example.com
owtf-admin demote reviewer@example.com
owtf-admin list
```

Admin access permits review and approval of community plugin source. Grant it only to trusted reviewers and remove it when no longer needed.

## Deployment warning

The checked-in development stack is not suitable for an internet-accessible deployment. Keep it on a trusted local network. A production deployment needs a separate hardening review that replaces all application and JWT secrets, restricts network access, configures HTTPS, and validates the authentication and CORS settings.
