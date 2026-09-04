# Captured scanner evidence

`gobuster-dns.txt` is unchanged Gobuster 3.8.2 output from the Kali container
gate during DNS plugin development, based on `c91f5891`. The target was a local
dnsmasq server with fixed A/AAAA records and no upstream resolver.

Source: `build/test-evidence/tools.l4ZctK/artifacts/tsk_32e521296662006ab48ce66f-dns.txt`.

This fixture tests decoding only. `make test-tools` exercises real DNS queries,
wildcard refusal, resolver errors, reports, and process cleanup. XML fixtures
have their own provenance in `xml/README.md`.
