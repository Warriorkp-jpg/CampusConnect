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
| GET/PATCH `/api/student-profile/` | Student | Manage skills, GitHub/LinkedIn links and PDF resume |
| GET `/api/students/{id}/resume/` | Owner, TPO or recruiter with an application | Download a protected student resume |
| GET `/api/notifications/` | Authenticated | List the current user's notifications |
| PATCH `/api/notifications/{id}/` | Notification owner | Mark a notification as read |
| GET `/api/tpo/reports/applications.csv/` | TPO | Export placement applications as CSV |
| GET `/api/student-zone/` | Student | Student dashboard |
| GET `/api/recruiter-zone/` | Recruiter | Recruiter dashboard and approval status |
| GET `/api/tpo-zone/` | TPO | Placement overview |
| GET `/api/tpo/recruiters/pending/` | TPO | Pending recruiter approvals |
| PATCH `/api/tpo/recruiters/{id}/review/` | TPO | Approve or reject a recruiter |
| `/api/tpo/student-roster/` | TPO | List and manage roster entries |
| POST `/api/tpo/student-roster/import/` | TPO | Bulk import CSV/XLSX roster |
| `/api/drive/` | Authenticated | Browse and manage placement drives |
| `/api/application/` | Authenticated | Apply, filter and manage application decisions |
| POST `/api/application/bulk-status/` | TPO or approved recruiter | Bulk update candidate stages for accessible applications |

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

The upgrade branch includes bulk roster import, student email OTP verification, a React/Vite role-based portal, and CI for backend tests and frontend builds. Remaining roadmap items include expanded student profiles/resumes, interview-stage pipeline, notifications, analytics and additional automated tests.

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


## React frontend setup

1. Open a second terminal and enter `frontend/`.
2. Install packages with `npm install`.
3. Copy `.env.example` to `.env` if you need to change the backend API URL.
4. Start the frontend with `npm run dev`.
5. Open `http://127.0.0.1:5173`.

The React app currently includes student OTP registration, recruiter self-registration, login, role-based dashboards, student-only eligible drive listings and profile/resume management, recruiter drive creation and candidate filters/bulk actions/interview scheduling, and TPO roster/recruiter management, placement analytics and CSV exports. A notification centre is available in the workspace header. The backend must be running at the configured API URL. The default CORS settings allow the Vite development origin.

## Automated checks

GitHub Actions runs `python manage.py check`, `python manage.py makemigrations --check --dry-run`, `python manage.py test`, and the React production build for the upgrade branch. Check the Actions tab for the latest run status.

Interactive API documentation is available at `/api/docs/` and the OpenAPI schema at `/api/schema/`.


## Placement pipeline and candidate filters

Application stages are `APPLIED`, `SHORTLISTED`, `INTERVIEW`, `SELECTED` and `REJECTED`. Valid transitions are enforced by the API. Moving a shortlisted candidate to `INTERVIEW` requires an interview date/time; the mode can be `ONLINE` or `IN_PERSON`.

Recruiters can filter their own candidates using `/api/application/?status=SHORTLISTED&min_cgpa=7&max_backlogs=0&search=python`. Available filters are `status`, `drive`, `min_cgpa`, `max_cgpa`, `max_backlogs` and `search`. Bulk stage updates accept up to 100 application IDs and are limited to records visible to the current recruiter or TPO.

## Student profile and resume privacy

Students can update their skills, GitHub URL, LinkedIn URL and a PDF resume of up to 5 MB. Resume downloads are served through an authenticated endpoint rather than a public media URL. A student can download their own resume, a TPO can access institutional records, and an approved recruiter can download a resume only when the student has applied to one of that recruiter's drives. Uploaded media is excluded from Git.
