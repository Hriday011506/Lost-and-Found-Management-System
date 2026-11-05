# Product proposal: Independent Campus Lost & Found service

## 1. Executive summary

Campus Connect is proposed as a standalone digital Lost & Found service for students and university staff. Users can report lost or found belongings, search campus listings and submit ownership claims. Designated university departments can review claims and coordinate the existing physical handover process.

The product is intentionally designed to operate independently. It does not require SLCM access, SLCM APIs or university single sign-on to demonstrate its value or run a controlled prototype. Any future connection to SLCM would be optional and subject to separate university approval.

## 2. Problem and opportunity

Lost-property information can be scattered across notice boards, informal messages, emails and verbal communication. A central online register could improve discoverability, reduce repeated enquiries and provide a traceable claim-review process.

These are hypotheses to validate with the university. Baseline report volumes, recovery rates and process times should be collected during discovery rather than assumed.

## 3. Proposed users and roles

- **Student:** register, sign in, submit lost / found reports, search listings, submit claims and track personal activity.
- **University staff:** use the same reporting and search workflow.
- **Department reviewer:** access only claims assigned to their department, review ownership evidence and record a decision.
- **System administrator:** provision department reviewers, oversee campus activity, manage access and inspect the audit trail.

Privileged accounts must be created by an authorised service administrator; public registration must never grant reviewer or administrator privileges.

## 4. Core workflow

1. A student or staff member signs in to the independent website.
2. They submit a Lost or Found report with item details, date, campus location and optional image.
3. The report is published to searchable campus listings.
4. A potential owner submits identifying information through a claim.
5. The claim is routed to the department responsible for the selected location / item.
6. An authorised department reviewer approves or rejects the claim and records a reason.
7. The responsible university team coordinates physical handover under its approved procedure.

## 5. Standalone architecture

**Student / Staff browser** → **Streamlit web application** → **Authentication and role checks** → **Application modules** → **SQLite database and image storage**

The prototype uses its own account store and does not collect SLCM credentials. For an institutional pilot, the university may require managed hosting, a managed relational database, object storage, central identity services, monitoring, backups and security controls.

## 6. Department-led verification

A department-based model is proposed because the team responsible for a particular campus location or property category is better placed to verify custody and handover. Departments should only see claims assigned to them. A central administrator should be able to audit the process without bypassing departmental accountability.

The university must decide the final department list, routing rules, evidence standards, escalation path and who is legally / operationally authorised to release an item.

## 7. Governance and safeguards

Before a live pilot, agree:
- Service owner and accountable department.
- Student / staff eligibility and account-verification approach.
- Department reviewer appointment and access-removal procedure.
- Minimum personal data and clear privacy notice.
- Image upload guidance and prohibition on unnecessary sensitive information.
- Data retention, deletion, correction and access-request process.
- False claims, abuse, duplicate reports and inappropriate-content handling.
- Secure hosting, encryption, backups, logging, monitoring and incident response.
- Physical custody, identity checks at handover and dispute escalation.
- Accessibility, mobile usability, support route and operating hours.

## 8. Pilot and evaluation

A controlled pilot should begin only after university approval of the service owner, operating procedure, privacy review and hosting. A limited cohort can test the workflow before a campus-wide rollout.

Potential measures:
- Number of valid lost / found reports.
- Percentage of reports with complete information.
- Time from report submission to first review.
- Claims submitted, reviewed, approved and rejected.
- Number of items marked resolved.
- Duplicate / invalid report rate.
- User satisfaction and department workload.

Targets should be agreed after baseline discovery.

## 9. Phased roadmap

| Phase | Work | Exit condition |
|---|---|---|
| 0 — Product validation | Stakeholder interviews and current-process mapping | Service owner and user needs agreed |
| 1 — Standalone prototype | Demonstrate reporting, search and claims | Feedback and workflow gaps documented |
| 2 — Department workflow | Department accounts, queues and routing | Role and decision tests pass |
| 3 — Controlled pilot | Approved hosting, policy and limited cohort | Pilot evaluation completed |
| 4 — Campus rollout | Training, support, monitoring and operations | Formal go-live approval |
| 5 — Optional SLCM assessment | Consider portal link / SSO if requested | Separate technical and institutional approval |

## 10. Decisions requested from the university

1. Nominate a service owner and participating departments.
2. Confirm how found property is currently received, stored and handed over.
3. Agree the evidence and escalation process for ownership claims.
4. Review the standalone prototype and advise on pilot requirements.
5. Confirm security, privacy, accessibility and hosting review requirements.

## 11. Status statement

This is a student project proposal and prototype, not an official university service or representation of institutional endorsement. SLCM integration is optional future scope and is not required for the standalone product.
