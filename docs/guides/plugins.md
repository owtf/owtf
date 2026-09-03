# Plugins

Plugins connect OWTF's assessment workflow to built-in checks and external security tools. OWTF records their output against a target so analysts can review related evidence together.

## Plugin groups

OWTF organizes plugins by target family:

- **WEB** for web applications and HTTP services;
- **NET** for network-level checks; and
- **AUX** for supporting activities that do not fit a single target flow.

## Interaction types

The plugin type communicates how work interacts with a target.

| Type | Behavior | Operational guidance |
| --- | --- | --- |
| Passive | Analyzes information already available to OWTF | Start here when possible |
| Semi-passive | Makes ordinary requests to gather more information | Confirm request volume and scope |
| Active | Probes for vulnerabilities | Can be disruptive; require explicit approval |
| Grep | Processes collected transactions and tool output | Usually depends on earlier traffic |
| External | Coordinates an external data source or tool | Review where data is sent |
| Bruteforce | Attempts multiple credentials or inputs | High risk; use only when explicitly allowed |

!!! note

    A plugin's category helps with planning, but it is not a safety guarantee. Review the plugin help text and the underlying tool before launching it.

## Launch plugins

You can launch plugins from the target table for multiple selected targets or from an individual target report. Search by plugin name or select a defined group when the entire group is within scope.

Before launching:

1. confirm the active session;
2. confirm every selected target;
3. read the plugin's help text;
4. validate the interaction type against the rules of engagement; and
5. check that the required external tool is available in the running container.

## Interpret output

Plugin output is evidence, not a confirmed finding. Verify the behavior, remove false positives, connect related observations, and record analyst context in the target report.

## Community plugins

Community plugins cross an additional trust boundary because approved Python code runs with the same application permissions as built-in plugin code. Administrators must review source before approval.

[Read the community plugin security model →](../reference/community-plugin-security.md)
