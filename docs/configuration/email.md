# Email configuration

OWTF uses SMTP for account verification and password recovery. Without SMTP, development flows write verification information to backend output.

Configure the following values through a local settings override or your deployment's secret-management mechanism:

```python
# ~/.owtf/settings.py
EMAIL_FROM = "owtf@example.test"
SMTP_LOGIN = "smtp-user"
SMTP_PASS = "load-this-from-a-secret-store"
SMTP_HOST = "smtp.example.test"
SMTP_PORT = 587
```

## Security guidance

- Never commit SMTP credentials.
- Use a dedicated sender account with the minimum required permissions.
- Protect the connection to the SMTP service according to the provider's requirements.
- Treat verification links and one-time recovery codes as credentials.
- Avoid including target or finding details in account emails.

After changing settings, restart the backend service and test sign-up and password recovery with a non-production account.
