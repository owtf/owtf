# Intercepting proxy

OWTF's intercepting proxy listens on `localhost:8008`. Route an authorized browser or test client through it to capture HTTP traffic for the transaction log, repeater, and manual analysis.

!!! danger "The proxy can see sensitive traffic"

    Captured requests and responses can contain credentials, session cookies, personal data, and proprietary information. Use a dedicated testing profile, restrict access to OWTF, and follow the engagement's evidence-retention policy.

## Start OWTF

```bash
make compose-safe
```

The proxy starts with the rest of the OWTF stack.

## Configure a test browser

Set both HTTP and HTTPS proxy values to:

| Setting | Value |
| --- | --- |
| Host | `127.0.0.1` |
| Port | `8008` |
| Type | HTTP proxy |

Use a dedicated browser profile with no personal accounts or unrelated browsing sessions. Do not route your entire workstation through an assessment proxy.

## Capture HTTPS traffic

HTTPS inspection requires the OWTF certificate authority to be trusted by the test client. Follow the [HTTPS interception guide](https-interception.md) and remove the CA trust when the assessment is complete.

## Work with captured traffic

Open the **Proxy** area in the OWTF web interface to:

- search request and response history;
- inspect an individual transaction;
- send a captured request to the repeater; and
- use live interception when you need to pause and modify traffic.

Live interception changes the timing and content of traffic. Enable it only while actively testing, then disable it when finished.

## Verify connectivity

If the browser cannot load a page:

1. confirm the backend container is healthy;
2. confirm port `8008` is listening on the host;
3. temporarily test a plain HTTP target to separate proxy connectivity from certificate trust;
4. inspect backend and proxy logs; and
5. check whether the target blocks the container's network path.
