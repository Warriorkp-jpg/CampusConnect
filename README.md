# CampusConnect — JMIT Placement Management Portal

CampusConnect is a single-college placement management portal for JMIT. The existing backend uses Django, Django REST Framework, SimpleJWT and SQLite. The React frontend and verified student onboarding are being introduced incrementally on the upgrade branch.

## Roles

- **Student:** registers using a roll number present in the TPO-maintained roster, views drives, applies when eligible and tracks application decisions.
- **Recruiter:** registers with company details. New accounts remain pending until approved by a TPO. Recruiters can manage their own drives and applicants.
- **TPO:** manages the student roster, approves recruiters and monitors drives and applications across the institution.

TPO accounts are created by a trusted administrator using Django admin. There is no public TPO registration endpoint.

## Current backend features

- JWT authentication and server-assigned roles.
- Student roster verification and roster-backed academic eligibility data.
- Recruiter approval workflow.
- Drive creation and management.
- CGPA/backlog eligibility checks and duplicate application protection.
- Application status updates and role-based queryset isolation.
- TPO dashboard and roster management.
- TPO-only CSV/XLSX bulk roster import with row-level validation.
- Student self-registration through roster-bound email OTP, hashed challenges, expiry, resend limits and attempt limits.

## Bulk student roster import

Use the sample file at `docs/student_roster_template.csv`.

Endpoint: `POST /api/tpo/student-roster/import/`

Send a multipart form request with the uploaded file in the `file` field. Supported formats are `.csv` and `.xlsx`. Uploads are limited to 5 MB and 5,000 data rows.

Required columns: `roll_number`, `full_name`, `college_email`.

Optional columns: `program`, `batch`, `cgpa`, `backlogs`.

The importer validates each row, reports row-level errors, skips existing roll numbers without overwriting their records, and inserts valid new records. Only users with the TPO role can access this endpoint.

## API overview

| Endpoint | Access | Purpose |
|---|---|---|
| POST `/api/register/student/request-otp/` | Public | Request an OTP sent only to the email in the official roster |
| POST `/api/register/student/verify-otp/` | Public | Verify the emailed OTP |
| POST `/api/register/student/` | Public | Complete registration using a verified challenge and password |
| POST `/api/register/recruiter/` | Public | Recruiter registration; account starts pending |
| POST `/api/login/` | Public | Obtain JWT tokens |
| GET `/api/me/` | Authenticated | Current account profile and role |
| GET `/api/student-zone/` | Student | Student dashboard |
| GET `/api/recruiter-zone/` | Recruiter | Recruiter dashboard and approval status |
| GET `/api/tpo-zone/` | TPO | Placement overview |
| GET `/api/tpo/recruiters/pending/` | TPO | Pending recruiter approvals |
| PATCH `/api/tpo/recruiters/{id}/review/` | TPO | Approve or reject a recruiter |
| `/api/tpo/student-roster/` | TPO | List and manage roster entries |
| POST `/api/tpo/student-roster/import/` | TPO | Bulk import CSV/XLSX roster |
| `/api/drive/` | Authenticated | Browse and manage placement drives |
| `/api/application/` | Authenticated | Apply and manage application decisions |

## Local setup

1. Clone the repository and enter the project folder.
2. Create and activate a Python virtual environment.
3. Install dependencies: `pip install -r requirements.txt`.
4. Set a strong `DJANGO_SECRET_KEY` for any shared or deployed environment.\n5. For local OTP testing, the default email backend prints the message in the Django terminal. For real email delivery, configure `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` and `DEFAULT_FROM_EMAIL` as environment variables. Never commit email credentials.
6. Run `python manage.py migrate`.
7. Create an administrator using `python manage.py createsuperuser`.
8. Assign the trusted TPO account the application role `TPO` in Django admin.
9. Run `python manage.py runserver`.

SQLite remains the selected development database. Keep `db.sqlite3` out of Git and back it up before migration changes.

## Upgrade roadmap

The upgrade branch is being developed in phases: bulk roster import, student email OTP verification, React application foundation, improved role dashboards, recruiter candidate workflows, application pipeline, notifications, analytics and automated tests.

## Important security notes

- A roll number must exist in the official TPO roster before student onboarding.
- OTP verification will prove access to the roster email address; roster membership remains the source of truth for eligibility.
- Configure HTTPS, secure secret management, trusted CORS origins and backups before public deployment.
- Run backend tests with `python manage.py test`.


## Student OTP onboarding API

1. Request an OTP with `POST /api/register/student/request-otp/` and JSON `{"roll_number":"JMIT2027CSE001"}`.
2. Verify it with `POST /api/register/student/verify-otp/` and JSON `{"challenge_id":"<uuid>","otp":"123456"}`.
3. Complete registration with `POST /api/register/student/` and JSON `{"challenge_id":"<uuid>","password":"A-strong-password"}`.

The challenge is short-lived; OTP values are stored as password hashes, expire after 10 minutes, allow at most five verification attempts, and are protected by per-roll-number resend limits and IP-based API throttling. The response does not reveal whether a roll number exists. The account email and academic values always come from the TPO roster; submitted role or email values cannot override them. Local development uses Django's console email backend by default, so the code appears in the backend terminal rather than being sent to a real inbox.
