# Campus Lost & Found Management System

A Streamlit + SQLite prototype for a university campus lost-and-found service, designed as a demonstrable pilot and a foundation for a future institutional SLCM integration proposal.

> **Status:** Academic / institutional proposal prototype. This repository is not an official MUJ service and is not connected to SLCM, university SSO, or university databases.

## What it demonstrates

- Single sign-in interface with role-based student and administrator experiences
- Student account registration
- Create Lost and Found reports, including optional image uploads
- Browse and filter active reports
- Submit ownership claims with identifying details
- Administrator claim approval / rejection and review notes
- Basic user directory, audit trail, dashboard metrics
- SQLite persistence and password hashing (PBKDF2-HMAC-SHA256)
- Dark and light appearance selector

## Run locally

Python 3.10+ is recommended.

```bash
git clone https://github.com/Hriday011506/Lost-and-Found-Management-System.git
cd Lost-and-Found-Management-System
python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
streamlit run app.py
```

The database is created automatically as `lost_found.db` in the project directory. Uploaded images are stored under `uploads/`.

### Initial demo administrator

- Email: `admin@campus.local`
- Password: `ChangeMe-Admin123!`

**Change the demo administrator password / remove the seeded account before exposing the app publicly.** For a real deployment, implement a proper admin bootstrap process and store secrets outside source control.

## Deploy on Streamlit Community Cloud

1. Push this repository to GitHub.
2. Open Streamlit Community Cloud and create an app from this repository.
3. Set the entry point to `app.py`.
4. Deploy.

**Important deployment limitation:** Streamlit Community Cloud's local filesystem should not be treated as a durable production database or file store. SQLite and local uploads in this prototype are intended for a demo / controlled pilot. A university deployment should use university-managed persistent database and object storage, backups, monitoring, and access controls.

## Proposed workflow

1. A student or staff member signs in.
2. They submit a Lost or Found report with item details, date, location and optional image.
3. Users search and filter open listings.
4. A claimant submits identifying ownership details.
5. An authorised administrator reviews the claim and approves or rejects it.
6. An approved claim marks the item resolved; physical handover remains an offline university process.

## Proposed data model

- **User**: identity, email, password hash, role
- **Item**: reporter, report type, item details, location, date, image reference, status
- **Claim**: item, claimant, ownership evidence, status, administrator note
- **AuditLog**: actor, action, record reference / detail, timestamp

## SLCM integration vision (future phase — not implemented)

The prototype is intentionally separated from SLCM. A future institutional integration should be designed with MUJ's IT / SLCM owners and security team. A possible target architecture is:

- **Identity:** SLCM / university-approved identity provider using an approved SSO protocol (e.g., OIDC or SAML); do not collect or store SLCM passwords in this app.
- **Authorisation:** map verified institutional identity attributes to student / staff / authorised administrator roles; administrator privileges require explicit institutional approval.
- **Integration:** publish an approved link or embedded entry point in SLCM, with documented API contracts if data exchange is required.
- **Hosting:** university-approved infrastructure, central logging, monitoring, backups, vulnerability management and recovery procedures.
- **Data governance:** approved purposes, retention periods, access rules, privacy notice, incident response and ownership of operational data.
- **Operations:** named service owner, support route, moderation / handover SOP, escalation procedure and service-level expectations.

No SLCM API, endpoint, credential, integration permission or institutional approval is assumed by this project.

## Pilot proposal outline

A safe way to evaluate the concept is a limited, time-bound pilot after university review:

1. **Discovery:** confirm the responsible department, item handover process, user groups and current pain points.
2. **Policy and privacy review:** approve data fields, image guidance, retention / deletion, moderation and escalation.
3. **Controlled pilot:** use a small campus cohort and non-sensitive test data in an approved hosting environment.
4. **Evaluation:** measure report completion, time to find a relevant listing, claims reviewed, resolved reports, duplicate / misleading reports and user feedback.
5. **Decision gate:** assess security, operational workload, adoption and value before considering SLCM integration.

## Known prototype limitations / next steps

- Email ownership and institutional identity are not verified.
- The demo admin bootstrap is suitable only for local demonstration.
- No email / push notifications, SLCM integration, QR / barcode support or physical handover workflow.
- No production-grade moderation, rate limiting, malware scanning or image redaction.
- Local SQLite and upload storage are not a multi-instance production architecture.
- Add password reset, account verification, formal admin provisioning and automated tests before a broader pilot.

## Academic context

The feature scope follows the supplied Software Requirements Specification for a campus lost-and-found system: user registration and login, lost / found reports, searching and filtering, ownership claims, and administrator management. SLCM connectivity is explicitly treated as a future enhancement rather than a Version 1.0 capability.
