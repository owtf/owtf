---
hide:
  - navigation
  - toc
---

<div class="owtf-hero" markdown>
<div markdown>
<p class="owtf-kicker">OWASP flagship project · offensive security</p>

# Human-led web security testing, without the repetitive work

<p class="owtf-hero__summary">OWTF coordinates security tools, targets, evidence, and reporting so penetration testers can spend more time reasoning about impact and less time repeating mechanical checks.</p>

<div class="owtf-hero__actions" markdown>
[Install OWTF](getting-started/installation.md){ .md-button .md-button--primary }
[Run your first assessment](getting-started/first-assessment.md){ .md-button }
</div>
</div>

<div class="owtf-terminal" markdown>
<div class="owtf-terminal__label"><span>quick start</span><span>docker compose</span></div>

```bash
git clone https://github.com/owtf/owtf.git
cd owtf
make compose-safe
```

Open `http://localhost:8019` when the services are ready.
</div>
</div>

!!! warning "Use OWTF only with authorization"

    Only test systems you own or have explicit permission to assess. OWTF can run active security tools that may change data, generate significant traffic, or disrupt a target.

## Start with the job you need to do

<div class="grid cards" markdown>

-   :material-target-account: **Set up an assessment**

    Add targets, separate engagements with sessions, and keep scope visible.

    [Targets and sessions →](guides/targets-and-sessions.md)

-   :material-puzzle-outline: **Run security tooling**

    Choose passive, semi-passive, or active plugins and monitor their work.

    [Plugins →](guides/plugins.md)

-   :material-file-chart-outline: **Review evidence**

    Explore plugin output, rank findings, add notes, and inspect proxy traffic.

    [Results and reporting →](guides/results-and-reporting.md)

-   :material-access-point-network: **Intercept traffic**

    Route an authorized browser through OWTF and inspect HTTP or HTTPS flows.

    [Intercepting proxy →](proxy/index.md)

</div>

## How OWTF fits together

OWTF runs as a small local application stack. The browser interface on port `8019` talks to the backend API on port `8009`; the intercepting proxy listens on port `8008`. PostgreSQL stores sessions, targets, work, and results.

```text
Browser UI :8019 ──► Backend API :8009 ──► PostgreSQL
                              │
                              ├──► workers ──► plugins and tools
                              │
Authorized browser ──► Proxy :8008 ──► target
```

[Read the architecture overview →](reference/architecture.md)

## Project status

These docs track the active `develop` branch. The latest tagged release is [v2.6.0](https://github.com/owtf/owtf/releases/tag/v2.6.0), published in March 2022. Use the development documentation when working from the current repository.
