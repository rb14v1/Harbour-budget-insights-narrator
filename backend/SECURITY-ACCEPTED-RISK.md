# Dependency security: accepted-risk register

This file records the CRITICAL/HIGH CVEs in `backend/requirements.txt` that are
still open, and the dependency audit that produces this list.

## Policy

- A CRITICAL or HIGH CVE that has a fixed release must be fixed by moving to a
  patched version before deployment.
- A CVE with no fix yet does not block deployment. It must be listed below with
  a justification and a review date.

## Audit procedure

Run this from `backend/` before each release and at least once a month:

```sh
pip install pip-audit
pip-audit -r requirements.txt
```

## Remediation log

| Date       | Package             | Change                         | CVEs addressed |
|------------|---------------------|--------------------------------|----------------|
| 2026-11-11 | Django              | 5.0.9 (EOL) -> >=5.2.8,<5.3 (5.2 LTS) | CVE-2025-64459 (CRITICAL), CVE-2024-53908, CVE-2025-57833, CVE-2025-64458, CVE-2026-15307 (HIGH) |
| 2026-11-11 | djangorestframework | 3.15.2 -> >=3.16.1,<4          | CVE-2026-114136, CVE-2026-114137, CVE-2026-114138 (HIGH) |

## Accepted risks (no fixed version available)

| CVE | Package | Severity | Justification | Accepted by | Review date |
|-----|---------|----------|---------------|-------------|-------------|
| _None at present_ | | | | | 2027-02-11 |

The next review is due by **2027-02-11**. Review sooner if a new advisory is
published for any pinned dependency.
