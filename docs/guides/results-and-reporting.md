# Results and reporting

OWTF groups plugin output by target and test code so analysts can review related evidence together. The report is a working surface for analysis; it does not replace manual verification.

## Read a target report

Open a target to see the plugins executed for it. Test groups collect plugins that address the same security objective. Expand a group and plugin type to inspect:

- execution status and timing;
- captured command output;
- requests, responses, and discovered URLs;
- files produced by external tools; and
- any previous analyst ranking or notes.

## Rank findings

Use the severity controls to record your current assessment of impact. A high tool-generated score is not automatically a high-severity vulnerability, and an informational result can become important when combined with other evidence.

Apply rankings consistently with the engagement's reporting standard and document why the evidence supports the chosen severity.

## Add notes

Use notes to preserve analyst context that raw output cannot express:

- reproduction steps;
- affected roles or tenants;
- false-positive reasoning;
- related endpoints or transactions;
- business impact; and
- follow-up work.

Do not store passwords, tokens, private keys, or unnecessary personal data in notes.

## Filter results

Filters help narrow a large report by plugin group, plugin type, test code, status, or ranking. Treat filters as a view over the evidence: changing a filter does not change the underlying plugin output.

## Inspect the transaction log

The transaction log contains HTTP traffic observed by the OWTF proxy. Search across request and response fields, then open an individual transaction to inspect headers and bodies.

Captured traffic can contain credentials, session cookies, personal information, and proprietary data. Restrict access to OWTF and follow the engagement's evidence-retention policy.

## Rerun or remove output

Rerunning a plugin creates new traffic and may replace or add to existing evidence. Confirm scope and preserve anything you need before rerunning or deleting output.
