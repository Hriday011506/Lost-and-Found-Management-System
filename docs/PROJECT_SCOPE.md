# Product scope — Version 1.0 prototype

## Purpose
Provide a web-based campus application for reporting lost and found items, searching item records, submitting ownership claims, and allowing authorised administrators to review reports and claims.

## User classes
- Student / staff user: create account, sign in, submit Lost / Found reports, search and filter, submit claims, view activity.
- Administrator: review claims, approve / reject with notes, inspect users and audit activity.

## Functional requirements mapped to this prototype
- FR-01 Account registration: student account creation with unique email.
- FR-02 Authentication: single sign-in page with role-based views.
- FR-03 Lost report: create a Lost item report.
- FR-04 Found report: create a Found item report.
- FR-05 Search: search open item records by keywords.
- FR-06 Filter: filter by report type and category.
- FR-07 Ownership claim: submit item-specific identifying details.
- FR-08 Claim review: administrator approves / rejects and records a note.
- FR-09 Status tracking: users view their own report and claims.
- FR-10 Administration: administrator can inspect users and audit activity.

## Non-functional intent
- Usability: simple responsive Streamlit interface and clear status labels.
- Security: salted password hashes, parameterised SQL and role-aware pages.
- Maintainability: separate database operations and UI sections within a compact prototype.
- Reliability: SQLite persistence for a single-instance demonstration.

These are implementation notes, not a formal verification that all institutional NFRs have been met.
