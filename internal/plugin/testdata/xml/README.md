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

The SMTP/SMB files below were captured with the production plugins and decoder
at commit `699151fe742a905595ad8c63782e392a7236b00d`, using the extended local
fixture gate. They are unchanged Nmap 7.99 output:

- `nmap-smtp.xml`: Postfix 3.11.6 on port 25; EHLO and HELP capabilities.
- `nmap-smb-required.xml`: Samba 4.23.8 on port 445; SMB2/SMB3, signing required.
- `nmap-smb-optional.xml`: the same Samba fixture after changing signing to auto.

Source evidence: `build/test-evidence/tools.Iim0S4/artifacts/`. Postfix does not
advertise NTLM, and Samba has SMB1 disabled. These files do not prove Windows
NTLM or SMB1-specific behavior.
