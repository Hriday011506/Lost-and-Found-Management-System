# Campus Connect — Independent Lost & Found Platform

A professional Streamlit application concept for a university campus. Students and university staff can report lost or found belongings, search listings and submit ownership claims. The service is designed to operate independently with its own accounts and database.

> **Project status:** Student-built prototype / proposed campus service. It is not an official university platform, is not endorsed by the university, and does not connect to SLCM or any university identity provider.

## Product direction

The immediate product is a standalone website. It can be demonstrated, evaluated and potentially piloted without depending on SLCM access or integration approval. A future SLCM link or single sign-on may be considered only if the university requests and approves it; it is not a dependency for this project.

## Current features

- Restricted institutional email registration and sign-in: students use `@muj.manipal.edu`; faculty use `@jaipur.manipal.edu`
- Independent registration and sign-in
- Student / staff user experience and role-based administrator access
- Lost and Found item reports with optional image upload
- Search and filters for active listings
- Ownership claim submission and status tracking
- Department-oriented claim verification workflow (planned next implementation milestone)
- Campus dashboard, operational metrics and audit history
- Dark / light appearance
- SQLite persistence and salted PBKDF2 password hashes

## Account eligibility

- Student accounts: email address must end exactly with `@muj.manipal.edu`.
- Faculty accounts: email address must end exactly with `@jaipur.manipal.edu`.
- The account role is assigned from the email domain; users cannot choose or self-assign a privileged role.
- Department reviewer and administrator accounts are provisioned separately by an administrator.
- **Important:** domain checking restricts the address format but does not prove mailbox ownership. Before a real campus pilot, add email verification (one-time link / code) or an approved university identity verification process.

## Run locally

Python 3.10+ recommended.

```bash
git clone https://github.com/Hriday011506/Lost-and-Found-Management-System.git
cd Lost-and-Found-Management-System
python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

Create `.streamlit/secrets.toml` locally (this file is ignored by Git):

```toml
[bootstrap]
admin_email = "your-admin-email@example.com"
admin_password = "Use-A-Unique-Password-Here"
```

Then start the app:

```bash
streamlit run app.py
```

The first run creates the administrator from the secrets above. If no bootstrap secrets are configured, public visitors can register as ordinary users but no administrator account is created. Do not commit secrets or real user data.

## Deploy a demonstration

1. Push the repository to GitHub.
2. Create an app in Streamlit Community Cloud using this repository and `app.py`.
3. Add the `bootstrap` values under the app's Secrets settings.
4. Deploy and test with dummy data only.

**Persistence warning:** Streamlit Community Cloud's local filesystem is not a production persistence guarantee. The SQLite database and uploaded images in this prototype are suitable for local development / demonstration, not a multi-instance institutional service. A real campus pilot should use university-approved hosting, managed database and object storage, backups, monitoring and recovery procedures.

## Proposed department-led operating model

1. A student or staff member reports an item and selects the responsible campus department.
2. The report appears in the campus listing.
3. A claimant submits identifying ownership details.
4. The responsible department reviews the claim and records a decision.
5. The relevant university team coordinates physical handover under its approved procedure.

The physical custody and handover of recovered property are outside the scope of this web prototype and must be defined by the university.

## Roadmap

- [x] Independent Streamlit application foundation
- [x] SQLite records and password hashing
- [x] Lost / Found reporting, browsing and claims
- [x] Dark / light theme and basic admin view
- [ ] Department reviewer accounts and restricted claim queues
- [ ] Campus location directory and department routing rules
- [ ] Smart Lost / Found match suggestions
- [ ] Email notifications and password recovery
- [ ] Automated tests, security review and accessibility checks
- [ ] Controlled campus pilot proposal and evaluation
- [ ] Optional SLCM entry point / SSO assessment, only if approved

## Institutional readiness

Before any live campus rollout, the university would need to approve a service owner, hosting, account verification, role assignments, privacy notice, data retention, moderation, claim-verification procedure, physical handover process, incident response and support ownership. This repository is a prototype and does not claim those approvals have been obtained.
