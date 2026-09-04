# Legacy settings audit

The inventory is complete for the four source files below. **Settings parity is
not complete.** Every declaration or resource occurrence has a status, replacement
or gap, current evidence path, and explanation in
[settings-migration.csv](settings-migration.csv).

## Source and scope

Legacy source is pinned to `c41908bf0b83c5588f885ee20e5d187bf5d87be2`, the locally
available Python `origin/develop` snapshot. This is **not a verified 2.6.10 tag**;
it includes later community-plugin and worker-scaling settings. Current code was
inspected at `89ffc5c4` on `owtf-next`. No legacy files were executed, and no
runtime settings or plugins were changed by this audit.

| Source | Occurrences |
| --- | ---: |
| `owtf/settings.py` | 117 |
| `owtf/data/conf/general.yaml` | 118 |
| `owtf/data/conf/framework.yaml` | 81 |
| `owtf/data/conf/resources.cfg` | 1,173 |
| **Total** | **1,489** |

The inventory covers uppercase Python assignments, including conditional database
assignments; every YAML `config` declaration; and every non-comment resource line.
It preserves duplicates by source line. Lowercase derived regex objects, Python
imports/control flow, runtime target substitutions, user-local overrides, and
separate group/order files are not additional entries in this four-file inventory.
Source file hashes and occurrence counts are in
[settings-migration-source.json](settings-migration-source.json). Per-row hashes
identify source lines without copying credentials or executable command templates.

## Status counts

| Status | Occurrences | Meaning |
| --- | ---: | --- |
| migrated | 10 | Equivalent control exists in typed configuration; defaults may differ. |
| replaced | 80 | Supported behavior moved to another mechanism with explicit differences. |
| partial | 170 | Related support exists, but some values, rules, or behavior differ or remain unverified. |
| removed | 912 | Covered by an existing retirement decision, rather than silently omitted. |
| deferred | 65 | Covered by existing deferred credential/SNMP work. |
| gap | 252 | No verified equivalent or explicit retirement decision. Requires a decision, not automatic implementation. |

These count source occurrences, not features or unique settings. Most removed
rows are repetitive DoS/exploit command resources belonging to rejected launchers.
A current plugin for the same technique is not proof that every old command,
reference URL, flag, or output was ported. Such resources remain partial or gaps.
Reference destinations were not checked for present-day availability.

## Mappings and consequential differences

- API listen address/port, plugin directory, task timeout, proxy listen address,
  CA paths, and cookie lists have typed settings. No importer reads old Python,
  YAML, or resource files into the new configuration.
- Output paths map to `server.dataDirectory`, SQLite records, and task-owned
  artifacts. Log-file names are replaced by process stderr and persisted events.
- Profiles and plugin group/type selections replace legacy group/order settings.
  Executables come from manifest requirements or the Kali tools image, not
  arbitrary global installation-path substitutions.
- Per-plugin `port` inputs replace supported network port constants. In particular,
  SQL Server now defaults to **TCP 1433**, whereas the old constant was **1434**;
  this does not establish UDP SQL Browser discovery parity.
- Global `PLUGIN_TIMEOUT` was 300 seconds in the audited source; the current
  server default is **30 seconds**. This is a default change, not a copied value.
- Automatic worker scaling and resource thresholds became a fixed bounded worker
  pool. Plugin retries were removed; proxy forwarding attempts are separate.
- OWTF proxy upstream settings replace outbound proxy fields. Proxychains settings
  are only partially replaced: arbitrary plugin traffic is not transparently
  routed through OWTF's proxy.
- Named wordlists and bounded task copies replace dictionary path substitution.
  They do not provide all old dictionary contents or install those collections.
- Header/body grep behavior moved into plugin YAML. Matching sets and extraction
  semantics differ, so those rows are partial even where related rules exist.

## Remaining decisions

The concrete gaps include:

1. Global API CORS policy and debug/log-level configuration.
2. Encrypted CA private keys/passphrase-file handling.
3. Global User-Agent behavior; selected plugins have an input, but no shared
   override controls all tools.
4. Reusable TCP/UDP port lists and legacy dictionary contents.
5. File/image/SSI URL classification and automatic small-file retrieval policy.
6. CSS/JS-comment, generic autocomplete/hidden-field, and legacy XSS-protection
   analysis rules. Existing fingerprint/CORS/cache/cookie rules also have narrower
   or changed behavior.
7. Unmapped legacy tool paths, passive discovery resources, and individual command
   options/reference links. These remain part of deferred plugin-related work.
8. Remote-shell/SBD/SET/phishing settings that lack a current implementation or an
   explicit retirement decision in the checked support matrix. This audit does
   not introduce such a decision.

The old editable settings API/UI also has no general replacement. `owtf config
show` resolves configuration for **the process running that command**, including
its environment and files; it is not a query of a remote running server's settings.
Only supported runtime APIs, such as proxy interceptor management, change live
state. Configuration file changes otherwise require a restart.

## Reproduce the coverage check

From the repository root:

```sh
go run ./scripts/check-settings-audit
```

If a shallow checkout lacks the pinned source object, fetch that specific commit
first:

```sh
git fetch --no-tags --depth=1 origin c41908bf0b83c5588f885ee20e5d187bf5d87be2
```

The checker compares all four file hashes, declaration/resource identities, line
hashes, duplicate occurrences, counts, status values, and referenced local paths.
It fails on omitted or extra entries. This verifies inventory completeness and
traceability; it does not prove runtime equivalence for partial or gap rows.
