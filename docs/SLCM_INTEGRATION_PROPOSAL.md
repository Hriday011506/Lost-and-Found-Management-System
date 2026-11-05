# Proposal: Campus Lost & Found as a future SLCM-linked service

## 1. Executive summary

This project proposes a centralised digital Lost & Found service for the university community. Students and staff could report lost or found belongings, search listings, and submit ownership claims. Authorised personnel could review reports and claims before coordinating the university's existing physical handover process.

The current repository is an academic prototype to demonstrate the workflow. It is not an official university service and is not integrated with SLCM. The proposal is to seek feedback and sponsorship from the appropriate university stakeholders before any live pilot or integration work.

## 2. Problem and opportunity

Lost-property information can be fragmented across notice boards, informal messages, emails and verbal communication. A central register could make reports easier to discover, reduce duplicated enquiries and provide a traceable claim-review process.

These are project hypotheses to validate with the university; baseline volumes and current process metrics should be gathered during discovery rather than assumed.

## 3. Proposed scope

### Student / staff-facing capabilities
- Sign in through a university-approved identity mechanism (future integration).
- Create a lost-item or found-item report.
- Add category, description, date, campus location and optional image.
- Search and filter active reports.
- Submit an ownership claim with identifying information.
- View report and claim status.

### Authorised administrator capabilities
- Review and moderate submitted reports.
- Review ownership claims and record a decision with a note.
- Maintain report status and remove inappropriate / duplicate content.
- View basic operational metrics and an audit trail.

### Explicitly out of scope for the prototype
- Physical custody, storage, delivery or handover of items.
- Direct access to SLCM, student records or institutional APIs.
- Automated identity verification or automatic ownership determination.
- Production notification infrastructure.

## 4. Suggested user journey

1. A student / staff member opens the service through an approved university entry point.
2. The user reports an item as Lost or Found.
3. The service displays appropriate active listings and filters.
4. A potential owner submits a claim with details that only the owner is likely to know.
5. An authorised administrator reviews the evidence and decides whether to approve or reject.
6. The responsible university department follows its approved physical handover SOP and updates the service status.

## 5. Indicative architecture

**SLCM / university portal (future entry point)** → **University identity provider (SSO)** → **Lost & Found application** → **University-managed application API / service layer** → **University-managed database and file storage**

SLCM should remain the identity / portal authority. The application should not ask users for their SLCM password or imitate the SLCM login page. Any API-based exchange must use an approved contract, least-privilege service credentials, and documented ownership.

## 6. Governance and safeguards to agree before a pilot

- Service owner and accountable department.
- Who may create, review, approve and administer records.
- Whether student, staff or visitor accounts are supported.
- Minimum necessary personal information and a clear privacy notice.
- Image upload rules; prohibit sensitive identity documents and unnecessary personal data.
- Data retention, deletion, correction and access-request procedures.
- Reporting abuse, false claims, duplicate reports and inappropriate content.
- Secure hosting, encryption, backups, logging, monitoring and incident response.
- Accessibility, mobile usability and supported browsers.
- Physical storage, verification and handover responsibilities.

## 7. Suggested pilot and evaluation

A pilot should begin only after the responsible university stakeholders approve the scope, privacy review, operating procedure and hosting. Start with a limited cohort and a defined evaluation period.

Possible measures:
- Number of valid reports submitted.
- Percentage of reports with sufficient information.
- Search-to-relevant-listing rate.
- Claims submitted, reviewed and resolved.
- Median time from report to first review.
- Duplicate / invalid report rate.
- User satisfaction and administrator workload.

The institution should set targets after collecting baseline data.

## 8. Phased roadmap

| Phase | Work | Exit condition |
|---|---|---|
| 0 — Discovery | Stakeholder interviews, process mapping, policy owner | Scope and owner agreed |
| 1 — Prototype review | Demonstrate current Streamlit workflow | Functional feedback recorded |
| 2 — Controlled pilot | Approved hosting, limited cohort, manual accounts if approved | Pilot evaluation completed |
| 3 — Hardening | Security, privacy, accessibility, operations | Formal technical sign-off |
| 4 — SLCM integration assessment | SSO / API design with SLCM team | Integration approved and scheduled |
| 5 — Institutional rollout | Support model, training, monitoring | Go-live approval |

## 9. Decisions requested from the university

1. Nominate the department / service owner for lost-property operations.
2. Identify the SLCM / IT contact to assess feasibility of a portal link and future SSO.
3. Confirm the policy for item custody, claim verification and handover.
4. Review the prototype and advise what would be required for a controlled pilot.
5. Confirm security, privacy, accessibility and procurement / hosting review requirements.

## 10. Important status statement

This document is a student project proposal, not a representation of university endorsement. All SLCM integration, institutional data access, production hosting and operational procedures are subject to approval by the university.
