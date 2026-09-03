# HTTPS interception

OWTF can terminate a client's TLS connection, inspect the decrypted HTTP traffic, and create a separate TLS connection to the upstream server. It generates a leaf certificate for each destination and signs it with OWTF's local certificate authority.

```text
test browser ◄── TLS signed by OWTF CA ──► OWTF proxy ◄── upstream TLS ──► target
```

Only use interception for traffic you are authorized to inspect.

## Before you begin

- Start OWTF with `make compose-safe`.
- Use a dedicated browser profile or disposable test client.
- Configure the client to use `127.0.0.1:8008` as its HTTP and HTTPS proxy.
- Close unrelated tabs and accounts in that profile.

## Download the OWTF CA certificate

Use the download control in the OWTF Proxy interface, or fetch the certificate from the local backend API:

```bash
curl --fail --output owtf-ca.crt \
  http://localhost:8009/api/v1/proxy/ca-cert/
```

Inspect the certificate before trusting it:

```bash
openssl x509 -in owtf-ca.crt -noout -subject -issuer -fingerprint -sha256
```

## Trust the CA in the test profile

Import `owtf-ca.crt` as a trusted certificate authority only in the dedicated test browser or client. The exact steps depend on the browser and operating system.

!!! warning

    Trusting this CA allows the holder of its private key to impersonate HTTPS sites to that client. Do not install it system-wide unless the test environment specifically requires that. Never distribute the CA private key.

Restart the test browser after importing the certificate.

## Verify interception

1. Visit an HTTPS endpoint that is inside the approved scope.
2. Inspect the connection certificate in the browser.
3. Confirm that the issuer is the OWTF CA you imported.
4. Open the OWTF transaction log and confirm the request appears.

If the browser reports a certificate error, compare the installed CA fingerprint with the file downloaded from the running OWTF instance.

## Known limitations

- Certificate-pinned applications can reject OWTF-generated certificates.
- Some clients ignore system or browser proxy settings.
- Mutual TLS requires additional client-certificate handling.
- Protocols that do not use HTTP over the configured proxy are not captured automatically.

Do not bypass certificate pinning unless the rules of engagement explicitly allow it.

## Remove trust after testing

When the assessment ends:

1. remove the OWTF CA from the test browser or operating-system trust store;
2. delete exported copies of the certificate if they are no longer required;
3. clear the dedicated browser profile according to the retention policy; and
4. protect or remove captured traffic through the approved evidence process.
