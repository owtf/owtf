# Scanner XML fixtures

These are unchanged scanner artifacts from the real Kali container gate at
commit `303c3328231264be083ec797e44eaa208ffd60c3`, not generated scanner mocks.
The gate ran against temporary local nginx and vsftpd services.

- `nmap-ftp.xml`: Nmap 7.99, FTP on port 21, service/version and NSE output.
- `nmap-closed.xml`: Nmap 7.99, closed TCP port 65000.
- `nikto.xml`: Nikto 2.6.1, local HTTP header and path checks.

Source evidence: `build/test-evidence/tools.ltbZ9C/artifacts/`.
`make test-tools` produces fresh scanner evidence and checks API, CLI, and ZIP
exports; these small fixtures only provide reproducible decoder regression tests.
